#!/usr/bin/env bash
brew update
brew tap samj1912/core
brew tap-pin samj1912/core
brew install python3
brew link python3 --force
brew install gettext
brew link gettext --force
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
virtualenv -p python3 .
