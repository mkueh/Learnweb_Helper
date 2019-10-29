#!/usr/bin/env python3

# Put this file in to execute it from any console
#
#

import configparser, argparse, time, locale, collections
import os, sys, glob, re, csv, numpy, pickle, shutil, glob
from zipfile import ZipFile

def main(delete):
    var = input("Type unpack or pack: ")
    #var = "pack"

    if(var == "unpack"):
        groupe = input("Type groupe: ")
        #groupe = "WI05"
        zipFiles = glob.glob('*.zip')

        for f in zipFiles:
            fileName = os.path.splitext(f)[0]

            taskname = getInformationFromZipname(f)
            studentIds = getStudents(f, groupe, taskname)

            createDirectoryStructure(f, studentIds, taskname)
            createValuationFile(f, studentIds)

    if(var == "pack"):
        numpyFiles = glob.glob('*.info')
        for f in numpyFiles:
            zipFilePath = f[:-4]
            infoFilePath = f
            zipFilePath = zipFilePath.strip()
            infoFilePath = infoFilePath.strip()
            createZipFile(zipFilePath,infoFilePath)

def getInformationFromZipname(zipFilePath:str) -> str:
    split = zipFilePath.split("-")
    taskName = split[2]
    return taskName

def getStudents(zipFilePath:str, group:str, taskname:str) -> dict:
    currentFile = ZipFile(zipFilePath, 'r');    
    out = {} # Empyt dict (grp, nr, vid)

    for exerciseFile in currentFile.namelist():
        split = exerciseFile.split("-")
        if(group in split[0]):
            temp = split[0].split(" ")
            grp = temp[1] + " " + temp[2]

            if(grp not in out):
                out[grp] = {}
                out[grp]["task"] = taskname
                out[grp]["student"] = []
                out[grp]["files"] = []
                        
            student = {}
            temp = exerciseFile.split("_")
            student["name"] = temp[0][len(split[0])+1:len(temp[0])]
            student["id"] = temp[1]
            if student not in out[grp]["student"]:
                out[grp]["student"].append(student)
            if(not checkIfFileisInserted(out[grp]["files"], os.path.basename(exerciseFile))):
                out[grp]["files"].append(exerciseFile)
    
    return collections.OrderedDict(sorted(out.items()))

def checkIfFileisInserted(l:list,s:str) -> bool:
    for i in l:
        if s in i:
            return True
    return False

def createDirectoryStructure(zipFilePath, studentIds:dict, taskname:str):
    currentFile = ZipFile(zipFilePath, 'r')
    fileName = os.path.splitext(zipFilePath)[0]
    
    for groupe in studentIds: 
        path = str(groupe)
        item = studentIds[groupe]

        #erstelle Ordner für Gruppe
        if not os.path.exists(path): os.makedirs(path)

        #kopiere Abgabe in den Ordner der Gruppe
        newfiles = []
        for exerciseFile in item["files"]:

            exerciseFileName = os.path.dirname(exerciseFile)
            uploadName = taskname
            
            currentFile.extract(exerciseFile, path)
            
            oldPath = os.path.join(path, os.path.dirname(exerciseFile))
            newPath = os.path.join(path, uploadName)
            
            if not os.path.exists(newPath): 
                os.rename(oldPath, newPath)
            else:
                shutil.move(os.path.join(path, exerciseFile), os.path.join(newPath,os.path.basename(exerciseFile)))
                shutil.rmtree(oldPath)

            newfiles.append(os.path.join(newPath,os.path.basename(exerciseFile)))              
        item["files"] = newfiles

    #speichere Zuordnungtabelle
    #numpy.save(taskname+'.npy', studentIds)
    with open(taskname+'.info', "wb") as myFile:
        pickle.dump(studentIds, myFile)
    currentFile.close()


def createValuationFile(zipFilePath, studentIds):
    header = ['ID', 'Gruppe', 'Bewertung', 'Zuletzt geändert (Bewertung)']
    row = ['Teilnehmer/in{}', '{}', '', time.strftime('%A, %d. %B %Y, %H:%M')]
        
    currentFile = ZipFile(zipFilePath, 'r')
    fileName = os.path.splitext(zipFilePath)[0]

    out = open(fileName + '.csv', 'wt', encoding='utf-8')
    
    writer = csv.writer(out, delimiter=';', lineterminator='\n', quoting=csv.QUOTE_ALL)
    writer.writerow(header)

    for grp in studentIds:
        for stu in studentIds[grp]["student"]:
            newRow = list(row)
            newRow[0] = newRow[0].format(stu["id"])
            newRow[1] = newRow[1].format(grp)
            writer.writerow(newRow)
          
    out.close()

def createZipFile(zipFilePath,infoFilePath):
    with open(infoFilePath, "rb") as myFile:
        dic = pickle.load(myFile)

    newZip = ZipFile(zipFilePath+"zip", 'w')
    for grp in dic:
        for stu in dic[grp]["student"]:
            folderpath = os.path.join(grp,dic[grp]["task"])
            folderpath = folderpath.strip()
            zipfile = createZipOfFolder(folderpath)
            newZip.write(zipfile,os.path.join(stu["name"]+"_"+stu["id"]+"_assignsubmission_file_","Feedback.zip"))
        os.remove(zipfile)
    newZip.close()

def createZipOfFolder(folderpath:str) -> str:    
    if os.path.exists(os.path.join(folderpath,"Feedback.zip")):
        return os.path.join(folderpath,"Feedback.zip")

    globsearch = os.path.join(folderpath,"*.*")
    Files = glob.glob(globsearch)
    newZip = ZipFile(os.path.join(folderpath,"Feedback.zip"), 'w')

    for f in Files:
        newZip.write(f,os.path.basename(f))

    newZip.close()
    return os.path.join(folderpath,"Feedback.zip")

if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description='Creates file and folder structure for student exercises.')
    parser.add_argument('-t', '--tut', action='store', default="DEFAULT", help="Specifies the tutorium to execute (use with -c to configure it)")
    parser.add_argument('-d', '--del', action='store_true', help="Delets all zip files from the directory after execution")

    args = vars(parser.parse_args())
    name = args['tut']

    main(args['del'])
