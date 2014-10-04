#!/bin/bash

set -e
#set -x

# Helper script for the release process

#############################################################################
# WARNING: you have to know what you are doing before executing this script #
#                                                                           #
# You have to edit Variables section before anything else                   #
#############################################################################

# Better to test on your own remote repo first !

# Copy this script outside your repo
#  cp ./scripts/do_release.sh ~
# edit it:
#  gvim ~/do_release.sh
# run it:
# ~/do_release.sh

# comment out this line after editing following variables
echo "Copy this script outside the source tree, and modify it !"; exit 1

# Variables

PICARD_REPO_PATH=/home/zas/src/picard_zas
PICARD_REMOTE=origin
PICARD_VERSION="1.3"
PICARD_VERSION_TUPLE="(1, 3, 0, 'final', 0)"
PICARD_NEXT_VERSION="1.4"
PICARD_NEXT_VERSION_TUPLE="(1, 4, 0, 'dev', 1)"
PICARD_RELEASE_TAG="release-$PICARD_VERSION"


echo "=== Preparing for $PICARD_VERSION release ==="

echo "=== Ensure git repository tree is clean ==="

cd "$PICARD_REPO_PATH" || exit 1
git fetch $PICARD_REMOTE && git checkout master && git reset --hard $PICARD_REMOTE/master && git clean -f -d
git tag "before-release-$PICARD_VERSION" --force

echo "=== Remove old compiled modules in case of ==="
find "$PICARD_REPO_PATH" -type f -name '*.pyc' -exec rm -f {} \;


echo "=== Remove any BOM nasty bytes from files ==="

# this shouldn't be needed, but better to check before releasing
git ls-tree --full-tree -r HEAD --name-only |while read f; do sed -i '1s/^\xEF\xBB\xBF//' "$f"; done && git diff --quiet || git commit -a -m 'Remove nasty BOM bytes'


echo "=== Get latest translations from Transifex ==="

python setup.py get_po_files && git diff --quiet || git commit -m 'Update .po files' -- po/


echo "=== Ensure generated consts are in sync with MB server ==="

python setup.py update_constants && git diff --quiet || git commit -a -m 'Update constants' -- picard/const/attributes.py  picard/const/countries.py


echo "=== Be sure picard.pot is in sync with sources ==="

python setup.py regen_pot_file && git diff --quiet || git commit -m 'Update pot file' -- po/picard.pot


echo "=== Set date in NEWS.txt ==="

OLD=$PICARD_VERSION; NEW=$PICARD_NEXT_VERSION; \
sed -i -e "s/^Version [^ ]\+ - xxxx-xx-xx\s*$/Version $OLD - "$(date +%F -u)"/" -e "1s/^/Version $NEW - xxxx-xx-xx\n\n/" NEWS.txt \
&& git diff --quiet || git commit -m "Update release date for version $OLD" -- NEWS.txt


echo "=== Update Picard version ==="

sed -i "s/^PICARD_VERSION = \(.*\)$/PICARD_VERSION = $PICARD_VERSION_TUPLE/" picard/__init__.py \
&& python setup.py test && git diff --quiet || git commit -m "Update version to $PICARD_VERSION" -- picard/__init__.py


echo "=== Tag new version ==="

git tag -s "$PICARD_RELEASE_TAG" -m "Release $PICARD_VERSION"

echo "=== Update Picard version to next dev ==="

sed -i "s/^PICARD_VERSION = \(.*\)$/PICARD_VERSION = $PICARD_NEXT_VERSION_TUPLE/" picard/__init__.py \
&& python setup.py test && git diff --quiet || git commit -m "Update version to $PICARD_NEXT_VERSION dev" -- picard/__init__.py

echo "=== Push new commits to master branch ==="

echo "**** TO PUSH ****"
cat <<-EOF
git push "$PICARD_REMOTE" master:master
git push "$PICARD_REMOTE" tag "$PICARD_RELEASE_TAG"
EOF

echo "**** To revert after push ****"
cat <<-EOF
git tag -d "release-$PICARD_VERSION"
git reset --hard "before-release-$PICARD_VERSION"
git push "$PICARD_REMOTE" :"$TAG"
git push "$PICARD_REMOTE" "before-release-$PICARD_VERSION":master --force
EOF
