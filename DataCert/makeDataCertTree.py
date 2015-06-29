import ROOT
import sys,os
import numpy
import array
import math
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--pccfile', type=str, default="", help='The pccfile to input (pixel clusters and vertices)')
parser.add_argument('--csvdir', type=str, default="/afs/cern.ch/user/m/marlow/public/lcr2/fillcsv/", help='bril data is here')
parser.add_argument('--nobril', type=bool, default=False, help="Don\'t process bril data (default false)")
parser.add_argument('--label', type=str, default="", help="Label for output file")
parser.add_argument('--minfill', type=int, default=3818, help="Minimum fill number")
parser.add_argument('--maxfill', type=int, default=9999, help="Maximum fill number")
parser.add_argument('-b', '--isBatch', default=False, action="store_true", help="Maximum fill number")

args = parser.parse_args()

if args.nobril:
    args.csvdir=""


f_LHC = 11245.6
t_LS=math.pow(2,18)/f_LHC
xsec_mb=80000. #microbarn


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


weightThreshold=1e-5

def AverageWithWeight(list):
    sumValue=0
    sumWeight=0
    for value,weight in list:
        sumValue=sumValue+value
        sumWeight=sumWeight+weight

    if sumWeight>0:
        return float(sumValue)/sumWeight

def GetWeightedValues(list):
    count=0
    sumOfWeights=0
    sumOfWeights2=0
    weightedSum=0

    for value,weight in list:
        #print value,weight
        if weight<weightThreshold:
            continue
        count=count+1
        sumOfWeights=sumOfWeights+weight
        sumOfWeights2=sumOfWeights2+math.pow(weight,2)
        weightedSum=weightedSum+weight*value

    return count,sumOfWeights,sumOfWeights2,weightedSum


def GetMean(list):
    #print "list length",len(list)
    count,sumOfWeights,sumOfWeights2,weightedSum=GetWeightedValues(list)
    mean=GetMeanFromWeightedValues(sumOfWeights,weightedSum)
    return mean


def GetMeanFromWeightedValues(sumOfWeights,weightedSum):
    mean=0
    if sumOfWeights>0:
        mean=weightedSum/sumOfWeights
    return mean


def GetMeanAndMeanError(list):
    count,sumOfWeights,sumOfWeights2,weightedSum=GetWeightedValues(list)
    if sumOfWeights2==0:
        return -99,-99
    neff=math.pow(sumOfWeights,2)/sumOfWeights
    mean=GetMeanFromWeightedValues(sumOfWeights,weightedSum)

    #print neff,count,sumOfWeights
    
    weightedSumDiffFromAve2=0
    for value,weight in list:
        if weight<weightThreshold:
            continue
        weightedSumDiffFromAve2=weightedSumDiffFromAve2+weight*math.pow(value-mean,2) 

    stddev=0
    meanError=0
    if count>2:
        stddev=math.sqrt( weightedSumDiffFromAve2 / (sumOfWeights))
        meanError=stddev/math.sqrt(neff)

    #print "stddev",stddev

    return mean,meanError



csvfilenames=[]

if not args.nobril:
    files=os.listdir(args.csvdir)
    files.sort()
    for file in files:
        if file.find("Fill") !=-1:
            thisFill=int(file.split("ill")[1].split(".csv")[0])
            if thisFill>=args.minfill and thisFill<=args.maxfill:
                csvfilenames.append(args.csvdir+"/"+file)


print len(csvfilenames)," csv files"

onlineLumi={} #(run,LS,LN)

fields = ['Fill','Run','LS','NB4','Mode','secs','msecs','deadfrac','PrimarySource','PrimaryLumi','HF','HFRaw','PLT','PLTRaw','PLTZero','PLTZeroRaw','BCMF','BCMFRaw','Ncol','Text','I','L[I]']
icsv=1
for csvfilename in csvfilenames:
    print csvfilename,icsv
    icsv=icsv+1
    lines = open(csvfilename,'r').readlines()
    for line in lines : 
        vals = line.split(',')
        try:
            key=(int(float(vals[fields.index('Run')])),int(float(vals[fields.index('LS')])),int(float(vals[fields.index('NB4')])))
            if onlineLumi.has_key(key):
                print "onlineLumi ALREADY HAS KEY",key
                print onlineLumi[key]['line']
                print line
            
            onlineLumi[key]={}
            onlineLumi[key]['line']=line
            for field in fields:
                val=vals[fields.index(field)]
                if is_number(val):
                    val=float(val)
                onlineLumi[key][field]=val
        except:
            if line.split(",")[fields.index('PrimaryLumi')]!="0" and line.split(",")[fields.index('PrimaryLumi')]!="PrimaryLumi":
                print "didn't work for line with non-zero lumi"
                print line

