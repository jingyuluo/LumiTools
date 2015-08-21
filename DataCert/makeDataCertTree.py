import ROOT
import sys,os
import numpy
import array
import math
import argparse
import pickle
import time

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--pccfile', type=str, default="", help='The pccfile to input (pixel clusters and vertices)')
parser.add_argument('--pkldir', type=str, default="brildata", help='bril data is here')
parser.add_argument('--nobril', type=bool, default=False, help="Don\'t process bril data (default false)")
parser.add_argument('-l','--label',type=str,default="",  help="Label for output file")
parser.add_argument('--minfill', type=int, default=3818, help="Minimum fill number")
parser.add_argument('--minrun',  type=int, default=230000,help="Minimum run number")
parser.add_argument('-b', '--isBatch', default=False, action="store_true", help="Maximum fill number")
parser.add_argument('--eventBased', default=False, action="store_true", help="PCC ntuples are event based (default false--typically LS-based)")

args = parser.parse_args()

if args.nobril:
    args.pkldir=""


f_LHC = 11245.6
t_LS=math.pow(2,18)/f_LHC
xsec_ub=80000. #microbarn


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



startTime=time.time()
onlineLumi={} #(fill,run,LS)

if not args.nobril:
    files=os.listdir(args.pkldir)
    files.sort()
    for fileName in files:
        if fileName.find(".pkl") !=-1:
            try:
                filePath=args.pkldir+"/"+fileName
                pklFile=open(filePath,'rb')
                data=pickle.load(pklFile)
                onlineLumi.update(data)
                pklFile.close()
            except:
                print "Problem with pickle file",fileName
        else:
            continue

        print fileName," new total LSs: ",len(onlineLumi)      

endTime=time.time()
print "Duration: ",endTime-startTime


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
        tree.GetEntry(iev)
        if iev%1000==0:
            print "iev,",iev
            print "(tree.run,tree.LS)",tree.run,tree.LS
            print "len(tree.nPixelClusters)",len(tree.nPixelClusters)
            print "len(tree.layers)",len(tree.layers)
        if len(tree.nPixelClusters)==0:
            continue
        
        LSKey=(tree.run,tree.LS)
        
        if LSKey not in vertexCounts:
            vertexCounts[LSKey]=[]
    
        for ibx,nGoodVtx in tree.nGoodVtx:
            vertexCounts[LSKey].append([nGoodVtx,tree.BXNo[ibx]])
       
       
        # 0 is the total count for layers 2-5
        # 1-5 is the count for layre 1-5
        # 6 is the count for per BX

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
        bxid=-1
        for item in tree.nPixelClusters:
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
        counter=counter+1
  
        if not args.eventBased: #divide by the sum of events
            pixelCount[(tree.run,tree.LS)][0]=pixelCount[(tree.run,tree.LS)][0]/float(tree.eventCounter)
            for layer in range(1,6):
                pixelCount[(tree.run,tree.LS)][layer]=pixelCount[(tree.run,tree.LS)][layer]/float(tree.eventCounter)
            for bxid in bxids:
                pixelCount[(tree.run,tree.LS)][6][bxid]=pixelCount[(tree.run,tree.LS)][6][bxid]/float(tree.BXNo[bxid])

        pixelCounts[(tree.run,tree.LS)][0].append([pixelCount[(tree.run,tree.LS)][0],1])
        for layer in range(1,6):
            pixelCounts[(tree.run,tree.LS)][layer].append([pixelCount[(tree.run,tree.LS)][layer],1])
        for bxid in bxids:
            if not pixelCounts[(tree.run,tree.LS)][6].has_key(bxid):
                pixelCounts[(tree.run,tree.LS)][6][bxid]=[]
            pixelCounts[(tree.run,tree.LS)][6][bxid].append([pixelCount[(tree.run,tree.LS)][6][bxid],1])


cmskeys=pixelCounts.keys()
brilkeys=onlineLumi.keys()
LSKeys=list(set(cmskeys+brilkeys))

LSKeys.sort()

if LSKeys[0][0]==123456:
    newfilename="dataCertification_"+str(LSKeys[1][0])+"_"+str(LSKeys[-1][0])+"_"+args.label+".root"
else:
    newfilename="dataCertification_"+str(LSKeys[0][0])+"_"+str(LSKeys[-1][0])+"_"+args.label+".root"
    
newfile=ROOT.TFile(newfilename,"recreate")
newtree=ROOT.TTree("certtree","validationtree")

