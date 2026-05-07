#!/bin/bash
set -e

cd "$(dirname "$0")/../../" || exit

RELEASE_TAG=$(git describe --match "release-*" --abbrev=0 --always HEAD)
CHANGE_COUNT=$(git rev-list --count "$RELEASE_TAG..HEAD")
COMMIT_HASH=$(git rev-parse --short HEAD)

if [ "$CHANGE_COUNT" -ne 0 ]; then
    VERSION_EXTRA="$CHANGE_COUNT-$COMMIT_HASH"
    echo "Patching version: $VERSION_EXTRA"
    python setup.py patch_version --platform="$VERSION_EXTRA"
fi

VERSION=$(python -c "import picard; print(picard.__version__)")
echo "Patched version: v$VERSION"
