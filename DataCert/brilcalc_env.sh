export PATH=$HOME/.local/bin:/afs/cern.ch/cms/lumi/brilconda-1.0.3/bin:$PATH
#setenv PATH $HOME/.local/bin:/afs/cern.ch/cms/lumi/brilconda-1.0.3/bin:$PATH (csh.tcsh)
pip install --index-url="https://testpypi.python.org/pypi" --install-option="--prefix=$HOME/.local" brilws