print "len(onlineLumi),",len(onlineLumi)


onlineLumiPerLSList={} #(run,LS)
onlineLumiPerLSMerged={} #(run,LS)

for LN in onlineLumi.keys():
    if not onlineLumiPerLSList.has_key((LN[0],LN[1])):
        onlineLumiPerLSList[(LN[0],LN[1])]=[]
        onlineLumiPerLSMerged[(LN[0],LN[1])]={}
    onlineLumiPerLSList[(LN[0],LN[1])].append(onlineLumi[LN])

noField={}

for LS_key in onlineLumiPerLSList:
    unMergedLists={}
    mergedLists={}
    for field in fields:
        unMergedLists[field]=[]
        mergedLists[field]=0
    for NB_dict in onlineLumiPerLSList[LS_key]:
        for field in fields:
            try:
                unMergedLists[field].append(NB_dict[field])
            except:
                if not noField.has_key(field):
                    noField[field]=0
                noField[field]=noField[field]+1

                #print "unMergedList has no",field,"for",LS_key


    for field in unMergedLists:
        item_list=unMergedLists[field]
        mergedLists[field]=unMergedLists[field]
        if len(item_list)>0:
            if is_number(item_list[0]):
                try:
                    mergedLists[field]=sum(unMergedLists[field])/len(unMergedLists[field])
                except:
                    print unMergedLists[field]

    onlineLumiPerLSMerged[LS_key]=mergedLists

print "Missing fields:",noField

maxLS={}
    
vertexCounts={}
pixelCounts={}
lumiEstimate={}
# key is bx,LS and LS


if args.pccfile!="":
    filename=args.pccfile

    if filename.find("/store")==0: # file is in eos
        filename="root://eoscms//eos/cms"+filename
    
    tfile=ROOT.TFile.Open(filename)
    
    tree=tfile.Get("lumi/tree")
    
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("nGoodVtx*",1)
    tree.SetBranchStatus("run*",1)
    tree.SetBranchStatus("LS*",1)
    tree.SetBranchStatus("event*",1)
    tree.SetBranchStatus("nPixelClusters*",1)
    tree.SetBranchStatus("layer*",1)
    tree.SetBranchStatus("BXNo",1)

    nentries=tree.GetEntries()
    
    print nentries
    maxNBX=0
    for iev in range(nentries):
    #for iev in range(60):
        tree.GetEntry(iev)
        #if tree.nPU < 70:
        #    continue
        #print "PU",tree.nPU
        if iev%1000==0:
            print "iev,",iev
            print "(tree.run,tree.LS)",tree.LS
            print "len(tree.nPixelClusters)",len(tree.nPixelClusters)
            print "len(tree.layers)",len(tree.layers)
        if len(tree.nPixelClusters)==0:
            continue
        
        LSKey=(tree.run,tree.LS)
        
        if LSKey not in vertexCounts:
            vertexCounts[LSKey]=[]
    
        for ibx,nGoodVtx in tree.nGoodVtx:
            vertexCounts[LSKey].append([nGoodVtx,tree.BXNo[ibx]])
        
    
        pixelCount={}
        bxids={}
        if pixelCount.has_key((tree.run,tree.LS)) == 0:
            pixelCount[(tree.run,tree.LS)]=[0]*6
            pixelCount[(tree.run,tree.LS)].append({}) # for bx->counts
       
        if pixelCounts.has_key((tree.run,tree.LS)) == 0:
            pixelCounts[(tree.run,tree.LS)]=[[] for x in xrange(6)]
            pixelCounts[(tree.run,tree.LS)].append({})
    
        if not maxLS.has_key(tree.run):
            maxLS[tree.run]=0
        
        if tree.LS>maxLS[tree.run]:
            maxLS[tree.run]=tree.LS+5
    
        layerNumbers=[]
        for item in tree.layers:
            layerNumbers.append(item[1])
    
        counter=0
        for item in tree.nPixelClusters:
            counter=counter+1
            bxid=item[0][0]
            module=item[0][1]
            layer=tree.layers[module]
            clusters=item[1]
    
            if layer==6:
                layer=1
    
            pixelCount[(tree.run,tree.LS)][layer]=pixelCount[(tree.run,tree.LS)][layer]+clusters
            if not pixelCount[(tree.run,tree.LS)][6].has_key(bxid):
                pixelCount[(tree.run,tree.LS)][6][bxid]=0
    
            if layer!=1:
                pixelCount[(tree.run,tree.LS)][6][bxid]=pixelCount[(tree.run,tree.LS)][6][bxid]+clusters
                pixelCount[(tree.run,tree.LS)][0]=pixelCount[(tree.run,tree.LS)][0]+clusters
    
        
            if bxids.has_key(bxid)==0:
               bxids[bxid]=1
            else:
               bxids[bxid]=bxids[bxid]+1
    
        pixelCounts[(tree.run,tree.LS)][0].append([pixelCount[(tree.run,tree.LS)][0]/float(tree.eventCounter),1])
        for layer in range(1,6):
            #print pixelCount[(tree.run,tree.LS,layer)], tree.eventCounter
            pixelCounts[(tree.run,tree.LS)][layer].append([pixelCount[(tree.run,tree.LS)][layer]/float(tree.eventCounter),1])
        for bxid in bxids:
            if not pixelCounts[(tree.run,tree.LS)][6].has_key(bxid):
                pixelCounts[(tree.run,tree.LS)][6][bxid]=[]
            pixelCounts[(tree.run,tree.LS)][6][bxid].append([pixelCount[(tree.run,tree.LS)][6][bxid]/float(tree.BXNo[bxid]),1])



