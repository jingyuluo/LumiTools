
import sys, os
from math import exp
import ROOT
from ROOT import TFile
from ROOT import gStyle

def findRange( hist, cut):
    gaplist=[]
    for i in range(1,3600):
        if hist.GetBinContent(i)<cut:
            gaplist.append(i)
    return gaplist

gStyle.SetOptStat(0)
filename=sys.argv[1]
run=sys.argv[2]
label=sys.argv[3]
tfile=ROOT.TFile(filename)
tree=tfile.Get("certtree")

tree.SetBranchStatus("*",0)
tree.SetBranchStatus("run*", 1)
tree.SetBranchStatus("fill*", 1)
tree.SetBranchStatus("LS*", 1)
tree.SetBranchStatus("PC_lumi_B3p8_perBX*", 1)
tree.SetBranchStatus("PCBXid*",1)


histnoise=ROOT.TH1F("histnoise","",3600,0,3600)
histfull=ROOT.TH1F("histfull","",3600,0,3600)
normfull=ROOT.TH1F("normfull","",3600,0,3600)
corrtemp=ROOT.TH1F("corrtemp","",3600,0,3600)
corrfill=ROOT.TH1F("corrfill","",3600,0,3600)

a=0.075#0.073827#0.078625#0.076825
b=0.00078#0.0007891#0.00080518#0.00080518#0.0008125#0.00090625#0.00047
c=0.012#0.011867#0.01261#0.0098

for i in range(2,3600):
    corrtemp.SetBinContent(i,b*exp(-(i-2)*c))
corrtemp.GetXaxis().SetRangeUser(0,100)

nentries=tree.GetEntries()

for iev in range(nentries):
    tree.GetEntry(iev)
    if tree.LS<3700:
        for ibx in range(tree.nBX):
            histfull.Fill(tree.PCBXid[ibx], tree.PC_lumi_B3p8_perBX[ibx])
            normfull.Fill(tree.PCBXid[ibx], 1)

histfull.Divide(normfull)
histsig=histfull.Clone()
histfull.SetTitle("Random Triggers in Run "+run+";BX;Average PCC SBIL Hz/ub")
histsig.SetTitle("Random Triggers in Run "+run+", after correction;BX; Average PCC SBIL Hz/ub")
histfull.SetLineColor(416)
histfull.GetXaxis().SetRangeUser(0,2000)
histfull.GetYaxis().SetRangeUser(-0.02,0.3)

can=ROOT.TCanvas("can_corr_temp","",800,800)
canfull=ROOT.TCanvas("can_full","",800,800)
cansig=ROOT.TCanvas("can_sig","",800,800)
canfill=ROOT.TCanvas("can_fill","",800,800)
canratio=ROOT.TCanvas("ratio_fill","",800,800)

can.cd()
corrtemp.SetTitle("Correction Function Template")
corrtemp.Draw("HIST")
can.SaveAs("SBIL_randoms_"+run+"_corrtemp_"+label+".png")

canfull.cd()
histfull.Draw()
canfull.SaveAs("full_SBIL_randoms_"+run+"_full_"+label+".png")


cansig.cd()
noise=0
for l in range(1,36):
    noise=noise+histsig.GetBinContent(l)
noise=noise/35
print("noise: {0}".format(noise))

for m in range(1,3600):
    histsig.SetBinContent(m, histsig.GetBinContent(m)-noise)
    histnoise.SetBinContent(m, noise)
    corrfill.SetBinContent(m, corrfill.GetBinContent(m)+noise)

for i in range(1,3600):
    bin_i = histsig.GetBinContent(i)
    histsig.SetBinContent(i+1, histsig.GetBinContent(i+1)-bin_i*a)
    corrfill.SetBinContent(i+1, corrfill.GetBinContent(i+1)+bin_i*a)

for i in range(1,3600):
    for j in range(i+1,3600):
        bin_i=histsig.GetBinContent(i)
        histsig.SetBinContent(j,histsig.GetBinContent(j)-bin_i*corrtemp.GetBinContent(j-i))
        corrfill.SetBinContent(j,corrfill.GetBinContent(j)+bin_i*corrtemp.GetBinContent(j-i))

histsig.GetXaxis().SetRangeUser(350,500)
histsig.GetYaxis().SetRangeUser(-0.03,0.1)
histsig.Draw()
cansig.SaveAs("full_SBIL_randoms_"+run+"_signal"+label+".png")

canfill.cd()
corrfill.SetTitle("The Overall Correction in the Run "+run)
corrfill.Draw()
canfill.SaveAs("full_SBIL_randoms_"+run+"_fill_"+label+".png")

ratiocorr=corrfill.Clone()
ratiocorr.Divide(histfull)

canratio.cd()
ratiocorr.SetTitle("The Ratio of Overall Correction in the Run "+run)
ratiocorr.GetXaxis().SetTitle("BX")
ratiocorr.GetYaxis().SetTitle("Ratio")
ratiocorr.Draw()
canratio.SaveAs("full_SBIL_randoms_"+run+"_ratio_"+label+".png")

ratio_gap=ROOT.TH1F("ratio_gap", "",100,0,2.8)
checklist=findRange(histfull, 0.2)
for l in checklist:
    ratio_gap.Fill(ratiocorr.GetBinContent(l))

ratio_noise=histnoise.Clone()
ratio_noise.Divide(corrfill)

newfile=TFile("Overall_Correction_"+run+"_"+label+".root", "recreate")
newfile.WriteTObject(histfull,  "Before_Corr_"+run)
newfile.WriteTObject(histsig, "After_Corr_"+run)
newfile.WriteTObject(histnoise, "Noise_"+run)
newfile.WriteTObject(corrfill, "Overall_Correction_"+run)
newfile.WriteTObject(ratiocorr, "Ratio_Correction_"+run)
newfile.WriteTObject(ratio_gap, "Ratio_Nonlumi_"+run)
newfile.WriteTObject(ratio_noise, "Ratio_Noise_"+run)

