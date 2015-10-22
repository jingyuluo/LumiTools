import sys, os
from math import exp
import subprocess
import ROOT
from ROOT import TFile
from ROOT import gStyle


filename=sys.argv[1]
run=sys.argv[2]

tfile=ROOT.TFile(filename)
h_origin=tfile.Get("Before_Corr_"+run)
h_after=tfile.Get("After_Corr_"+run)

total_origin=0
total_after=0
for i in range(3600):
    if h_origin.GetBinContent(i) > 0.5:
        total_origin+=h_origin.GetBinContent(i)
        total_after+=h_after.GetBinContent(i)


print "Percentage of Correction is:", total_after/total_origin

