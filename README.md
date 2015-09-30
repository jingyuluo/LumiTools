### LumiTools
Python scripts for making trees and plots for luminosity

Checkout instructions on lxplus:
cmsrel CMSSW_7_4_5  
cd CMSSW_7_4_5/src/  
cmsenv  
git clone http://github.com/capalmer85/LumiTools  
cd LumiTools/DataCert  

DataCert is weekly certification of luminosity for CMS data  
VdmPrep is for producing vdm mini-trees for the VdM framework


Instrucations for producing PCC ntuples:

cmsrel CMSSW_7_6_X
cd CMSSW_7_6_X/src
cmsenv
git cms-addpkg RecoLuminosity/LumiProducer
scram b -j 8
cd RecoLuminosity/LumiProducer/test/analysis/test

The script Run_PixVertex_LS.py can generate the PCC ntuplse for data certification.

The script crab3_dataCert_ZeroBiasSkim_150924.py can be modified to submit the CRAB jobs.

In the CRAB configuration file, "config.Data.runRange" should be the run numbers to be certified; "config.Data.inputDataset" can be fetched by " das_client --query='dataset dataset=/ZeroBias*/Run2015*Lumi*/ALCARECO run=RUN_NUMBER' " 


To submit CRAB jobs:

crab submit -c crab3_dataCert_ZeroBiasSkim_150924.py
