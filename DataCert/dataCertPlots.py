import ROOT
import sys
import math
import argparse


scale=1
def ReStyleHistogram(hist,nRows=3):
    hist.GetXaxis().SetTitleSize(0.15*nRows/5)
    hist.GetXaxis().SetTitleOffset(-0.4)
    #hist.GetXaxis().SetNdivisions(1009)
    hist.SetLabelSize(0.14*nRows/5)
    hist.GetYaxis().SetTitleSize(0.12*nRows/5)
    hist.GetYaxis().SetTitleOffset(0.4)
    hist.SetMinimum(0.00001)
    hist.SetLineWidth(scale)


def GetMaximum(histList,scale=1.0):

    listMax=0
    for hist in histList:
        listMax=max(listMax,hist.GetMaximum())

    return listMax*scale



parser = argparse.ArgumentParser(description='Make data certifcation plots')
parser.add_argument('-c', '--certfile', type=str, default="", help='The data certfication tree')
parser.add_argument('-r', '--runlist', type=str, default="", help="Minimum fill number")
parser.add_argument('-a', '--autogen', action='store_true', default=False, help="Auto generator list of runs from file")
parser.add_argument('-b', '--batch',   action='store_true', default=False, help="Batch mode (doesn't make GUI TCanvases)")

args = parser.parse_args()

if args.batch is True:
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    scale=4


filename=args.certfile
tfile=ROOT.TFile(filename)
tree=tfile.Get("certtree")

runsToCheck=[]
missingRuns=[]


if args.autogen:
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("run",1)
    nentries=tree.GetEntries()
    for ient in range(nentries):
        tree.GetEntry(ient)
        if tree.run not in runsToCheck:
            runsToCheck.append(int(tree.run))
            missingRuns.append(int(tree.run))
        
else:
    for run in args.runlist.split(","):
        runsToCheck.append(int(run))
        missingRuns.append(int(run))

runsToCheck.sort()
missingRuns.sort()
print runsToCheck
#246908,246919,246920,246923,246926,246930,246936,246951,246960,247068,247070,247073,247078,247079,247081,247252,247253,247262,247267,247377,247381

tree.SetBranchStatus("*",0)
tree.SetBranchStatus("run",1)
tree.SetBranchStatus("LS",1)
tree.SetBranchStatus("hasBrilData",1)
tree.SetBranchStatus("hasCMSData",1)
tree.SetBranchStatus("nBX",1)

onlyBril=[]
onlyCMS=[]
bothSets=[]

runLSMax={}

nentries=tree.GetEntries()
for ient in range(nentries):
    tree.GetEntry(ient)
    if tree.run in missingRuns:
        missingRuns.remove(tree.run)
    if not runLSMax.has_key(tree.run):
        runLSMax[tree.run]=tree.LS
    elif runLSMax[tree.run]<tree.LS:
        runLSMax[tree.run]=tree.LS

    if tree.hasBrilData and tree.hasCMSData:
        bothSets.append(tree.run)
    elif tree.hasBrilData:
        onlyBril.append(tree.run)
    elif tree.hasCMSData:
        onlyCMS.append(tree.run)

print "missingRuns runs: ",missingRuns
print "Not both CMS and Bril: ",list(set(runsToCheck)-set(bothSets))


tree.SetBranchStatus("*",1)
histpix={}
histpix_HF = {}
histpix_BCMF = {}
histpix_PLT = {}
histPCLumiB3p8={}
histbest={}
histHFLumi={}
histBCMFLumi={}
histPLTLumi={}
histlayers={}
PCClayers={}
histPU={}

bestHF={}
bestBCM1f={}
bestPLT={}

#yLabelPix="PCC/BestLumi*2^18*N_{BX}"
yLabelPix="Pixel Cluster xsec (ub)"

