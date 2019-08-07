#!/usr/bin/env bash
set -e

if [ -z "$TRAVIS_TAG" ]
then
    python3 setup.py patch_version --platform=osx_$TRAVIS_OSX_IMAGE
fi
VERSION=$(python3 -c 'import picard; print(picard.__version__)')

rm -rf dist build locale
python3 setup.py clean
python3 setup.py build_ext
python3 setup.py build_locales
# Downgrade pip to 18.1 due to https://tickets.metabrainz.org/browse/PICARD-1456
pip3 install pip==18.1
pip3 install -r requirements-build.txt
pyinstaller picard.spec

CODESIGN=0
KEYCHAIN_PATH=picard.keychain
KEYCHAIN_PASSWORD=picard
CERTIFICATE_NAME="Developer ID Application: MetaBrainz Foundation Inc."
CERTIFICATE_FILE=scripts/appledev.p12

if [ -n "$encrypted_be5fb2212036_key" ] && [ -n "$encrypted_be5fb2212036_iv" ]; then
    openssl aes-256-cbc -K "$encrypted_be5fb2212036_key" -iv "$encrypted_be5fb2212036_iv" -in scripts/appledev.p12.enc -out $CERTIFICATE_FILE -d
fi

if [ -f scripts/appledev.p12 ] && [ -n "$appledev_p12_password" ]; then
    security create-keychain -p $KEYCHAIN_PASSWORD $KEYCHAIN_PATH
    security unlock-keychain -p $KEYCHAIN_PASSWORD $KEYCHAIN_PATH
    security list-keychains -d user -s $KEYCHAIN_PATH
    security default-keychain -s $KEYCHAIN_PATH
    security import $CERTIFICATE_FILE -k $KEYCHAIN_PATH -P "$appledev_p12_password" -T /usr/bin/codesign
    # The line below is necessary when building on Sierra.
    # See https://stackoverflow.com/q/39868578
    security set-key-partition-list -S apple-tool:,apple: -s -k $KEYCHAIN_PASSWORD $KEYCHAIN_PATH
    security find-identity -p codesigning # For debugging
    CODESIGN=1
fi

cd dist
ditto -rsrc --arch x86_64 'MusicBrainz Picard.app' 'MusicBrainz Picard.tmp'
rm -r 'MusicBrainz Picard.app'
mv 'MusicBrainz Picard.tmp' 'MusicBrainz Picard.app'
[ "$CODESIGN" = '1' ] && codesign --keychain $KEYCHAIN_PATH --verify --verbose --deep --sign "$CERTIFICATE_NAME" 'MusicBrainz Picard.app'
dmg="MusicBrainz Picard $VERSION.dmg"
hdiutil create -volname "MusicBrainz Picard $VERSION" -srcfolder 'MusicBrainz Picard.app' -ov -format UDBZ "$dmg"
[ "$CODESIGN" = '1' ] && codesign --keychain $KEYCHAIN_PATH --verify --verbose --sign "$CERTIFICATE_NAME" "$dmg"
if [ -n "$UPLOAD_OSX" ]
then
    set +e
    # make upload failures non fatal
    curl -v --retry 6 --retry-delay 10 --upload-file "$dmg" https://transfer.sh/
    set -e
    # Required for a newline between the outputs
    echo -e "\n"
    md5 -r "$dmg"
fi
