import ROOT
import sys
import argparse
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument("-d",  "--dir", default="", help="EOS path to data cert tree files /store/user/..")
parser.add_argument("-f",  "--file",default="", help="EOS path to data cert tree file /store/user/..")
parser.add_argument("--nbxfile",default="NBX.csv", help="CSV file with run and NBX.")
parser.add_argument("--corrfile",default="", help="Corection file.")
parser.add_argument("--yaml",default="", help="yaml file to append.")
parser.add_argument("--xsec",default=9.4e6, help="PC cross section (default:  9.4e6 ub).")
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
#print NBXPerRun


corrPerRun={}
corrfile=open(args.corrfile)
for line in corrfile.readlines():
    items=line.split(",")
    try:
        run=int(items[0])
        print run,
        corrFac=float(items[1])
        print corrFac
        corrPerRun[run]=corrFac
    except:
        print "Problem with line",line

corrfile.close()
print corrPerRun


f_LHC=11245.6

rawPCCFile=open('rawPCC.csv', 'a+')
PCLumiFile=open('PCLumi.csv', 'a+')
if args.yaml!="":
    yamlFile=open(args.yaml, 'a+')

rawPCCFile.write("run,LS,PCC\n")
PCLumiFile.write("run,LS,PCLumi\n")

if args.yaml!="":
    if len(yamlFile.readlines())==0:
        yamlFile.write("name: pccv1\n")
        yamlFile.write("applyto: lumi\n")
        yamlFile.write("datasource: pcc\n")
        yamlFile.write("istypedefault: 0\n")
        yamlFile.write("comments: 2015B 50 ns data\n")
        yamlFile.write("since:\n")

    runs=corrPerRun.keys()
    runs.sort()
    for run in runs:
       yamlFile.write("      - "+str(run)+":\n")
       yamlFile.write("              func: poly1dWafterglow\n")
       yamlFile.write("              payload: {'coefs': '"+str(f_LHC/args.xsec)+",0.', 'afterglowthresholds':'(1,"+str(corrPerRun[run])+")'}\n")
       yamlFile.write("              comments: 2015, egev 6500, PROTPHYS, preliminary VdM calibration\n")

yamlFile.close()


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
            PCLumi_uncorr=nClusterXNBX*f_LHC/args.xsec
            PCLumi_corr=PCLumi_uncorr
            if corrPerRun.has_key(tree.run):
                PCLumi_corr=PCLumi_corr*corrPerRun[tree.run]
            else:
                print "No corrections available for run",tree.run
            rawPCCFile.write(str(tree.run)+","+str(tree.LS)+","+str(nClusterXNBX)+"\n")
            PCLumiFile.write(str(tree.run)+","+str(tree.LS)+","+str(PCLumi_uncorr)+"\n")

    except:
        print "Problem with file",filename

rawPCCFile.close()
PCLumiFile.close()
