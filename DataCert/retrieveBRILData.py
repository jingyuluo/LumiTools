import subprocess
import sys, os
import argparse
import pickle
from scipy import stats

def CallBrilcalcAndProcess(onlineLumiDict,type="best"):
    cmd=["brilcalc","lumi","--byls"]
    if args.json!="":
        cmd.extend(["-i",args.json])
    else:
        if args.run!=0:
            cmd.extend(["-r",str(args.run)])
        if args.fill!=0:
            cmd.extend(["-f",str(args.fill)])
        if args.xing:
            cmd.extend(["--xing"])

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
                if args.xing:
                    if type is not "best":
                        bxname = type+"_BX"
                        onlineLumiDict[lskey][bxname]={}
                        bxlist = items[10].lstrip().lstrip("[").rstrip().rstrip("]")
                        bxlist = bxlist.split()
                        for i in range(len(bxlist)):
                            if i%3==0:
                                try:
                                    onlineLumiDict[lskey][bxname][int(bxlist[i])]=float(bxlist[i+1])
                                except: 
                                    print lskey,type,"bx",bxlist[i],"can't be integer"
                                    print "or lumi",bxlist[i+1],"can't be float"
                               
            except:
                print "Problem with line",line
   

parser = argparse.ArgumentParser(description='Get integrated luminosity per LS in a run or fill')
parser.add_argument('-l', '--label',type=str, default="",help="Label for output file")
parser.add_argument('-f', '--fill', type=int, default=0, help="fill number")
parser.add_argument('-r', '--run',  type=int, default=0, help="run number")
parser.add_argument('-j', '--json', type=str, default="", help="JSON formatted file with runs and LSs ranges you desire")
parser.add_argument('-o', '--overwrite', action='store_true', default=False, help="Overwrite data if it already exists (default False)")
parser.add_argument('--datadir',    type=str, default="brildata", help="Location to put/retrieve bril data")
parser.add_argument('-x', '--xing', action='store_true', default=False, help="Get the Lumi per BX")
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
types=["best","PLTZERO","HFOC","BCM1F"]
            
for type in types:
    CallBrilcalcAndProcess(onlineLumi,type)

onlineLumi["runInfo"]={}
onlineLumi["runInfo"]["nActiveBXHF"]={}

lsKeys = onlineLumi.keys()
lsKeys.sort()
    
nBXInRuns={}
nBXListInRuns={}

for lsKey in lsKeys:
    if onlineLumi[lsKey].has_key('HFOC_BX'):
        HFbxkeys = onlineLumi[lsKey]['HFOC_BX'].keys()
        HFbxkeys.sort()
        
        HFMaxLumi=0
        for HFbxkey in HFbxkeys :
            HFMaxLumi=max(HFMaxLumi,onlineLumi[lsKey]['HFOC_BX'][HFbxkey])

        HFActiveBX=0
        for HFbxkey in HFbxkeys :
            HFLumi_thisbx=onlineLumi[lsKey]['HFOC_BX'][HFbxkey]
            if HFLumi_thisbx>0.2*HFMaxLumi and HFLumi_thisbx>0.1:
                HFActiveBX=HFActiveBX+1

        if not nBXListInRuns.has_key(lsKey[0]):
            nBXListInRuns[lsKey[0]]=[]
        nBXListInRuns[lsKey[0]].append(HFActiveBX)

for run in nBXListInRuns.keys():
    modes=stats.mode(nBXListInRuns[run])
    maxMode=0
    maxModeInd=-1
    for iMod in range(len(modes)):
        if maxMode<modes[iMod]:
            maxModeInd=iMod
        elif maxMode==modes[iMod]:
            print "equal parts",maxMode,modes[iMod],maxModeInd,iMod
        print iMod,modes[iMod],nBXListInRuns[run][iMod]
    onlineLumi["runInfo"]["nActiveBXHF"][run]=nBXListInRuns[run][maxModeInd]
    

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
    if lskey=="runInfo":
        outFile.write(lskey+",")
        for itemKey in onlineLumi["runInfo"]:
            outFile.write(str(itemKey)+","+str(onlineLumi[lskey][itemKey])+",")
        outFile.write("\n")
        continue
            
        

    iPart=0
    for part in lskey:
        outFile.write(keyKey[iPart]+","+str(part)+",")
        iPart=iPart+1
    for detector in onlineLumi[lskey]:
        if detector.find("_")==-1:
            outFile.write(detector+","+onlineLumi[lskey][detector]+",")
    if args.xing:
        for type in types:
            if type=="best": 
                continue
            if onlineLumi[lskey].has_key(type+"_BX"):
                outFile.write(type+"BX,")
                bxs=onlineLumi[lskey][type+"_BX"].keys()
                bxs.sort()
                for bx in bxs:
                    outFile.write(str(bx)+","+str(onlineLumi[lskey][type+"_BX"][bx])+",")
    outFile.write("\n")

outFile.close()
