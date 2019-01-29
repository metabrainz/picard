#!/usr/bin/env bash
set -e

brew update
brew install gettext
brew link gettext --force
wget "https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-macosx10.9.pkg"
sudo installer -pkg python-${PYTHON_VERSION}-macosx10.9.pkg -target /
sudo python3 -m ensurepip
wget "ftp://ftp.musicbrainz.org/pub/musicbrainz/libdiscid/libdiscid-$DISCID_VERSION.tar.gz"
tar -xf "libdiscid-$DISCID_VERSION.tar.gz"
cd "libdiscid-$DISCID_VERSION"
./configure --prefix="$HOME/libdiscid"
make install
cd ..
cp "$HOME/libdiscid/lib/libdiscid.0.dylib" .
wget "https://github.com/acoustid/chromaprint/releases/download/v$FPCALC_VERSION/chromaprint-fpcalc-$FPCALC_VERSION-macos-x86_64.tar.gz"
tar -xf "chromaprint-fpcalc-$FPCALC_VERSION-macos-x86_64.tar.gz"
cp "chromaprint-fpcalc-$FPCALC_VERSION-macos-x86_64/fpcalc" .
pip3 install --upgrade pip setuptools wheel
pip3 install virtualenv
python3 -m virtualenv -p python3 .
