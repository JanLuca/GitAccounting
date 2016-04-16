#!/usr/bin/python3
# encoding: utf-8
'''
accounting -- shortdesc

accounting is a description

It defines classes_and_methods

@author:     Jan Luca Naumann

@copyright:  2016 Jan Luca Naumann. All rights reserved.

@license:    GPL version 3.0

@contact:    user_email
@deffield    updated: Updated
'''

import sys
import os
import time
import errno
import shutil

import git
from git.repo.fun import is_git_dir
import re

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from sys import path
from distlib.compat import raw_input

__all__ = []
__version__ = 0.1
__date__ = '2016-04-14'
__updated__ = '2016-04-14'

DEBUG = 1
TESTRUN = 0
PROFILE = 0

dirList = [];

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def getAccountInt(text, fromAccount = None):
    result = None;
    
    try:
        result = int(raw_input(text));
        dirList[result];
    except ValueError:
        print("Bitte eine Zahl eingeben!");
        result = getAccountInt(text, fromAccount);
    except IndexError:
        print("Bitte eine Zahl im Bereich der existierenden Konten eingeben!");
        result = getAccountInt(text, fromAccount);
        
    if(result == fromAccount):
        print("Bitte nicht das gleiche Konto zweimal auswählen!");
        result = getAccountInt(text, fromAccount);
        
    return result;

def genDirList(repoPath):
    if(len(dirList) == 0):    
        for root, dirs, files in os.walk(repoPath):
            for dirName in dirs:
                relDirName = os.path.relpath(os.path.join(root, dirName), repoPath);
                if(relDirName.find(".git") == 0):
                    continue;
                dirList.append(relDirName);
        
        dirList.sort();

def printAccountStructure(repoPath):
    print("Liste der verfügbaren Accounts:");
    
    genDirList(repoPath);
    
    i = 0; 
    for dirName in dirList: 
        print(str(i) + ") " + dirName);
        i += 1;
        
def readTransferAmount():
    transferStr = raw_input("Bitte die Geldmenge zur Übertragung eingeben: ");
    transferStr = transferStr.replace(",", ".");
    
    result = None;
    indexDot = transferStr.find(".")
    
    try:
        if(transferStr.find(".") == -1):
            result = int(transferStr) * 100;
        elif(len(transferStr) - indexDot > 3):
            print("Es sind nur zwei Nachkommastellen unterstützt");
            return readTransferAmount();
        elif(len(transferStr) - indexDot == 2):
            result = int(transferStr.replace(".", "")) * 10;
        else:
            result = int(transferStr.replace(".", ""))
    except ValueError:
        print("Bitte einen richtigen Betrag eingeben!");
        result = readTransferAmount;
        
    return result; 

def importDocument(repoObj, repoPath):
    filePath = raw_input("Bitte den Dateipfad angeben: ");
    if(not os.path.isfile(filePath)):
        print("An der angegeben Stelle scheint keine Datei zu liegen. Bitte nochmal versuchen.");
        return importDocument(repoObj);
    
    try:
        os.makedirs(os.path.join(repoPath, "documents"))
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass;
        else:
            raise;
        
    docIdFile = open(os.path.join(repoPath, "docid"), 'r+');
    docId = int(docIdFile.readline());
    docIdFile.seek(0);
    docIdFile.write("{}".format(docId + 1));
    docIdFile.truncate();
    docIdFile.close();
    
    newFileName = os.path.join("documents", "{}_{}".format(docId, os.path.basename(filePath)));
    shutil.copyfile(filePath, os.path.join(repoPath, newFileName));
    
    repoObj.index.add([os.path.join(repoPath, "docid"), newFileName]);
    
    importDocumentQuest = raw_input("Möchtest du noch ein Dokument importieren ([y]es/[n]o): ");
    if importDocumentQuest == 'y' or importDocumentQuest == 'yes':
        return importDocument(repoObj, repoPath);
    
    return 0;

