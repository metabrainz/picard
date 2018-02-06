#!/usr/bin/env bash
brew update
brew install python3
brew link python3 --force
brew install gettext
brew link gettext --force
brew install libdiscid
cp "/usr/local/Cellar/libdiscid/$DISCID_VERSION/lib/libdiscid.0.dylib" .
pip3 install --upgrade pip setuptools wheel
pip3 install virtualenv
virtualenv -p python3 .
