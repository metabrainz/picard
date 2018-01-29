if [ -z "$CI_BUILD_TAG" ]
then
    python3 setup.py patch_version --platform=osx
fi
VERSION=$(python3 -c 'import picard; print(picard.__version__)')

rm -rf dist build locale
python3 setup.py clean
python3 setup.py build_ext
python3 setup.py build_locales
pip3 install pyinstaller
pyinstaller picard.spec

cd dist
ditto -rsrc --arch x86_64 'MusicBrainz Picard.app' 'MusicBrainz Picard.tmp'
rm -r 'MusicBrainz Picard.app'
mv 'MusicBrainz Picard.tmp' 'MusicBrainz Picard.app'
hdiutil create -volname "MusicBrainz Picard $VERSION" -srcfolder 'MusicBrainz Picard.app' -ov -format UDBZ ../picard.dmg
cd ..
ls
curl --upload-file "picard.dmg" https://transfer.sh/picard.dmg
