#!/usr/bin/env bash
set -e

VERSION=$(python3 -c 'import picard; print(picard.__version__)')

MACOS_VERSION=$(sw_vers -productVersion)
MACOS_VERSION_MAJOR=${MACOS_VERSION%.*}
MACOS_VERSION_MAJOR=${MACOS_VERSION_MAJOR%.*}
MACOS_VERSION_MINOR=${MACOS_VERSION#*.}
MACOS_VERSION_MINOR=${MACOS_VERSION_MINOR%.*}

APP_BUNDLE="MusicBrainz Picard.app"

CODESIGN=0
KEYCHAIN_PATH=picard.keychain
KEYCHAIN_PASSWORD=$(openssl rand -base64 32)
CODESIGN_IDENTITY="MetaBrainz Foundation Inc."
CERTIFICATE_FILE=scripts/package/appledev.p12

if [ -f "$CERTIFICATE_FILE" ] && [ -n "$CODESIGN_MACOS_P12_PASSWORD" ]; then
    echo "Preparing code signing certificate..."
    security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
    security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
    security set-keychain-settings "$KEYCHAIN_PATH"  # Ensure keychain stays unlocked
    security list-keychains -d user -s "$KEYCHAIN_PATH"
    security default-keychain -s "$KEYCHAIN_PATH"
    security import "$CERTIFICATE_FILE" -k "$KEYCHAIN_PATH" -P "$CODESIGN_MACOS_P12_PASSWORD" -T /usr/bin/codesign
    # The line below is necessary when building on Sierra.
    # See https://stackoverflow.com/q/39868578
    security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
    security find-identity -p codesigning # For debugging
    CODESIGN=1
    export CODESIGN_IDENTITY
fi

echo "Building Picard..."
rm -rf dist build
python3 setup.py clean
python3 setup.py build --disable-locales
python3 setup.py build_locales
python3 setup.py build_ext -i
pyinstaller --noconfirm --clean picard.spec

cd dist

if [ "$CODESIGN" = '1' ]; then
  ../scripts/package/macos-notarize-app.sh "$APP_BUNDLE"
  echo "Verifying signature and notarization for app bundle ${APP_BUNDLE}..."
  codesign --verify --verbose --deep --strict=symlinks --check-notarization  "$APP_BUNDLE"
fi

echo "Testing executables..."
"$APP_BUNDLE/Contents/MacOS/picard-run" --long-version --no-crash-dialog || echo "Failed running picard-run"
VERSIONS=$("$APP_BUNDLE/Contents/MacOS/picard-run" --long-version --no-crash-dialog)
echo "$VERSIONS"
ASTRCMP_REGEX="astrcmp C"
[[ $VERSIONS =~ $ASTRCMP_REGEX ]] || (echo "Failed: Build does not include astrcmp C" && false)
LIBDISCID_REGEX="libdiscid [0-9]+\.[0-9]+\.[0-9]+"
[[ $VERSIONS =~ $LIBDISCID_REGEX ]] || (echo "Failed: Build does not include libdiscid" && false)
"$APP_BUNDLE/Contents/Frameworks/fpcalc" -version

echo "Package app bundle into DMG image..."
DMG="MusicBrainz-Picard${VERSION:+-$VERSION}${MACOSX_DEPLOYMENT_TARGET:+-macOS-$MACOSX_DEPLOYMENT_TARGET}${TARGET_ARCH:+-$TARGET_ARCH}.dmg"
mkdir staging
mv "$APP_BUNDLE" staging/
# Offer a link to /Applications for easy installation
ln -s /Applications staging/Applications

set +e
# workaround hdiutil: create failed - Resource busy
ATTEMPTS=5
DELAY=5
for i in $(seq $ATTEMPTS); do
    hdiutil create -verbose -volname "MusicBrainz Picard $VERSION" \
      -srcfolder staging -ov -format UDBZ "$DMG"
    ret=$?
    [ "$ret" -eq 0 ] && break
    echo "hdutil failed with exit code $ret ($i/$ATTEMPTS), retrying in $DELAY seconds"
    sleep $DELAY
done
if [ "$ret" -ne 0 ]; then
  echo "hdiutil failed too many times, exiting..."
  exit "$ret"
fi
set -e

[ "$CODESIGN" = '1' ] && codesign --verify --verbose \
  --keychain "$KEYCHAIN_PATH" --sign "$CODESIGN_IDENTITY" "$DMG"
md5 -r "$DMG"