cmskeys=pixelCounts.keys()
brilkeys=onlineLumiPerLSMerged.keys()
LSKeys=list(set(cmskeys+brilkeys))

LSKeys.sort()

if LSKeys[0][0]==123456:
    newfilename="dataCertification_"+str(LSKeys[1][0])+"_"+str(LSKeys[-1][0])+"_"+args.label+".root"
else:
    newfilename="dataCertification_"+str(LSKeys[0][0])+"_"+str(LSKeys[-1][0])+"_"+args.label+".root"
    
newfile=ROOT.TFile(newfilename,"recreate")
newtree=ROOT.TTree("certtree","validationtree")

run = array.array( 'l', [ 0 ] )
LS  = array.array( 'l', [ 0 ] )
nBX = array.array( 'l', [ 0 ] )
nCluster    = array.array( 'd', [ 0 ] )
nPCPerLayer = array.array( 'd', 5*[ 0 ] )

HFLumi    = array.array( 'd', [ 0 ] )
BCMFLumi  = array.array( 'd', [ 0 ] )
PLTLumi   = array.array( 'd', [ 0 ] )
BestLumi  = array.array( 'd', [ 0 ] )
BestLumi_PU  = array.array( 'd', [ 0 ] )

HFLumi_integrated    = array.array( 'd', [ 0 ] )
BCMFLumi_integrated  = array.array( 'd', [ 0 ] )
PLTLumi_integrated   = array.array( 'd', [ 0 ] )
BestLumi_integrated  = array.array( 'd', [ 0 ] )

hasBrilData = array.array('b', [0])
hasCMSData  = array.array('b', [0])

pixel_xsec         = array.array( 'd', [ 0 ] )
pixel_xsec_layers  = array.array( 'd', 5*[ 0 ] )

nPCPerBXid  = array.array( 'd', 3600*[ 0 ] )
BXid        = array.array( 'd', 3600*[ 0 ] )

goodVertices  = array.array( 'd', [ 0 ] )
goodVertices_xsec  = array.array( 'd', [ 0 ] )
goodVertices_eff  = array.array( 'd', [ 0 ] )
# 0 - average vertices; 1 - xsec; 2 - vertex efficiency


newtree.Branch("run",run,"run/I")
newtree.Branch("LS",LS,"LS/I")
newtree.Branch("nBX",nBX,"nBX/I")
newtree.Branch("nCluster",nCluster,"nCluster/D")
newtree.Branch("nPCPerLayer",nPCPerLayer,"nPCPerLayer[5]/D")

newtree.Branch("pixel_xsec",pixel_xsec,"pixel_xsec/D")
newtree.Branch("pixel_xsec_layers",pixel_xsec_layers,"pixel_xsec_layers[5]/D")


newtree.Branch("BXid",BXid,"BXid[nBX]/D")
newtree.Branch("nPCPerBXid",nPCPerBXid,"nPCPerBXid[nBX]/D")

newtree.Branch("BestLumi",BestLumi,"BestLumi/D")
newtree.Branch("HFLumi",HFLumi,"HFLumi/D")
newtree.Branch("BCMFLumi",BCMFLumi,"BCMFLumi/D")
newtree.Branch("PLTLumi",PLTLumi,"PLTLumi/D")

