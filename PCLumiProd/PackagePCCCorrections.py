import sys, os
from math import exp
import subprocess
import ROOT
import argparse


parser=argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="The path to the corrections file.")
parser.add_argument("-r", "--runs", default="", help="Comma separated list of runs.")
parser.add_argument("-a", "--auto", default=False, action='store_true', help="Find list of runs from the histograms in the file.")
args=parser.parse_args()


tfile=ROOT.TFile(args.file)
if args.runs!="":
    runs=args.runs.split(",")
else:
    runs=[]

if args.auto:
    listFromFile=tfile.GetListOfKeys()
    runs=[]
    #print "size",listFromFile.GetSize()
    for iList in range(listFromFile.GetSize()):
    #    print iList,listFromFile.At(iList).GetName()
        thisName=listFromFile.At(iList).GetName()
        if thisName.find("Overall_Correction")!=-1:
            run=thisName.split("_")[2]
            runs.append(run)
            #print thisName,run
#print runs

corrections={}
for run in runs:
    h_origin=tfile.Get("Before_Corr_"+run)
    h_after=tfile.Get("After_Corr_"+run)
    
    total_origin=0
    total_after=0
    for i in range(3600):
        if h_origin.GetBinContent(i) > 0.5:
            total_origin+=h_origin.GetBinContent(i)
            total_after+=h_after.GetBinContent(i)
    
    corrections[run]=total_after/total_origin 


corrPCCFile=open('corrPCC.csv', 'a+')
corrRuns=corrections.keys()
corrRuns.sort()

for run in corrRuns:
    corrPCCFile.write(str(run)+","+'{:.4f}'.format(corrections[run])+"\n")

corrPCCFile.close()
