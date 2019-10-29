#!/usr/bin/env python3

# https://regex101.com/

import os, glob, re, csv
import argparse, time, pickle

from collections import OrderedDict
from zipfile import ZipFile

ACTION_PACK = 'pack'
ACTION_UNPACK = 'unpack'


def getExerciseGroups(zipFilePath, studentNames):
    currentFile = ZipFile(zipFilePath, 'r');    
    out = {} # Dict grpName => {students, files}

    regex = r"((?P<grp>.*?)_)?(?P<name>.*?)_(?P<id>[0-9]*)_assignsubmission_file_"

    for exerciseFile in currentFile.namelist():
        matches = re.match(regex, exerciseFile, re.DOTALL)
        
        if matches:
            grp = matches.group("grp")
            name = matches.group("name")
            
            if not grp: grp = name
            
            if name not in studentNames: continue
            
            if grp not in out:
                out[grp] = {}
                out[grp]["students"] = []
                out[grp]["files"] = []
            
            student = {}
            student["name"] = matches.group("name")
            student["id"] = matches.group("id")
            
            if student not in out[grp]["students"]: out[grp]["students"].append(student)
            if not checkIfFileIsInserted(out[grp]["files"], os.path.basename(exerciseFile)):
                out[grp]["files"].append(exerciseFile)
    
    return OrderedDict(sorted(out.items(), key=lambda t: t[0]))


def checkIfFileIsInserted(l:list,s:str) -> bool:
    for i in l:
        if s in i:
            return True
    return False


def createDirectoryStructure(zipFilePath, groups):
    currentFile = ZipFile(zipFilePath, 'r')
    exerciseName = os.path.splitext(zipFilePath)[0]
    
    for grpName, obj in groups.items():
        if not os.path.exists(grpName): os.makedirs(grpName)

        for exerciseFile in obj["files"]:
            currentFile.extract(exerciseFile, grpName)
        
        if obj["files"]:
            oldPath = os.path.join(grpName, os.path.dirname(obj["files"][0]))
            newPath = os.path.join(grpName, exerciseName)

            os.rename(oldPath, newPath)
            
            obj["files"] = [os.path.join(newPath,os.path.basename(it)) for it in obj["files"]]
    
    with open(exerciseName+'.info', "wb") as infoFile:
        pickle.dump(groups, infoFile)
        
    currentFile.close()


def isSingleStudentExercise(groups):
    for grpName, obj in groups.items():
        if grpName == obj["students"][0]: return False
        
    return True


def createValuationFile(zipFilePath, groups):
    header = ['ID', 'Vollständiger Name', 'Gruppe', 'Bewertung', 'Zuletzt geändert (Bewertung)']
    row = ['Teilnehmer/in{}', '{}', '{}', '', time.strftime('%A, %d. %B %Y, %H:%M')]
    
    singleExercise = isSingleStudentExercise(groups)
    
    if singleExercise: # Remove Gruppe item from csv
        header.pop(2) 
        row.pop(2)
        
    currentFile = ZipFile(zipFilePath, 'r');
    exerciseName = os.path.splitext(zipFilePath)[0]

    out = open(exerciseName + '.csv', 'wt', encoding='utf-8')
    
    writer = csv.writer(out, delimiter=',', lineterminator='\n', quoting=csv.QUOTE_ALL)
    writer.writerow(header)

    for grpName, obj in groups.items():
        
        for student in obj["students"]:
            newRow = list(row)
            
            newRow[0] = newRow[0].format(student["id"])
            newRow[1] = newRow[1].format(student["name"])
            
            if not singleExercise: newRow[2] = newRow[2].format(grpName)
            
            writer.writerow(newRow)
          
    out.close()


def createZipFile(zipFilePath, infoFilePath):
    with open(infoFilePath, "rb") as infoFile:
        groups = pickle.load(infoFile)

    newZip = ZipFile(zipFilePath + "-Feedback.zip", 'w')
    
    for grpName, obj in groups.items():
		    
        for student in obj["students"]:
            files = obj["files"]
            
            for f in files:
                filename = os.path.basename(f)
                newZip.write(f,os.path.join(student["name"]+"_"+student["id"]+ "_assignsubmission_file_",filename))
    
    newZip.close()


if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description='Creates file and folder structure for student exercises.')
    
    parser.add_argument('action', type=str, choices=[ACTION_PACK, ACTION_UNPACK], help="the action the script should perform")
    parser.add_argument('-f', type=str, metavar="file", default="Teilnehmer.txt", help="specifies a file with student names")
    
    args = vars(parser.parse_args())
    
    if args['action'] == ACTION_UNPACK:
        zipFiles = glob.glob('*.zip');

        with open(args['f']) as namesFile:
            studentNames = namesFile.readlines()

        # remove whitespace characters like \n at the end of each line
        studentNames = [x.strip() for x in studentNames]  

        for f in zipFiles:
            fileName = os.path.splitext(f)[0]
            groups = getExerciseGroups(f, studentNames)

            createDirectoryStructure(f, groups)
            createValuationFile(f, groups)
            
    elif args['action'] == ACTION_PACK:
        infoFiles = glob.glob('*.info')
        for f in infoFiles: createZipFile(f[:-5],f)
