import ROOT
import sys
import math
import argparse

parser = argparse.ArgumentParser(description='Produce a JSON file of the run,LS from ROOT tree.')
parser.add_argument('-f', '--filename', type=str, default="", help='The data certification file.')
parser.add_argument('-l', '--label',    type=str, default="", help="Label for output file")
parser.add_argument('-t', '--treename', type=str, default="certtree", help="Tree name")
args = parser.parse_args()

if args.filename=="":
    print "Re-run giving '-f FILENAME' as agrument"
    sys.exit(1)


def MakeListOfLists(inputList):
    outputList = []
    inputList.sort()
    firstLS = -1
    lastLS = -1
    for lumiSect in inputList:
        if firstLS == -1:
            firstLS = lumiSect
        if lastLS == -1:
            lastLS = lumiSect
        if lumiSect - lastLS == 1:
            lastLS = lumiSect 
        elif lumiSect - lastLS > 1:
            myList = [firstLS, lastLS]
            outputList.append(myList)
            firstLS = lumiSect
            lastLS = lumiSect
        if lumiSect == inputList[-1]:    
            myList = [firstLS, lastLS]
            outputList.append(myList)
    return outputList

# order the contents of inputList
# loop through contents of inputList
# variable outside loop containing what the first entry of the list should be
# append loop list to outputList


tfile=ROOT.TFile(args.filename)
tree=tfile.Get(args.treename)

tree.SetBranchStatus("*",0)
tree.SetBranchStatus("run",1)
tree.SetBranchStatus("LS",1)

nentries=tree.GetEntries()

LSbyRun={}

for ient in range(nentries):
    tree.GetEntry(ient)
    if not LSbyRun.has_key(tree.run):
        LSbyRun[tree.run]=[]
    LSbyRun[tree.run].append(tree.LS)

textFile = open("jsonOfReadRunLSs"+args.label+".txt","w")

textFile.write('{')
for run in LSbyRun.keys():
    newList = MakeListOfLists(LSbyRun[run])
    newListStr=str(newList)
    strToWrite="\"" + str(run) + "\": " + newListStr
    if run != LSbyRun.keys()[-1]:
        strToWrite=strToWrite+','
    strToWrite=strToWrite+'\n'

    textFile.write(strToWrite)

textFile.write('}')
textFile.close()
