#!/bin/bash
set -ex

# Run codacy-analysis-cli using markdownlint tool by default
#
# Optionally use the tool passed as argument
# List is available at https://docs.codacy.com/repositories-configure/codacy-configuration-file/#which-tools-can-be-configured-and-which-name-should-i-use
#
# Requires docker
# See https://github.com/codacy/codacy-analysis-cli for details

if [ -z "$1" ]; then
  TOOL=markdownlint
else
  # use tool passed as command-line argument
  TOOL="$1"
fi

# change to picard source directory
pushd "$(dirname "$0")/../../" || exit

CODACY_CODE="$(pwd)"
docker run \
  --rm=true \
  --env CODACY_CODE="$CODACY_CODE" \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --volume "$CODACY_CODE":"$CODACY_CODE":ro \
  --volume /tmp:/tmp \
  codacy/codacy-analysis-cli \
    analyze --verbose --tool "$TOOL"

popd