for ient in range(nentries):
    tree.GetEntry(ient)
    if tree.hasCMSData:
        for layer in range(0,5):
            layerkey=str(tree.run)+"_PCClayer"+str(layer+1)
            if not PCClayers.has_key(layerkey):
                PCClayers[layerkey]=ROOT.TH1F(str(tree.run)+"_PCClayer"+str(layer+1),";PCC  ;"+yLabelPix,runLSMax[tree.run],0,runLSMax[tree.run])
                ReStyleHistogram(PCClayers[layerkey],3)
            PCClayers[str(tree.run)+"_PCClayer"+str(layer+1)].Fill(tree.LS,tree.nPCPerLayer[layer]/tree.nCluster)


    if tree.run in bothSets:
        if not histpix.has_key(tree.run):
            histpix[tree.run]=ROOT.TH1F(str(tree.run)+"pix",";Luminosity Section  ;"+yLabelPix,runLSMax[tree.run],0,runLSMax[tree.run])
            ReStyleHistogram(histpix[tree.run],4)

            histpix_HF[tree.run]=ROOT.TH1F(str(tree.run)+"pixHF", ";Luminosity Section  ;"+yLabelPix, runLSMax[tree.run],0,runLSMax[tree.run])
            ReStyleHistogram(histpix_HF[tree.run],4)
            histpix_BCMF[tree.run]=ROOT.TH1F(str(tree.run)+"pixBCMF", ";Luminosity Section  ;"+yLabelPix, runLSMax[tree.run],0,runLSMax[tree.run])
            ReStyleHistogram(histpix_BCMF[tree.run],4)
            histpix_PLT[tree.run]=ROOT.TH1F(str(tree.run)+"pixPLT", ";Luminosity Section  ;"+yLabelPix, runLSMax[tree.run],0,runLSMax[tree.run])
            ReStyleHistogram(histpix_PLT[tree.run],4)

            for layer in range(0,5):
                layerkey=str(tree.run)+"_layer"+str(layer+1)
                histlayers[layerkey]=ROOT.TH1F(str(tree.run)+"_layer"+str(layer+1),";Luminosity Section  ;"+yLabelPix,runLSMax[tree.run],0,runLSMax[tree.run])
                ReStyleHistogram(histlayers[layerkey],3)

        histpix[tree.run].Fill(tree.LS,tree.PC_xsec)
        if (tree.HFLumi != 0):
            histpix_HF[tree.run].Fill(tree.LS,tree.PC_xsec*tree.BestLumi/tree.HFLumi)

        if (tree.PLTLumi != 0):
            histpix_PLT[tree.run].Fill(tree.LS,tree.PC_xsec*tree.BestLumi/tree.PLTLumi)

        if (tree.BCMFLumi != 0):
            histpix_BCMF[tree.run].Fill(tree.LS,tree.PC_xsec*tree.BestLumi/tree.BCMFLumi)

        for layer in range(0,5):
            histlayers[str(tree.run)+"_layer"+str(layer+1)].Fill(tree.LS,tree.PC_xsec_layers[layer])

    if tree.hasBrilData:
        key=tree.run
        if not histbest.has_key(key):
            histPCLumiB3p8[key]=ROOT.TH1F(str(tree.run)+"PCLumiB3p8",";Luminosity Section  ;Integrated Luminosity(ub^{-1})",runLSMax[tree.run],0,runLSMax[tree.run])
            histbest[key]=ROOT.TH1F(str(tree.run)+"best",";Luminosity Section  ;Integrated Luminosity(ub^{-1})",runLSMax[tree.run],0,runLSMax[tree.run])
            histHFLumi[key]=ROOT.TH1F(str(tree.run)+"HF",";Luminosity Section  ;Integrated Luminosity(ub^{-1})",runLSMax[tree.run],0,runLSMax[tree.run])
            histBCMFLumi[key]=ROOT.TH1F(str(tree.run)+"BCMF",";Luminosity Section  ;Integrated Luminosity(ub^{-1})",runLSMax[tree.run],0,runLSMax[tree.run])
            histPLTLumi[key]=ROOT.TH1F(str(tree.run)+"PLT",";Luminosity Section  ;Integrated Luminosity(ub^{-1})",runLSMax[tree.run],0,runLSMax[tree.run])
            histPU[key]=ROOT.TH1F(str(tree.run)+"bestPU",";Luminosity Section  ;Pile-up",runLSMax[tree.run],0,runLSMax[tree.run])
            ReStyleHistogram(histbest[key],3)
            ReStyleHistogram(histPCLumiB3p8[key],3)
            ReStyleHistogram(histHFLumi[key],3)
            ReStyleHistogram(histBCMFLumi[key],3)
            ReStyleHistogram(histPLTLumi[key],3)
            ReStyleHistogram(histPU[key],3)
        if tree.BestLumi>0:
            histbest[key].Fill(tree.LS,tree.BestLumi_integrated)
            histHFLumi[key].Fill(tree.LS,tree.HFLumi_integrated)
            histBCMFLumi[key].Fill(tree.LS,tree.BCMFLumi_integrated)
            histPLTLumi[key].Fill(tree.LS,tree.PLTLumi_integrated)
            if tree.hasCMSData:
                histPCLumiB3p8[key].Fill(tree.LS,tree.PC_lumi_integrated_B3p8)
        if tree.BestLumi_PU>0:
            histPU[key].Fill(tree.LS,tree.BestLumi_PU)
        if tree.HFLumi>0 and tree.BCMFLumi>0 and tree.BestLumi>0:
            # FIXME USE ACTUAL BEST LUMI STRING FROM TREE (NOT IN TREE YET)
            if tree.run not in bestHF.keys():
                bestHF[tree.run]=0
                bestBCM1f[tree.run]=0
                bestPLT[tree.run]=0
            
            diffBestHF=math.fabs(tree.HFLumi_integrated-tree.BestLumi_integrated)
            diffBestBCMF=math.fabs(tree.BCMFLumi_integrated-tree.BestLumi_integrated)
            diffBestPLT=math.fabs(tree.PLTLumi_integrated-tree.BestLumi_integrated)
            minLumi=min(diffBestHF,min(diffBestBCMF,diffBestPLT))
            if minLumi==diffBestHF:
                bestHF[tree.run]=bestHF[tree.run]+1
            elif minLumi==diffBestBCMF:
                bestBCM1f[tree.run]=bestBCM1f[tree.run]+1
            elif minLumi==diffBestPLT:
                bestPLT[tree.run]=bestPLT[tree.run]+1


