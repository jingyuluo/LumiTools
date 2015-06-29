import ROOT
import sys
import argparse
import os
import subprocess


def MakeJob(outputdir,jobid,filename,minfill,maxfill):
    joblines=[]
    joblines.append("source /cvmfs/cms.cern.ch/cmsset_default.sh")
    joblines.append("cd "+outputdir)
    joblines.append("cmsenv")
    joblines.append("python ../makeDataCertTree.py --pccfile="+filename+" --csvdir=/afs/cern.ch/user/m/marlow/public/lcr2/fillcsv -b --label="+str(jobid)+" --minfill="+str(minfill)+" --maxfill="+str(maxfill))
    
    scriptFile=open(outputdir+"/job_"+str(jobid)+".sh","w+")
    for line in joblines:
        scriptFile.write(line+"\n")
        
    scriptFile.close()

def SubmitJob(job,queue="8nh"):
    baseName=str(job.split(".")[0])
    cmd="bsub -q "+queue+" -J "+baseName+" -o "+baseName+".log < "+str(job)
    output=os.system(cmd)
    if output!=0:
        print job,"did not submit properly"
        print cmd


parser=argparse.ArgumentParser()
parser.add_argument("-p",  "--path",  help="EOS path to PCCNTuples... /store/user/..")
parser.add_argument("-d",  "--dir", default="JobsDir", help="Output directory")
parser.add_argument('--minfill', type=int, default=3818, help="Minimum fill number")
parser.add_argument('--maxfill', type=int, default=9999, help="Maximum fill number")
parser.add_argument("-s",  "--sub", action='store_true', default=False, help="bsub created jobs")

args=parser.parse_args()

# ls the eos directory
fileinfos=subprocess.check_output(["cmsLs", args.path])
fileinfos=fileinfos.split("\n")

filenames={}
for fileinfo in fileinfos:
    info=fileinfo.split()
    if len(info)<4:
        continue
    filename=info[4]
    if filename.find(".root") == -1:
        continue
    jobid=filename.split("/")[-1].split(".")[0].split("_")[-1]
    #print jobid, filename
    filenames[int(jobid)]=filename

fullOutPath=os.getcwd()
if not os.path.exists(args.dir):
    os.makedirs(args.dir)
fullOutPath=fullOutPath+"/"+args.dir

for job in filenames:
    MakeJob(fullOutPath,job,filenames[job],args.minfill,args.maxfill)

if args.sub:
    print "Submitting",len(filenames),"jobs"
    for job in filenames:
        SubmitJob(args.dir+"/job_"+str(job)+".sh")
        #raw_input()
