# Picard release process


## Release preparation (few weeks/days before)


### Synchronize picard.pot with sources

```bash
python setup.py regen_pot_file && git diff --quiet || git commit -m 'Update pot file' -- po/picard.pot
```

And push changes to main remote repository, see [po/README.md](po/README.md) for details about translations

## Ensure git repository tree is clean

From the local repository:

### Check out the repo master branch

```bash
git fetch $PICARD_REMOTE && git checkout master
```

### Ensure nothing is on the way

```bash
git reset --hard $PICARD_REMOTE/master && git clean -f -d
```


#### Remove old compiled modules

```bash
find . -type f -name '*.pyc' -exec rm -f {} \;
```

### Tag to save the current state

```bash
git tag "before-release-$PICARD_VERSION" --force
```

### Remove any BOM nasty bytes from files

This shouldn't be needed, but better to check before releasing

```bash
git ls-tree --full-tree -r HEAD --name-only |while read f; do sed -i '1s/^\xEF\xBB\xBF//' "$f"; done && git diff --quiet || git commit -a -m 'Remove nasty BOM bytes'
```

## Synchronize generated consts

```bash
python setup.py update_constants && git diff --quiet || git commit -a -m 'Update constants' -- picard/const/*.py
```

## Update NEWS.txt

TODO: explain how

## Update Picard version

Edit `picard/__init__.py` and set new version tuple

Run tests:

```bash
python setup.py test
```

Commit changes!


## Tag new version

```bash
git tag -s "$PICARD_RELEASE_TAG" -m "Release $PICARD_VERSION"
```

Stable release tags have the following format: `release-#.#.#`
Example: `release-2.1.0`

## Update Picard version to next dev version

Edit `picard/__init__.py` and set new dev version tuple.

Run tests:

```bash
python setup.py test
```

Commit changes!


## Push new commits and tags to remote

```bash
git push "$PICARD_REMOTE" master:master
git push "$PICARD_REMOTE" tag "$PICARD_RELEASE_TAG"
```

### To revert after push

```bash
git tag -d "release-$PICARD_VERSION"
git reset --hard "before-release-$PICARD_VERSION"
git push "$PICARD_REMOTE" :"$TAG"
git push "$PICARD_REMOTE" "before-release-$PICARD_VERSION":master --force
```
