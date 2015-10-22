
import sys, os
from math import exp
import argparse
import subprocess
import ROOT
from ROOT import TFile
from ROOT import gStyle

parser=argparse.ArgumentParser()
parser.add_argument("-p", "--path", help="The path to the PCC ntuple")
parser.add_argument("-r", "--run", type=str, help="The label for run number")
parser.add_argument("-l", "--label", type=str, help="The label for outputs")
parser.add_argument("-a", "--all", default=True, help="Apply both the type1 and type2 correction")
parser.add_argument("--noType1", action='store_true', default=False, help="Only apply the type2 correction")
parser.add_argument("--noType2", action='store_true', default=False, help="Only apply the type1 correction")
parser.add_argument("-u","--useresponse", action='store_true', default=False, help="Use the final response instead of the real activity to calculate the Type2 Correction")

args=parser.parse_args()

def findRange( hist, cut):
    gaplist=[]
    for i in range(1,3600):
        if hist.GetBinContent(i)<cut:
            gaplist.append(i)
    return gaplist

gStyle.SetOptStat(0)
#filename=sys.argv[1]
#run=sys.argv[2]
#label=sys.argv[3]

filename=args.path
run=args.run
runnum=int(run)
label=args.label

tfile=ROOT.TFile(filename)
tree=tfile.Get("certtree")

tree.SetBranchStatus("*",0)
tree.SetBranchStatus("run*", 1)
tree.SetBranchStatus("fill*", 1)
tree.SetBranchStatus("LS*", 1)
tree.SetBranchStatus("PC_lumi_B3p8_perBX*", 1)
tree.SetBranchStatus("PCBXid*",1)


histpar_a=ROOT.TH1F("histpar_a","",10, 0, 10)
histpar_b=ROOT.TH1F("histpar_b","",10, 0, 10)
histpar_c=ROOT.TH1F("histpar_c","",10, 0, 10)

histnoise=ROOT.TH1F("histnoise","",3600,0,3600)
histfull=ROOT.TH1F("histfull","",3600,0,3600)
normfull=ROOT.TH1F("normfull","",3600,0,3600)
corrtemp=ROOT.TH1F("corrtemp","",3600,0,3600)
corrfill=ROOT.TH1F("corrfill","",3600,0,3600)

a=0.066#0.06636#0.073827#0.078625#0.076825
b=0.00078#0.00083#0.00078#0.00067#0.00083#0.000811#0.0007891#0.00080518#0.00080518#0.0008125#0.00090625#0.00047
c=0.012#0.0126#0.012#0.017#0.0126#0.012282#0.011867#0.01261#0.0098

if args.noType1:
    a=0
if args.noType2:
    b=0


for ia in range(10):
    histpar_a.SetBinContent(ia,a)
for ib in range(10):
    histpar_b.SetBinContent(ib,b)
for ic in range(10):
    histpar_c.SetBinContent(ic,c)


corrtemp.SetBinContent(1,a+b*exp(c))
for i in range(2,3600):
    corrtemp.SetBinContent(i,b*exp(-(i-2)*c))
corrtemp.GetXaxis().SetRangeUser(0,100)

nentries=tree.GetEntries()

for iev in range(nentries):
    tree.GetEntry(iev)
    if tree.LS<3700 and tree.run==runnum:
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
    for j in range(i+1,3600):
        binsig_i=histsig.GetBinContent(i)
        binfull_i=histfull.GetBinContent(i)
        if not args.useresponse:
            histsig.SetBinContent(j,histsig.GetBinContent(j)-binsig_i*corrtemp.GetBinContent(j-i))
            corrfill.SetBinContent(j, corrfill.GetBinContent(j)+binsig_i*corrtemp.GetBinContent(j-i))
        else:
            histsig.SetBinContent(j,histsig.GetBinContent(j)-binfull_i*corrtemp.GetBinContent(j-i))
            corrfill.SetBinContent(j,corrfill.GetBinContent(j)+binfull_i*corrtemp.GetBinContent(j-i))

histsig.GetXaxis().SetRangeUser(0,2000)
histsig.GetYaxis().SetRangeUser(-0.03,3.0)
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
newfile.WriteTObject(histpar_a, "Parameter_a")
newfile.WriteTObject(histpar_b, "Parameter_b")
newfile.WriteTObject(histpar_c, "Parameter_c")

newfile.WriteTObject(histfull,  "Before_Corr_"+run)
newfile.WriteTObject(histsig, "After_Corr_"+run)
newfile.WriteTObject(histnoise, "Noise_"+run)
newfile.WriteTObject(corrfill, "Overall_Correction_"+run)
newfile.WriteTObject(ratiocorr, "Ratio_Correction_"+run)
newfile.WriteTObject(ratio_gap, "Ratio_Nonlumi_"+run)
newfile.WriteTObject(ratio_noise, "Ratio_Noise_"+run)
