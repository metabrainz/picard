#!/usr/bin/env bash
set -e

# Install gettext
brew install gettext
brew link gettext --force

# Install requested Python version
if [ -n "$PYTHON_VERSION" ]; then
  PYTHON_FILENAME=python-$PYTHON_VERSION-macosx10.9.pkg
  wget "https://www.python.org/ftp/python/$PYTHON_VERSION/$PYTHON_FILENAME"
  echo "$PYTHON_SHA256SUM  $PYTHON_FILENAME" | shasum --algorithm 256 --check --status
  sudo installer -pkg "$PYTHON_FILENAME" -target /
  sudo python3 -m ensurepip
fi

# Install libdiscid
if [ ! -f "$HOME/libdiscid/lib/libdiscid.0.dylib" ]; then
  DISCID_FILENAME="libdiscid-$DISCID_VERSION.tar.gz"
  wget "ftp://ftp.musicbrainz.org/pub/musicbrainz/libdiscid/$DISCID_FILENAME"
  echo "$DISCID_SHA256SUM  $DISCID_FILENAME" | shasum --algorithm 256 --check --status
  tar -xf "$DISCID_FILENAME"
  cd "libdiscid-$DISCID_VERSION"
  ./configure --prefix="$HOME/libdiscid"
  make install
  cd ..
fi
cp "$HOME/libdiscid/lib/libdiscid.0.dylib" .

# Install fpcalc
if [ -n "$FPCALC_VERSION" ]; then
  FPCALC_FILENAME="chromaprint-fpcalc-$FPCALC_VERSION-macos-x86_64.tar.gz"
  wget "https://github.com/acoustid/chromaprint/releases/download/v$FPCALC_VERSION/$FPCALC_FILENAME"
  echo "$FPCALC_SHA256SUM  $FPCALC_FILENAME" | shasum --algorithm 256 --check --status
  tar -xf "$FPCALC_FILENAME"
  cp "chromaprint-fpcalc-$FPCALC_VERSION-macos-x86_64/fpcalc" .
fi

# Install AcousticBrainz extractor
if [ -n "$ABEXTRACTOR_VERSION" ]; then
  ABEXTRACTOR_FILENAME="essentia-extractor-$ABEXTRACTOR_VERSION-macos.tar.gz"
  wget "https://github.com/phw/essentia-extractor-builds/releases/download/$ABEXTRACTOR_VERSION/$ABEXTRACTOR_FILENAME"
  echo "$ABEXTRACTOR_SHA256SUM  $ABEXTRACTOR_FILENAME" | shasum --algorithm 256 --check --status
  tar -xf "$ABEXTRACTOR_FILENAME"
  cp "essentia-extractor-$ABEXTRACTOR_VERSION-macos/streaming_extractor_music" .
fi