tcan=ROOT.TCanvas("tcan","",1200*scale,700*scale)
padlumis =ROOT.TPad("padlumis", "",0.0,0.0,0.5,1.0)
padpixxsec =ROOT.TPad("padpixxsec","",0.5,0.0,1.0,1.0)

padlumis.Draw()
padpixxsec.Draw()

PC_calib_xsec_B0=7.4e6
PC_calib_xsec_B3p8=8.6e6

for run in runsToCheck:

    padlumis.Divide(1,3)
    padpixxsec.Divide(1,4)
    lineB0=ROOT.TLine(0,PC_calib_xsec_B0,runLSMax[run],PC_calib_xsec_B0)
    lineB0.SetLineColor(634)
    lineB0.SetLineStyle(ROOT.kDashed)
    lineB0.SetLineWidth(2*scale)
    
    lineB3p8=ROOT.TLine(0,PC_calib_xsec_B3p8,runLSMax[run],PC_calib_xsec_B3p8)
    lineB3p8.SetLineColor(418)
    lineB3p8.SetLineStyle(ROOT.kDashed)
    lineB3p8.SetLineWidth(2*scale)

    legPixXSec=ROOT.TLegend(0.8,0.7,0.9,0.9)
    legPixXSec.AddEntry(lineB3p8,"B=3.8","l")
    legPixXSec.AddEntry(lineB0,"B=0","l")


    if run in histpix.keys():
        padpixxsec.cd(1)
        histpix[run].SetMaximum(max(PC_calib_xsec_B3p8,histpix[run].GetMaximum())*1.4)
        label=ROOT.TText(0,histpix[run].GetMaximum()*0.88,"   Pixel Cluster Cross Section - Run="+str(run))
        label.SetTextSize(.1)
        histpix[run].Draw("hist")
        label.Draw("same")
        lineB0.Draw("same")
        lineB3p8.Draw("same")
        legPixXSec.Draw("same")
        padpixxsec.Update()

        padpixxsec.cd(2)
        histpix_HF[run].SetMaximum(max(PC_calib_xsec_B3p8,histpix_HF[run].GetMaximum())*1.4)
        label3=ROOT.TText(0,histpix_HF[run].GetMaximum()*0.88,"   Pixel Cluster Cross Section HF - Run="+str(run))
        label3.SetTextSize(.1)
        histpix_HF[run].Draw("hist")
        label3.Draw("same")
        lineB0.Draw("same")
        lineB3p8.Draw("same")
        legPixXSec.Draw("same")
        padpixxsec.Update()

        padpixxsec.cd(3)
        histpix_BCMF[run].SetMaximum(max(PC_calib_xsec_B3p8,histpix_BCMF[run].GetMaximum())*1.4)
        label4=ROOT.TText(0,histpix_BCMF[run].GetMaximum()*0.88,"   Pixel Cluster Cross Section BCM1f - Run="+str(run))
        label4.SetTextSize(.1)
        histpix_BCMF[run].Draw("hist")
        label4.Draw("same")
        lineB0.Draw("same")
        lineB3p8.Draw("same")
        legPixXSec.Draw("same")
        padpixxsec.Update()

        padpixxsec.cd(4)
        histpix_PLT[run].SetMaximum(max(PC_calib_xsec_B3p8,histpix_PLT[run].GetMaximum())*1.4)
        label5=ROOT.TText(0,histpix_PLT[run].GetMaximum()*0.88,"   Pixel Cluster Cross Section PLT - Run="+str(run))
        label5.SetTextSize(.1)
        histpix_PLT[run].Draw("hist")
        label5.Draw("same")
        lineB0.Draw("same")
        lineB3p8.Draw("same")
        legPixXSec.Draw("same")
        padpixxsec.Update()

    if run in histbest.keys():
        padlumis.cd(1)
        maxHist=GetMaximum([histbest[run],histHFLumi[run],histBCMFLumi[run],histPLTLumi[run],histPCLumiB3p8[run]],1.1)

        if maxHist>2*histbest[run].GetMaximum():
            print "There is a serious outlier; setting max to 1.5*bestmax."
            maxHist=histbest[run].GetMaximum()*1.5

        histbest[run].SetLineColor(ROOT.kBlack)
        histbest[run].SetLineWidth(2*scale)
        histbest[run].SetMaximum(maxHist)
        histbest[run].Draw("hist")
        print "intL for best in run",run,"is",histbest[run].Integral()
        histHFLumi[run].SetLineColor(633)
        histHFLumi[run].Draw("histsame")
        histBCMFLumi[run].SetLineColor(417)
        histBCMFLumi[run].Draw("histsame")
        histPLTLumi[run].SetLineColor(601)
        histPLTLumi[run].Draw("histsame")
        histPCLumiB3p8[run].SetLineColor(802)
        histPCLumiB3p8[run].Draw("histsame")
        
        leg=ROOT.TLegend(0.1,0.1,0.7,0.4)
        tot=float(bestHF[run]+bestBCM1f[run]+bestPLT[run])
        leg.AddEntry(histbest[run],"Best Lumi","l")
        leg.AddEntry(histHFLumi[run],"HF: "+"{0:.1f}".format((bestHF[run]/tot)*100)+"%","l")
        leg.AddEntry(histBCMFLumi[run],"BCM1f: "+"{0:.1f}".format((bestBCM1f[run]/tot)*100)+"%","l")
        leg.AddEntry(histPLTLumi[run],"PLT: "+"{0:.1f}".format((bestPLT[run]/tot)*100)+"%","l")
        leg.AddEntry(histPCLumiB3p8[run],"PCC - B=3.8","l")
        leg.SetFillStyle(0)
        leg.SetBorderSize(0)
        leg.Draw("same")
        padlumis.Update()

        padlumis.cd(2)
        PCLumiOBest=histPCLumiB3p8[run].Clone("best_o_PCLumi")
        PCLumiOBest.Divide(histbest[run])
        PCLumiOBest.SetMaximum(2.0)
        PCLumiOBest.SetTitle(";Luminosity Section  ;Best/PCLumi")
        PCLumiOBest.SetLineColor(802)

        bestOHFLumi=histbest[run].Clone("best_o_HFLumi")
        bestOHFLumi.Divide(histHFLumi[run])
        bestOHFLumi.SetMaximum(2.0)
        bestOHFLumi.SetTitle(";Luminosity Section  ;Best/HFLumi")

        hfOverBcm1f=histHFLumi[run].Clone("HFLumi_o_BCM1f")
        hfOverBcm1f.Divide(histBCMFLumi[run])
        hfOverBcm1f.SetMaximum(2.0)
        hfOverBcm1f.SetTitle(";Luminosity Section  ;HFLumi/BCM1fLumi")

        pltOverHF=histPLTLumi[run].Clone("PLTLumi_o_HFLumi")
        pltOverHF.Divide(histHFLumi[run])
        pltOverHF.SetMaximum(2.0)
        pltOverHF.SetTitle(";Luminosity Section  ;PLTLumi/HFLumi")

        leg2=ROOT.TLegend(0.1,0.7,0.5,0.9)
        leg2.AddEntry(PCLumiOBest,"PCLumi/Best - Run="+str(run),"l")
        leg2.AddEntry(bestOHFLumi,"Best/HF","l")
        leg2.AddEntry(hfOverBcm1f,"HF/BCM1f","l")
        leg2.AddEntry(pltOverHF,"PLT/HF","l")
        PCLumiOBest.Draw("hist")
        bestOHFLumi.Draw("histsame")
        hfOverBcm1f.Draw("histsame")
        pltOverHF.Draw("histsame")
        leg2.Draw("sames")
        padlumis.Update()

        
        if run in bothSets:
            padlumis.cd(3)
            histPU[run].Draw("hist")
            padlumis.Update()

    tcan.Update()
    tcan.SaveAs(str(run)+".png")

    #raw_input()
    padlumis.Clear()
    padpixxsec.Clear()
    tcan.Update()

    if run in bothSets:
        layertexts={}
        lines={}
        canlayers=ROOT.TCanvas("canlayers","",1200,700)
        canlayers.Divide(2,3)

        canlayers.cd(1)
        ReStyleHistogram(histpix[run],3)
        histpix[run].Draw("hist")
        label.Draw("same")
        lineB0.Draw("same")
        lineB3p8.Draw("same")
        for layer in range(5):
            lines[layer]=ROOT.TF1("pol1_"+str(layer+1),"pol1",70,175)
            canlayers.cd(layer+2)
            key=str(run)+"_layer"+str(layer+1)
            layertexts[layer]=ROOT.TText(0,histlayers[key].GetMaximum()*1.05,"    Pixel Cluster Cross Section - Layer="+str(layer+1))
            layertexts[layer].SetTextSize(.1)
            histlayers[key].SetMaximum(histlayers[key].GetMaximum()*1.2)
            #histlayers[key].Fit(lines[layer],"","",75,175)
            histlayers[key].Draw("hist")
            #if run==246908:
            #    lines[layer].Draw("same")
            layertexts[layer].Draw("same")
        canlayers.Update()
        canlayers.SaveAs(str(run)+"_layers.png")


    if run in bothSets or run in onlyCMS:
        layertexts={}
        lines={}
        stability=ROOT.TCanvas("stability","",1200,700)

        for layer in range(5):
            key=str(run)+"_PCClayer"+str(layer+1)
            #histlayers[key].Fit(lines[layer],"","",75,175)
            if layer==0:
                PCClayers[key].Draw("hist")
            else:
                PCClayers[key].Draw("histsame")
        stability.Update()
        stability.SaveAs(str(run)+"_stability.png")



