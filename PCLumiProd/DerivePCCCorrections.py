import sys, os
from math import exp
import argparse
import subprocess

import ROOT

parser=argparse.ArgumentParser()
#parser.add_argument("-h", "--help", help="Display this message.")
parser.add_argument("-f", "--file", default="", help="The path to a cert tree.")
parser.add_argument("-d", "--dir",  default="", help="The path to a directory of cert trees.")
parser.add_argument("-r", "--runs", default="", help="Comma separated list of runs.")
parser.add_argument("--auto", default=False, action="store_true", help="Determine the runs from the certtree")
parser.add_argument("-l", "--label", default="", help="The label for outputs")
parser.add_argument("-a", "--all", default=True, help="Apply both the type1 and type2 correction")
parser.add_argument("--noType1", action='store_true', default=False, help="Only apply the type2 correction")
parser.add_argument("--noType2", action='store_true', default=False, help="Only apply the type1 correction")
parser.add_argument("-u","--useresponse", action='store_true', default=False, help="Use the final response instead of the real activity to calculate the Type2 Correction")
parser.add_argument('-b', '--batch',   action='store_true', default=False, help="Batch mode (doesn't make GUI TCanvases)")
parser.add_argument('-p', '--par', default="0.066, 0.00078, 0.012", help="The parameters for type1 and type2 correction")

args=parser.parse_args()

def findRange( hist, cut):
    gaplist=[]
    for i in range(1,3600):
        if hist.GetBinContent(i)<cut:
            gaplist.append(i)
    return gaplist

ROOT.gStyle.SetOptStat(0)
if args.batch is True:
    ROOT.gROOT.SetBatch(ROOT.kTRUE)

a=0.0#0.06636#0.073827#0.078625#0.076825
b=0.0#0.00083#0.00078#0.00067#0.00083#0.000811#0.0007891#0.00080518#0.00080518#0.0008125#0.00090625#0.00047
c=0.0#0.0126#0.012#0.017#0.0126#0.012282#0.011867#0.01261#0.0098

if args.par!="":
    pars=args.par.split(",")
    if len(pars) >= 3:
        a=float(pars[0])
        b=float(pars[1])
        c=float(pars[2])

if args.noType1:
    a=0
if args.noType2:
    b=0

# Print out the paramters for correction:
print "parameter a: ", a
print "parameter b: ", b
print "parameter c: ", c


histpar_a=ROOT.TH1F("histpar_a","",10, 0, 10)
histpar_b=ROOT.TH1F("histpar_b","",10, 0, 10)
histpar_c=ROOT.TH1F("histpar_c","",10, 0, 10)

for ia in range(10):
    histpar_a.SetBinContent(ia,a)
for ib in range(10):
    histpar_b.SetBinContent(ib,b)
for ic in range(10):
    histpar_c.SetBinContent(ic,c)

corrTemplate=ROOT.TH1F("corrTemplate","",3600,0,3600)

#corrTemplate.SetBinContent(1,a+b*exp(c))
for i in range(1,3600):
    corrTemplate.SetBinContent(i,b*exp(-(i-2)*c))
corrTemplate.GetXaxis().SetRangeUser(0,100)

filename=args.file
if args.runs!="":
    runs=args.runs.split(",")
else:
    runs=[]
label=args.label

newfile=ROOT.TFile("Overall_Correction_"+label+".root", "recreate")
newfile.WriteTObject(histpar_a, "Parameter_a")
newfile.WriteTObject(histpar_b, "Parameter_b")
newfile.WriteTObject(histpar_c, "Parameter_c")

tfile=ROOT.TFile(filename)
tree=tfile.Get("certtree")

tree.SetBranchStatus("*",0)
tree.SetBranchStatus("run*", 1)

if args.auto:
    nentries=tree.GetEntries()

    for iev in range(nentries):
        tree.GetEntry(iev)
        if str(tree.run) not in runs:
            print "Adding",tree.run
            runs.append(str(tree.run))

    print "auto", runs
    runs.sort()

tree.SetBranchStatus("fill*", 1)
tree.SetBranchStatus("LS*", 1)
tree.SetBranchStatus("PC_lumi_B3p8_perBX*", 1)
tree.SetBranchStatus("PCBXid*",1)

for run in runs:
    runnum=int(run)

    histnoise=ROOT.TH1F("histnoise","",3600,0,3600)
    histfull=ROOT.TH1F("histfull","",3600,0,3600)
    normfull=ROOT.TH1F("normfull","",3600,0,3600)
    corrfill=ROOT.TH1F("corrfill","",3600,0,3600)

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
    corrTemplate.SetTitle("Correction Function Template")
    corrTemplate.Draw("HIST")
    can.SaveAs("SBIL_randoms_"+run+"_corrTemplate_"+label+".png")

    canfull.cd()
    histfull.Draw()
    canfull.SaveAs("full_SBIL_randoms_"+run+"_full_"+label+".png")


    cansig.cd()
    noise=0
    # FIXME
    # 36/35 are magic numbers
    # they may not always be valid
    for l in range(1,36):
        noise=noise+histsig.GetBinContent(l)
    noise=noise/35
    print("noise: {0}".format(noise))

    for k in range(1,3600):
        bin_k = histsig.GetBinContent(k)
        histsig.SetBinContent(k+1, histsig.GetBinContent(k+1)-bin_k*a)
        corrfill.SetBinContent(k+1, corrfill.GetBinContent(k+1)+bin_k*a)
    hist_afterTypeI=histsig.Clone()

    for m in range(1,3600):
        histsig.SetBinContent(m, histsig.GetBinContent(m)-noise)
        histnoise.SetBinContent(m, noise)
        corrfill.SetBinContent(m, corrfill.GetBinContent(m)+noise)


    for i in range(1,3600):
        for j in range(i+1,3600):
            binsig_i=histsig.GetBinContent(i)
            binfull_i=histfull.GetBinContent(i)
            if not args.useresponse:
                histsig.SetBinContent(j,histsig.GetBinContent(j)-binsig_i*corrTemplate.GetBinContent(j-i))
                corrfill.SetBinContent(j, corrfill.GetBinContent(j)+binsig_i*corrTemplate.GetBinContent(j-i))
            else:
                histsig.SetBinContent(j,histsig.GetBinContent(j)-binfull_i*corrTemplate.GetBinContent(j-i))
                corrfill.SetBinContent(j,corrfill.GetBinContent(j)+binfull_i*corrTemplate.GetBinContent(j-i))

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

    newfile.WriteTObject(histfull,  "Before_Corr_"+run)
    newfile.WriteTObject(hist_afterTypeI, "After_TypeI_Corr_"+run)
    newfile.WriteTObject(histsig, "After_Corr_"+run)
    newfile.WriteTObject(histnoise, "Noise_"+run)
    newfile.WriteTObject(corrfill, "Overall_Correction_"+run)
    newfile.WriteTObject(ratiocorr, "Ratio_Correction_"+run)
    newfile.WriteTObject(ratio_gap, "Ratio_Nonlumi_"+run)
    newfile.WriteTObject(ratio_noise, "Ratio_Noise_"+run)
