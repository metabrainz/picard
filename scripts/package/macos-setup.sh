#!/usr/bin/env bash
set -e

# Install gettext
brew install gettext
brew link gettext --force

# Install requested Python version
if [ -n "$PYTHON_VERSION" ]; then
  wget "https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-macosx10.9.pkg"
  sudo installer -pkg "python-${PYTHON_VERSION}-macosx10.9.pkg" -target /
  sudo python3 -m ensurepip
fi

# Install libdiscid
if [ ! -f "$HOME/libdiscid/lib/libdiscid.0.dylib" ]; then
  wget "ftp://ftp.musicbrainz.org/pub/musicbrainz/libdiscid/libdiscid-$DISCID_VERSION.tar.gz"
  tar -xf "libdiscid-$DISCID_VERSION.tar.gz"
  cd "libdiscid-$DISCID_VERSION"
  ./configure --prefix="$HOME/libdiscid"
  make install
  cd ..
fi
cp "$HOME/libdiscid/lib/libdiscid.0.dylib" .

# Install fpcalc
if [ -n "$FPCALC_VERSION" ]; then
  wget "https://github.com/acoustid/chromaprint/releases/download/v$FPCALC_VERSION/chromaprint-fpcalc-$FPCALC_VERSION-macos-x86_64.tar.gz"
  tar -xf "chromaprint-fpcalc-$FPCALC_VERSION-macos-x86_64.tar.gz"
  cp "chromaprint-fpcalc-$FPCALC_VERSION-macos-x86_64/fpcalc" .
fi

# Install AcousticBrainz extractor
if [ -n "$ABEXTRACTOR_VERSION" ]; then
  wget "https://github.com/phw/essentia-extractor-builds/releases/download/$ABEXTRACTOR_VERSION/essentia-extractor-$ABEXTRACTOR_VERSION-macos.tar.gz"
  tar -xf "essentia-extractor-$ABEXTRACTOR_VERSION-macos.tar.gz"
  cp "essentia-extractor-$ABEXTRACTOR_VERSION-macos/streaming_extractor_music" .
fi
