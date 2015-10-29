import ROOT
import sys
import argparse
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument("-d",  "--dir", default="", help="EOS path to data cert tree files /store/user/..")
parser.add_argument("-f",  "--file",default="", help="EOS path to data cert tree file /store/user/..")
parser.add_argument("--nbxfile",default="NBX.csv", help="CSV file with run and NBX.")
parser.add_argument("--corrfile",default="", help="Corection file.")
args=parser.parse_args()

NBXPerRun={}
nbxfile=open(args.nbxfile)
for line in nbxfile.readlines():
    items=line.split(",")
    try:
        run=int(items[0])
        NBX=int(items[1])
        NBXPerRun[run]=NBX
    except:
        print "Problem with line",line

nbxfile.close()
print NBXPerRun


f_LHC=11245.6
xsec_PC=9.4e6

rawPCCFile=open('rawPCC.csv', 'a+')
PCLumiFile=open('PCLumi.csv', 'a+')

rawPCCFile.write("run,LS,PCC\n")
PCLumiFile.write("run,LS,PCLumi\n")


filenames=[]
if args.file!="":
    filenames.append("root://eoscms//eos/cms"+args.file)
if args.dir!="":
    filesInDirString=subprocess.check_output(["/afs/cern.ch/project/eos/installation/0.3.4/bin/eos.select","ls", args.dir])
    for fileInDir in filesInDirString.split("\n"):
        filenames.append("root://eoscms//eos/cms"+args.dir+"/"+fileInDir)

for filename in filenames:
    try:
        tfile=ROOT.TFile.Open(filename)
        tree=tfile.Get("certtree")
        
        nEntries=tree.GetEntries()
        
        for iEnt in range(nEntries):
            tree.GetEntry(iEnt)
            nClusterXNBX=tree.nCluster*NBXPerRun[tree.run]
            PCLumi_uncorr=nClusterXNBX*f_LHC/xsec_PC
            rawPCCFile.write(str(tree.run)+","+str(tree.LS)+","+str(nClusterXNBX)+"\n")
            PCLumiFile.write(str(tree.run)+","+str(tree.LS)+","+str(PCLumi_uncorr)+"\n")

    except:
        print "Problem with file",filename

rawPCCFile.close()
PCLumiFile.close()
