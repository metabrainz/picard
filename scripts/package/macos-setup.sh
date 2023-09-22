#!/usr/bin/env bash
set -e

# Install gettext
brew install gettext
brew link gettext --force

# Install requested Python version
if [ -n "$PYTHON_VERSION" ]; then
  PYTHON_FILENAME=python-$PYTHON_VERSION.pkg
  wget "https://www.python.org/ftp/python/${PYTHON_VERSION%-*}/$PYTHON_FILENAME"
  echo "$PYTHON_SHA256SUM  $PYTHON_FILENAME" | shasum --algorithm 256 --check --status
  sudo installer -pkg "$PYTHON_FILENAME" -target /
  sudo python3 -m ensurepip
fi

# Install libdiscid
if [ -n "$DISCID_VERSION" ]; then
  DISCID_FILENAME="libdiscid-$DISCID_VERSION-mac.zip"
  wget "ftp://ftp.musicbrainz.org/pub/musicbrainz/libdiscid/$DISCID_FILENAME"
  echo "$DISCID_SHA256SUM  $DISCID_FILENAME" | shasum --algorithm 256 --check --status
  unzip "$DISCID_FILENAME"
  cp "libdiscid-$DISCID_VERSION-mac/x86_64/libdiscid.0.dylib" .
fi

# Install fpcalc
if [ -n "$FPCALC_VERSION" ]; then
  FPCALC_FILENAME="chromaprint-fpcalc-$FPCALC_VERSION-macos-universal.tar.gz"
  wget "https://github.com/acoustid/chromaprint/releases/download/v$FPCALC_VERSION/$FPCALC_FILENAME"
  echo "$FPCALC_SHA256SUM  $FPCALC_FILENAME" | shasum --algorithm 256 --check --status
  tar -xf "$FPCALC_FILENAME"
  cp "chromaprint-fpcalc-$FPCALC_VERSION-macos-universal/fpcalc" .
fi
