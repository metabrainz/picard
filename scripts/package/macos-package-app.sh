#!/usr/bin/env bash
set -e

if [ -z "$TRAVIS_TAG" ] && [ -n "$TRAVIS_OSX_IMAGE" ]; then
    python3 setup.py patch_version --platform="osx.$TRAVIS_OSX_IMAGE"
fi
VERSION=$(python3 -c 'import picard; print(picard.__version__)')

MACOS_VERSION=$(sw_vers -productVersion)
MACOS_VERSION_MAJOR=${MACOS_VERSION%.*.*}
MACOS_VERSION_MINOR=${MACOS_VERSION#*.}
MACOS_VERSION_MINOR=${MACOS_VERSION_MINOR%.*}

rm -rf dist build locale
python3 setup.py clean
python3 setup.py build
python3 setup.py build_ext -i
pyinstaller --noconfirm --clean picard.spec

CODESIGN=0
NOTARIZE=0
KEYCHAIN_PATH=picard.keychain
KEYCHAIN_PASSWORD=picard
CERTIFICATE_NAME="Developer ID Application: MetaBrainz Foundation Inc."
CERTIFICATE_FILE=scripts/package/appledev.p12

if [ -n "$encrypted_be5fb2212036_key" ] && [ -n "$encrypted_be5fb2212036_iv" ]; then
    openssl aes-256-cbc -K "$encrypted_be5fb2212036_key" -iv "$encrypted_be5fb2212036_iv" -in scripts/package/appledev.p12.enc -out $CERTIFICATE_FILE -d
fi

if [ -f scripts/package/appledev.p12 ] && [ -n "$appledev_p12_password" ]; then
    security create-keychain -p $KEYCHAIN_PASSWORD $KEYCHAIN_PATH
    security unlock-keychain -p $KEYCHAIN_PASSWORD $KEYCHAIN_PATH
    security set-keychain-settings $KEYCHAIN_PATH  # Ensure keychain stays unlocked
    security list-keychains -d user -s $KEYCHAIN_PATH
    security default-keychain -s $KEYCHAIN_PATH
    security import $CERTIFICATE_FILE -k $KEYCHAIN_PATH -P "$appledev_p12_password" -T /usr/bin/codesign
    # The line below is necessary when building on Sierra.
    # See https://stackoverflow.com/q/39868578
    security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k $KEYCHAIN_PASSWORD $KEYCHAIN_PATH
    security find-identity -p codesigning # For debugging
    CODESIGN=1
fi

# Submit app for notarization on macOS >= 10.14
if [ "$MACOS_VERSION_MAJOR" -eq 10 ] && [ "$MACOS_VERSION_MINOR" -ge 14 ]; then
    NOTARIZE=1
fi

cd dist

# Create app bundle
ditto -rsrc --arch x86_64 'MusicBrainz Picard.app' 'MusicBrainz Picard.tmp'
rm -r 'MusicBrainz Picard.app'
mv 'MusicBrainz Picard.tmp' 'MusicBrainz Picard.app'
if [ "$CODESIGN" = '1' ]; then
    # Enable hardened runtime if app will get notarized
    if [ "$NOTARIZE" = "1" ]; then
      codesign --verify --verbose --deep \
        --options runtime \
        --entitlements ../scripts/package/entitlements.plist \
        --keychain "$KEYCHAIN_PATH" --sign "$CERTIFICATE_NAME" \
        "MusicBrainz Picard.app"
      ../scripts/package/macos-notarize-app.sh "MusicBrainz Picard.app"
    else
      codesign --verify --verbose --deep \
        --keychain "$KEYCHAIN_PATH" --sign "$CERTIFICATE_NAME" \
        "MusicBrainz Picard.app"
    fi
fi

# Verify Picard executable works and required dependencies are bundled
VERSIONS=$("MusicBrainz Picard.app/Contents/MacOS/picard-run" --long-version)
echo "$VERSIONS"
ASTRCMP_REGEX="astrcmp C"
[[ $VERSIONS =~ $ASTRCMP_REGEX ]] || (echo "Failed: Build does not include astrcmp C" && false)
LIBDISCID_REGEX="libdiscid [0-9]+\.[0-9]+\.[0-9]+"
[[ $VERSIONS =~ $LIBDISCID_REGEX ]] || (echo "Failed: Build does not include libdiscid" && false)
"MusicBrainz Picard.app/Contents/MacOS/fpcalc" -version

# Package app bundle into DMG image
if [ -n "$TRAVIS_OSX_IMAGE" ]; then
  DMG="MusicBrainz-Picard-${VERSION}_macOS-$MACOS_VERSION_MAJOR.$MACOS_VERSION_MINOR.dmg"
else
  DMG="MusicBrainz-Picard-$VERSION.dmg"
fi
hdiutil create -volname "MusicBrainz Picard $VERSION" \
  -srcfolder 'MusicBrainz Picard.app' -ov -format UDBZ "$DMG"
[ "$CODESIGN" = '1' ] && codesign --verify --verbose \
  --keychain "$KEYCHAIN_PATH" --sign "$CERTIFICATE_NAME" "$DMG"
md5 -r "$DMG"

if [ -n "$UPLOAD_OSX" ]; then
    echo "Preparing to upload $DMG..."
    # make upload failures non fatal
    set +e
    # Set $AWS_ARTIFACTS_BUCKET, $AWS_ACCESS_KEY_ID and $AWS_SECRET_ACCESS_KEY for AWS S3 upload to work
    if [ -n "$AWS_ARTIFACTS_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
      pip3 install --upgrade awscli
      aws s3 cp --acl public-read "$DMG" "s3://${AWS_ARTIFACTS_BUCKET}/${TRAVIS_REPO_SLUG}/${TRAVIS_BUILD_NUMBER}/$DMG"
      echo "Package uploaded to https://s3.${AWS_DEFAULT_REGION}.amazonaws.com/${AWS_ARTIFACTS_BUCKET}/${TRAVIS_REPO_SLUG}/${TRAVIS_BUILD_NUMBER}/${DMG// /%20}"
    else
      # Fall back to transfer.sh
      curl -v --retry 6 --retry-delay 10 --max-time 180 --upload-file "$DMG" https://transfer.sh/
    fi
    set -e
    # Required for a newline between the outputs
    echo -e "\n"
fi