def execCommand(repoPath, command, remote):
    if(command == "create"):
        if(is_git_dir(os.path.join(repoPath, ".git"))):
            print("Git-Repo existiert bereits. Abbruch...")
            return 0;
  
        repoObj = git.Repo.init(repoPath, True);
        
        docFile = open(os.path.join(repoPath, "docid"), 'w');
        docFile.write("0");
        docFile.close();
        
        repoObj.index.add(["docid"]);
        repoObj.index.commit("Erstelle neues Buchhaltungsrepo.");
        
        print("Git-Repo wurde angelegt.");
        return 0;
    
    repoObj = git.Repo(repoPath);
    remoteExists = False;
    try:
        remoteObj = repoObj.remote(remote);
        remoteExists = True;
    except ValueError:
        pass;
    
    if len(repoObj.untracked_files) != 0 or repoObj.is_dirty():
        print("Im Git-Repo sind Aenderungen ohne Commit gemacht wurden. Achtung, Inkosistenzen sind möglich!")
        return 1;
    
    if(command == "transaction"):        
        if remoteExists:
            remoteObj.pull();
            
        genDirList(repoPath);
        printAccountStructure(repoPath);
        
        fromAccount = getAccountInt("Bitte das Startkonto eingeben: ");
        toAccount = getAccountInt("Bitte das Zielkonto eingeben: ", fromAccount);
        transferAmount = readTransferAmount();
        
        # Open start and end account file
        fromAccountFile = open(os.path.join(repoPath, dirList[fromAccount], "account"));
        toAccountFile = open(os.path.join(repoPath, dirList[toAccount], "account"));
        
        # Calculate new amounts
        fromAccountAmount = int(fromAccountFile.readline());
        fromAccountAmount -= transferAmount;
        toAccountAmount = int(toAccountFile.readline());
        toAccountAmount += transferAmount;
        
        # Close files and reopen them
        fromAccountFile.close();
        toAccountFile.close();
        fromAccountFile = open(os.path.join(repoPath, dirList[fromAccount], "account"), 'w');
        toAccountFile = open(os.path.join(repoPath, dirList[toAccount], "account"), 'w');
        
        # Write new amounts and close files
        fromAccountFile.write(str(fromAccountAmount));
        toAccountFile.write(str(toAccountAmount));
        fromAccountFile.close();
        toAccountFile.close();
        
        repoObj.index.add([os.path.join(dirList[fromAccount], "account"), os.path.join(dirList[toAccount], "account")]);
        
        importDocumentQuest = raw_input("Möchtest du ein Dokument importieren ([y]es/[n]o): ");
        if importDocumentQuest == 'y' or importDocumentQuest == 'yes':
            importDocument(repoObj, repoPath);
        
        transferMsg = raw_input("Bitte eine Meldung für die Transaktion angeben: ");
        repoObj.index.commit(transferMsg);
        
        if remoteExists:
            remoteObj.push();
            
        print("Transaktion erfolgreich ausgeführt");
        
    elif(command == "accounts"):
        printAccountStructure(repoPath);
        
    elif(command == "createaccount"):
        if remoteExists:
            remoteObj.pull();
        
        acctName = raw_input("Bitte den Namen des Kontos angeben (einzelne Ebene durch \"/\" abtrennen): ");
        acctNameList = acctName.split(sep="/");
        
        if(os.path.isfile(os.path.join(repoPath, os.path.sep.join(acctNameList), "account"))):
            print("Konto existiert bereits.")
            return 1;
        
        path = repoPath;
        for dirName in acctNameList:
            path = os.path.join(path, dirName);
            
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno == errno.EEXIST and os.path.isdir(path):
                    pass;
                else:
                    raise;
            
            pathFile = os.path.join(path, "account")
            if(not os.path.isfile(pathFile)):
                accountFile = open(pathFile, 'w');
                accountFile.write("0");
                accountFile.close();
                repoObj.index.add([pathFile]);
        
        repoObj.index.commit("Lege neues Konto \"{}\" an.".format(acctName));
        
        if remoteExists:
            remoteObj.push();
            
        print("Konto wurde erfolgreich angelegt.");
        
    elif(command == "list"):
        for commit in repoObj.iter_commits():
            dateTuple = time.localtime(commit.authored_date);
            commitMsg = commit.message.strip();
            
            print("{:04d}-{:02d}-{:02d} {:02d}:{:02d} -- {}".format(dateTuple[0], dateTuple[1], dateTuple[2],
                                                                    dateTuple[3], dateTuple[4], commitMsg));
            
            if len(commit.parents) > 0:                                                
                diffList = commit.parents[0].diff(commit, create_patch=True)
                
                if len(diffList) >= 2:
                    fromAccount = None;
                    toAccount = None;
                    differenceAmount = 0;
                    
                    for diffEntry in diffList:
                        if(diffEntry.deleted_file or diffEntry.new_file or diffEntry.renamed or diffEntry.a_path == "docid"):
                            break;
                        
                        diffStr = diffEntry.diff.decode("utf-8") 
                        
                        removedValue = re.search(r"^-(-?\d+)", diffStr, re.MULTILINE);
                        removedValue = int(removedValue.group(1));
                        
                        addedValue = re.search(r"^\+(-?\d+)", diffStr, re.MULTILINE);
                        addedValue = int(addedValue.group(1));
                        
                        difference = addedValue - removedValue;
                        if difference < 0:
                            fromAccount = os.path.dirname(diffEntry.a_path);
                        elif difference > 0:
                            toAccount = os.path.dirname(diffEntry.a_path);
                            differenceAmount = difference;
                        else:
                            print("Eine Differenz von 0. Da ist wohl was schief gegangen.");
                            exit(1);
                        
                        continue;
                    
                    differenceAmount = str(differenceAmount);
                    differenceAmount = differenceAmount[:len(differenceAmount)-2] + "." + differenceAmount[len(differenceAmount)-2:]
                    try:
                        print("{} --> {}: {}".format(fromAccount, toAccount, differenceAmount));
                    except Exception:
                        pass;
    
            print("")
    return 0;

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_license = '''Created by Jan Luca Naumann.
  Copyright 2016. All rights reserved.

  Licensed under the GPL version 3.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
'''

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-p", "--repopath", dest="repopath", default=".", help="set path to git repo [default: %(default)s]")
        parser.add_argument("-r", "--remote", dest="remote", default="origin", help="set the name of the git remote [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument(dest="command", help="paths to folder(s) with source file(s) [default: %(default)s]",
                            choices=['create','transaction','createaccount','accounts','list'])

        # Process arguments
        args = parser.parse_args()
        
        repoPath = args.repopath.lstrip();
        command = args.command;
        remote = args.remote;

        execCommand(repoPath, command, remote);

        return 0;
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0;
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-p /tmp/gitTest") 
        sys.argv.append("test") 
    sys.exit(main())