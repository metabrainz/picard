#!/bin/bash
cd "$(dirname "$0")/../../" || exit

PICARD_VERSION=$(python -c "import picard; print(picard.__version__)")
TAG="release-$PICARD_VERSION"

echo "Tagging $TAG..."
git tag --sign "$TAG" --message="Release $PICARD_VERSION" $@