fill= array.array( 'l', [ 0 ] )
run = array.array( 'l', [ 0 ] )
LS  = array.array( 'l', [ 0 ] )
nBX = array.array( 'l', [ 0 ] )
nBXHF = array.array( 'l', [ 0 ] )
nBXBCMF = array.array( 'l', [ 0 ] )
nBXPLT = array.array( 'l', [ 0 ] )

nCluster    = array.array( 'd', [ 0 ] )
nClusterError    = array.array( 'd', [ 0 ] )
nPCPerLayer = array.array( 'd', 5*[ 0 ] )

HFLumi    = array.array( 'd', [ 0 ] )
BCMFLumi  = array.array( 'd', [ 0 ] )
PLTLumi   = array.array( 'd', [ 0 ] )
BestLumi  = array.array( 'd', [ 0 ] )
BestLumi_PU  = array.array( 'd', [ 0 ] )

HFLumi_perBX = array.array( 'd', 3600*[ 0 ] )
BCMFLumi_perBX = array.array( 'd', 3600*[ 0 ] )
PLTLumi_perBX = array.array('d', 3600*[ 0 ] )

HFBXid = array.array('l', 3600*[ 0 ] )
BCMFBXid = array.array('l', 3600*[ 0 ] )
PLTBXid = array.array('l', 3600*[ 0 ] )

HFLumi_integrated    = array.array( 'd', [ 0 ] )
BCMFLumi_integrated  = array.array( 'd', [ 0 ] )
PLTLumi_integrated   = array.array( 'd', [ 0 ] )
BestLumi_integrated  = array.array( 'd', [ 0 ] )

hasBrilData = array.array('b', [0])
hasCMSData  = array.array('b', [0])

PC_lumi_B0      = array.array( 'd', [ 0 ] )
PC_lumi_B3p8    = array.array( 'd', [ 0 ] )
PC_lumi_integrated_B0      = array.array( 'd', [ 0 ] )
PC_lumi_integrated_B3p8    = array.array( 'd', [ 0 ] )
PC_lumi_integrated_error_B0      = array.array( 'd', [ 0 ] )
PC_lumi_integrated_error_B3p8    = array.array( 'd', [ 0 ] )

PC_lumi_B0_perBX  = array.array('d', 3600*[ 0 ])
PC_lumi_B3p8_perBX = array.array('d', 3600*[ 0 ])

PC_xsec         = array.array( 'd', [ 0 ] )
PC_xsec_layers  = array.array( 'd', 5*[ 0 ] )

nPCPerBXid  = array.array( 'd', 3600*[ 0 ] )
BXid        = array.array( 'd', 3600*[ 0 ] )

goodVertices  = array.array( 'd', [ 0 ] )
goodVertices_xsec  = array.array( 'd', [ 0 ] )
goodVertices_eff  = array.array( 'd', [ 0 ] )
# 0 - average vertices; 1 - xsec; 2 - vertex efficiency


newtree.Branch("fill",fill,"fill/I")
newtree.Branch("run",run,"run/I")
newtree.Branch("LS",LS,"LS/I")
newtree.Branch("nBX",nBX,"nBX/I")
newtree.Branch("nBXHF", nBXHF, "nBXHF/I")
newtree.Branch("nBXBCMF", nBXBCMF, "nBXBCMF/I")
newtree.Branch("nBXPLT", nBXPLT, "nBXPLT/I")

newtree.Branch("nCluster",nCluster,"nCluster/D")
newtree.Branch("nClusterError",nClusterError,"nClusterError/D")
newtree.Branch("nPCPerLayer",nPCPerLayer,"nPCPerLayer[5]/D")

newtree.Branch("PC_lumi_B0",PC_lumi_B0,"PC_lumi_B0/D")
newtree.Branch("PC_lumi_B3p8",PC_lumi_B3p8,"PC_lumi_B3p8/D")
newtree.Branch("PC_lumi_integrated_B0",PC_lumi_integrated_B0,"PC_lumi_integrated_B0/D")
newtree.Branch("PC_lumi_integrated_B3p8",PC_lumi_integrated_B3p8,"PC_lumi_integrated_B3p8/D")
newtree.Branch("PC_lumi_integrated_error_B0",PC_lumi_integrated_error_B0,"PC_lumi_integrated_error_B0/D")
newtree.Branch("PC_lumi_integrated_error_B3p8",PC_lumi_integrated_error_B3p8,"PC_lumi_integrated_error_B3p8/D")

newtree.Branch("PC_lumi_B0_perBX", PC_lumi_B0_perBX, "PC_lumi_B0_perBX[nBX]/D")
newtree.Branch("PC_lumi_B3p8_perBX", PC_lumi_B3p8_perBX, "PC_lumi_B3p8_perBX[nBX]/D")

