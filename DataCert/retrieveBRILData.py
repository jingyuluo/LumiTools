import subprocess
import sys, os
import argparse
import pickle

def CallBrilcalcAndProcess(onlineLumiDict,type="best"):
    cmd=["brilcalc","lumi","--byls"]
    if args.json!="":
        cmd.extend(["-i",args.json])
    else:
        if args.run!=0:
            cmd.extend(["-r",str(args.run)])
        if args.fill!=0:
            cmd.extend(["-f",str(args.fill)])

    if type is not "best":
        cmd.append("--type="+type)
    brilcalcOutput=subprocess.check_output(cmd)
    
    lines=brilcalcOutput.split("\n")
    for line in lines:
        if line.find("STABLE BEAMS")!=-1:
            items=line.split("|")
            try:
                lskey=(int(items[1].strip().split(":")[0]),int(items[2].strip().split(":")[0])) #run,ls
                if not onlineLumiDict.has_key(lskey):
                    onlineLumiDict[lskey]={}
                    onlineLumiDict[lskey]["fill"]=items[1].strip().split(":")[1]
                if type is "best":
                    best=items[9].strip()
                    if best=="HF":
                        best="HFOC"
                    onlineLumiDict[lskey][type]=best #whose lumi is best
                    onlineLumiDict[lskey]["PU_best"]=items[8].strip() #PU
                else:
                    onlineLumiDict[lskey][type]=items[6].strip() #integrated lumi
            except:
                print "Problem with line",line
   

parser = argparse.ArgumentParser(description='Get integrated luminosity per LS in a run or fill')
parser.add_argument('-l', '--label',type=str, default="",help="Label for output file")
parser.add_argument('-f', '--fill', type=int, default=0, help="fill number")
parser.add_argument('-r', '--run',  type=int, default=0, help="run number")
parser.add_argument('-j', '--json', type=str, default="", help="JSON formatted file with runs and LSs ranges you desire")
parser.add_argument('-o', '--overwrite', action='store_true', default=False, help="Overwrite data if it already exists (default False)")
parser.add_argument('--datadir',    type=str, default="brildata", help="Location to put/retrieve bril data")

args = parser.parse_args()

    
if args.run==0 and args.fill==0 and args.json=="":
    print "Try again... need to give a non-zero fill or run"
    sys.exit(4)


if args.run!=0 and args.fill!=0 and args.json!="":
    print "I have been given run",args.run,"and fill",args.fill
    print "Setting run to 0 and retrieving lumi from fill"
    args.run=0

try:
    checkBrilCalc=subprocess.check_output(["brilcalc","-h"])
except:
    print "brilcalc needs the environment set.  Please use the"
    print "following commands."
    print "cmsenv"
    print "source brilcalc_env.sh"
    sys.exit(4)

if not os.path.exists(args.datadir):
    os.mkdir(args.datadir)

if not args.overwrite:
    haveBrilData=False
    files=os.listdir(args.datadir)
    for file in files:
        if args.run!=0:
            splitBy="run"
            partitionStr=str(args.run)
        if args.fill!=0:
            splitBy="fill"
            partitionStr=str(args.fill)
        fileNameParts=file.split(splitBy)
        if len(fileNameParts)==2:
            if fileNameParts[1].find(partitionStr)!=-1:
                print "Found",file
                haveBrilData=True
                myDataFile=file
                break
    
    if haveBrilData:
        print "BRIL data already retrieved."
        sys.exit(0)

onlineLumi={}
types=["best","PLT","HFOC","BCM1F"]
            
for type in types:
    CallBrilcalcAndProcess(onlineLumi,type)



if args.run!=0:
    outFileName="run"+str(args.run)+".csv"
    pklFileName="run"+str(args.run)+".pkl"
if args.fill!=0:
    outFileName="fill"+str(args.fill)+".csv"
    pklFileName="fill"+str(args.fill)+".pkl"
if args.json!="":
    outFileName=args.json.split(".")[0]+".csv"
    pklFileName=args.json.split(".")[0]+".pkl"


pklFile=open(args.datadir+"/"+pklFileName, 'w')
pickle.dump(onlineLumi, pklFile)
pklFile.close()

outFile=open(args.datadir+"/"+outFileName,"w+")

allKeys=onlineLumi.keys()
allKeys.sort()

keyKey=["run","ls"]
for lskey in allKeys:
    iPart=0
    for part in lskey:
        outFile.write(keyKey[iPart]+","+str(part)+",")
        iPart=iPart+1
    for detector in onlineLumi[lskey]:
        outFile.write(detector+","+onlineLumi[lskey][detector]+",")
    outFile.write("\n")

outFile.close()
