brew install python3
brew link python3 --force
brew install gettext
brew link gettext --force
brew install libdiscid 
pip3 install --upgrade pip setuptools wheel
pip3 install virtualenv
virtualenv -p python3 .
source bin/activate