newtree.Branch("PC_xsec",PC_xsec,"PC_xsec/D")
newtree.Branch("PC_xsec_layers",PC_xsec_layers,"PC_xsec_layers[5]/D")

newtree.Branch("BXid",BXid,"BXid[nBX]/I")
newtree.Branch("nPCPerBXid",nPCPerBXid,"nPCPerBXid[nBX]/D")

newtree.Branch("BestLumi",BestLumi,"BestLumi/D")
newtree.Branch("HFLumi",HFLumi,"HFLumi/D")
newtree.Branch("BCMFLumi",BCMFLumi,"BCMFLumi/D")
newtree.Branch("PLTLumi",PLTLumi,"PLTLumi/D")

newtree.Branch("HFLumi_perBX", HFLumi_perBX, "HFLumi_perBX[nBXHF]/D")
newtree.Branch("BCMFLumi_perBX", BCMFLumi_perBX, "BCMFLumi_perBX[nBXBCMF]/D")
newtree.Branch("PLTLumi_perBX", PLTLumi_perBX, "PLTLumi_perBX[nBXPLT]/D")

newtree.Branch("HFBXid", HFBXid, "HFBXid[nBXHF]/I")
newtree.Branch("BCMFBXid", BCMFBXid, "BCMFBXid[nBXBCMF]/I")
newtree.Branch("PLTBXid", PLTBXid, "PLTBXid[nBXPLT]/I")

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


