#!/usr/bin/env bash
PYFILES=$(git diff --cached --name-only --diff-filter=ACM| grep "\\.py$" | grep --invert-match \
  -e "^tagger\\.py$" \
  -e "^picard/resources\\.py$" \
  -e "^picard/const/\(attributes\|countries\)\\.py$" \
  -e "^picard/ui/ui_.*\\.py$" \
  -e "^scripts/picard\\.in$")

if [ ! -z "$PYFILES" ]; then
  set -e
  isort --check-only --diff --quiet $PYFILES
  flake8 $PYFILES
fi
