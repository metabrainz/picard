#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "Specify app bundle as first parameter"
    exit 1
fi

if [ -z "$APPLE_ID_USER" ] || [ -z "$APPLE_ID_PASSWORD" ]; then
    echo "You need to set your Apple ID credentials with \$APPLE_ID_USER and \$APPLE_ID_PASSWORD."
    exit 1
fi

APP_BUNDLE=$(basename "$1")
APP_BUNDLE_DIR=$(dirname "$1")

xpath() {
  # the xpath tool command line syntax changed in Big Sur
  if [[ $(sw_vers -buildVersion) > "20A" ]]; then
    /usr/bin/xpath -e "$@"
  else
    /usr/bin/xpath "$@"
  fi
}

cd "$APP_BUNDLE_DIR" || exit 1

# Package app for submission
echo "Generating ZIP archive ${APP_BUNDLE}.zip..."
ditto -c -k --rsrc --keepParent "$APP_BUNDLE" "${APP_BUNDLE}.zip"

# Submit for notarization
echo "Submitting $APP_BUNDLE for notarization..."
RESULT=$(xcrun notarytool submit \
  --apple-id "$APPLE_ID_USER" \
  --team-id "$APPLE_ID_TEAM" \
  --password "$APPLE_ID_PASSWORD" \
  --output-format plist \
  --wait \
  --timeout 10m \
  "${APP_BUNDLE}.zip")

if [ $? -ne 0 ]; then
  echo "Submitting $APP_BUNDLE failed:"
  echo "$RESULT"
  exit 1
fi

STATUS=$(echo "$RESULT" | xpath \
  "//key[normalize-space(text()) = 'status']/following-sibling::string[1]/text()" 2> /dev/null)

if [ "$STATUS" = "Accepted" ]; then
  echo "Notarization of $APP_BUNDLE succeeded!"
else
  echo "Notarization of $APP_BUNDLE failed:"
  echo "$RESULT"
  exit 1
fi

# Staple the notary ticket
xcrun stapler staple "$APP_BUNDLE"