PC_calib_xsec={}
PC_calib_xsec["B0"]=7.4e6
PC_calib_xsec["B3p8"]=8.6e6


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
    PC_xsec[0]=-1

    PC_lumi_B0[0]=-1
    PC_lumi_B3p8[0]=-1
    PC_lumi_integrated_B0[0]=-1
    PC_lumi_integrated_B3p8[0]=-1
    PC_lumi_integrated_error_B0[0]=-1
    PC_lumi_integrated_error_B3p8[0]=-1

    goodVertices[0]=-1
    goodVertices_xsec[0]=-1
    goodVertices_eff[0]=-1

    for layer in range(0,5):
        PC_xsec_layers[layer]=-1
        nPCPerLayer[layer]=-1

    if key in brilkeys:
        try:
            hasBrilData[0]=True
            fill[0]=int(onlineLumi[key]['fill'])
            BestLumi_integrated[0]=float(onlineLumi[key][onlineLumi[key]['best']])
            BestLumi[0]=BestLumi_integrated[0]
            BestLumi_PU[0]=float(onlineLumi[key]['PU_best'])
            if BestLumi[0]>0:
                BestLumi[0]=BestLumi[0]/t_LS
            if onlineLumi[key].has_key('HFOC'):
                HFLumi_integrated[0]=float(onlineLumi[key]['HFOC'])
                HFLumi[0]=HFLumi_integrated[0]
                if HFLumi[0]>0:
                    HFLumi[0]=HFLumi[0]/t_LS
            if onlineLumi[key].has_key('PLT'):
                PLTLumi_integrated[0]=float(onlineLumi[key]['PLT'])
                PLTLumi[0]=PLTLumi_integrated[0]
                if PLTLumi[0]>0:
                    PLTLumi[0]=PLTLumi[0]/t_LS
            if onlineLumi[key].has_key('BCM1F'):
                BCMFLumi_integrated[0]=float(onlineLumi[key]['BCM1F'])
                BCMFLumi[0]=BCMFLumi_integrated[0]
                if BCMFLumi[0]>0:
                    BCMFLumi[0]=BCMFLumi[0]/t_LS

            if onlineLumi[key].has_key('HFOC_BX'):
                nBXHF[0] = len(onlineLumi[key]['HFOC_BX'])
                idxHF=0
                HFbxkeys = onlineLumi[key]['HFOC_BX'].keys()
                HFbxkeys.sort()
                print "HF length", len(HFbxkeys)
   
                for HFbxkey in HFbxkeys :#onlineLumi[key]['HFOC_BX'].keys():
                    HFBXid[idxHF] = int(HFbxkey)
                    HFLumi_perBX[idxHF] = float(onlineLumi[key]['HFOC_BX'][HFbxkey])/t_LS
                    idxHF = idxHF+1

            if onlineLumi[key].has_key('PLT_BX'):
                nBXPLT[0] = len(onlineLumi[key]['PLT_BX'])
                idxPLT=0
                PLTbxkeys = onlineLumi[key]['PLT_BX'].keys()
                PLTbxkeys.sort()
                print len(PLTbxkeys)
                for PLTbxkey in PLTbxkeys :#onlineLumi[key]['HFOC_BX'].keys():
                    PLTBXid[idxPLT] = int(PLTbxkey)
                    PLTLumi_perBX[idxPLT] = float(onlineLumi[key]['PLT_BX'][PLTbxkey])/t_LS
                    idxPLT = idxPLT+1
        
            if onlineLumi[key].has_key('BCM1F_BX'):
                nBXBCMF[0] = len(onlineLumi[key]['BCM1F_BX'])
                idxBCMF=0
                BCMFbxkeys = onlineLumi[key]['BCM1F_BX'].keys()
                BCMFbxkeys.sort()
                print len(BCMFbxkeys)
                for BCMFbxkey in BCMFbxkeys :#onlineLumi[key]['HFOC_BX'].keys():
                    BCMFBXid[idxBCMF] = int(BCMFbxkey)
                    BCMFLumi_perBX[idxBCMF] = float(onlineLumi[key]['BCM1F_BX'][BCMFbxkey])/t_LS
                    idxBCMF = idxBCMF+1
               
            print "Success!"                   
                        
                
        except:
            print "Failed in brilkey",key#,onlineLumi[key]

    if key in cmskeys:
        try:
            hasCMSData[0]=True
            count=0
            mean=AverageWithWeight(vertexCounts[key])
            #print mean
            goodVertices[0]=mean
            nBX[0]=len(tree.BXNo)
            
            for PCCs in pixelCounts[key]:
                if count==0:
                    mean,error=GetMeanAndMeanError(PCCs)
                    nCluster[0]=mean
                    nClusterError[0]=error
                elif count<6:
                    mean,error=GetMeanAndMeanError(PCCs)
                    nPCPerLayer[count-1]=mean
                else:
                    ibx=0
                    for bxid in PCCs:
                        print bxid, ibx
                        mean,error=GetMeanAndMeanError(PCCs[bxid])
                        BXid[ibx]=bxid
                        nPCPerBXid[ibx]=mean
                        totalPCperBX=mean*math.pow(2,18)
                        PC_lumi_B0_perBX[ibx]=totalPCperBX/PC_calib_xsec["B0"]/t_LS
                        PC_lumi_B3p8_perBX[ibx]=totalPCperBX/PC_calib_xsec["B3p8"]/t_LS

                        ibx=ibx+1
                        if ibx>nBX[0]:
                            print "ibx,nBX[0],",ibx,nBX[0],", but WHY?!!!"

                count=count+1 
            
            totalPC=nCluster[0]*math.pow(2,18)*nBX[0]
            totalPCError=nClusterError[0]*math.pow(2,18)*nBX[0]
            
            PC_lumi_B0[0]=totalPC/PC_calib_xsec["B0"]/t_LS
            PC_lumi_B3p8[0]=totalPC/PC_calib_xsec["B3p8"]/t_LS
            PC_lumi_integrated_B0[0]=totalPC/PC_calib_xsec["B0"]
            PC_lumi_integrated_B3p8[0]=totalPC/PC_calib_xsec["B3p8"]
            PC_lumi_integrated_error_B0[0]=totalPCError/PC_calib_xsec["B0"]
            PC_lumi_integrated_error_B3p8[0]=totalPCError/PC_calib_xsec["B3p8"]
            
        except:
            print "Failed in cmskey",key
            
    if hasCMSData[0] and hasBrilData[0]: 
        try:
            PC_xsec[0]=nCluster[0]/BestLumi_integrated[0]*math.pow(2,18)*nBX[0]
            goodVertices_xsec[0]=goodVertices[0]/BestLumi_integrated[0]*math.pow(2,18)*nBX[0]
            goodVertices_eff[0]=goodVertices_xsec[0]/xsec_ub
            #print key,PC_xsec[0],goodVertices_xsec[0],goodVertices_eff[0]
            for layer in range(0,5):
                PC_xsec_layers[layer]=nPCPerLayer[layer]/BestLumi_integrated[0]*math.pow(2,18)*nBX[0]
            if BestLumi_PU[0]==0 and BestLumi[0]>0 and nBX[0]>0:
                BestLumi_PU[0]=BestLumi[0]*xsec_ub/nBX[0]/f_LHC
                
        except:
            print "Failed cms+bril computation",key,onlineLumi[key]

    if args.isBatch is True:
        if hasCMSData[0] and hasBrilData[0]: 
            newtree.Fill()
    else:       
        newtree.Fill()

newfile.Write()
newfile.Close()