newtree.Branch("BestLumi_integrated",BestLumi_integrated,"BestLumi_integrated/D")
newtree.Branch("HFLumi_integrated",HFLumi_integrated,"HFLumi_integrated/D")
newtree.Branch("BCMFLumi_integrated",BCMFLumi_integrated,"BCMFLumi_integrated/D")
newtree.Branch("PLTLumi_integrated",PLTLumi_integrated,"PLTLumi_integrated/D")

newtree.Branch("BestLumi_PU",BestLumi_PU,"BestLumi_PU/D")

newtree.Branch("hasBrilData",hasBrilData,"hasBrilData/O")
newtree.Branch("hasCMSData",hasCMSData,"hasCMSData/O")

newtree.Branch("goodVertices",      goodVertices,     "goodVertices/D")
newtree.Branch("goodVertices_xsec", goodVertices_xsec,"goodVertices_xsec/D")
newtree.Branch("goodVertices_eff",  goodVertices_eff, "goodVertices_eff/D")


hists={}
PCCPerLayer=[118.,44.3,39.2,34.9,22.3,23.9]
for key in LSKeys:
    run[0]=key[0]
    LS[0]=key[1]
    #print key
    hasBrilData[0]=False
    hasCMSData[0]=False
    
    HFLumi[0]=-1
    BestLumi[0]=-1
    PLTLumi[0] =-1
    BCMFLumi[0]=-1
    
    HFLumi_integrated[0]=-1
    BestLumi_integrated[0]=-1
    PLTLumi_integrated[0] =-1
    BCMFLumi_integrated[0]=-1
        
    BestLumi_PU[0]=-1
    pixel_xsec[0]=-1

    goodVertices[0]=-1
    goodVertices_xsec[0]=-1
    goodVertices_eff[0]=-1

    for layer in range(0,5):
        pixel_xsec_layers[layer]=-1
        nPCPerLayer[layer]=-1

    try:
        if key in brilkeys:
            hasBrilData[0]=True
            HFLumi[0]=onlineLumiPerLSMerged[key]['HF']
            BestLumi[0]=onlineLumiPerLSMerged[key]['PrimaryLumi']
            PLTLumi[0] =onlineLumiPerLSMerged[key]['PLT']
            BCMFLumi[0]=onlineLumiPerLSMerged[key]['BCMF']
            
            HFLumi_integrated[0]=onlineLumiPerLSMerged[key]['HF']*t_LS
            BestLumi_integrated[0]=onlineLumiPerLSMerged[key]['PrimaryLumi']*t_LS
            PLTLumi_integrated[0] =onlineLumiPerLSMerged[key]['PLT']*t_LS
            BCMFLumi_integrated[0]=onlineLumiPerLSMerged[key]['BCMF']*t_LS
            

        if key in cmskeys:
            hasCMSData[0]=True
            count=0
            mean=AverageWithWeight(vertexCounts[key])
            #print mean
            goodVertices[0]=mean
            
            
            for PCCs in pixelCounts[key]:
                if count==0:
                    mean,error=GetMeanAndMeanError(PCCs)
                    nCluster[0]=mean
                elif count<6:
                    mean,error=GetMeanAndMeanError(PCCs)
                    nPCPerLayer[count-1]=mean
                else:
                    ibx=0
                    nBX[0]=len(PCCs)
                    for bxid in PCCs:
                        mean,error=GetMeanAndMeanError(PCCs[bxid])
                        BXid[ibx]=bxid
                        nPCPerBXid[ibx]=mean
                        ibx=ibx+1
                        if ibx>nBX[0]:
                            print "ibx,nBX[0],",ibx,nBX[0],", but WHY?!!!"

                count=count+1 
  
        if hasCMSData[0] and hasBrilData[0]: 
            BestLumi_PU[0]=onlineLumiPerLSMerged[key]['PrimaryLumi']*xsec_mb/nBX[0]/f_LHC
            pixel_xsec[0]=nCluster[0]/BestLumi_integrated[0]*math.pow(2,18)*nBX[0]
            goodVertices_xsec[0]=goodVertices[0]/BestLumi_integrated[0]*math.pow(2,18)*nBX[0]
            goodVertices_eff[0]=goodVertices_xsec[0]/xsec_mb
            #print key,pixel_xsec[0],goodVertices_xsec[0],goodVertices_eff[0]
            for layer in range(0,5):
                pixel_xsec_layers[layer]=nPCPerLayer[layer]/BestLumi_integrated[0]*math.pow(2,18)*nBX[0]


        if args.isBatch is True:
            if hasCMSData[0] and hasBrilData[0]: 
                newtree.Fill()
        else:        
            newtree.Fill()

    except:
        print "I've failed me for the last time",key

newfile.Write()
newfile.Close()

