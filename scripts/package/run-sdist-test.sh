#!/usr/bin/env bash

# Build the sdist archive, extract it and run the tests.

set -e

rm -rf dist
python -m build --sdist
cd dist
SDIST_ARCHIVE=$(echo picard-*.tar.gz)
tar xvf "$SDIST_ARCHIVE"
cd "${SDIST_ARCHIVE%.tar.gz}"
pytest --verbose
