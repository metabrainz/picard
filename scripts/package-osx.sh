if [ -z "$CI_BUILD_TAG" ]
then
    python setup.py patch_version --platform=osx
fi
VERSION=`python -c 'import picard; print picard.__version__'`

rm -rf dist build locale
python setup.py clean
python setup.py build_ext -i
python setup.py build_locales -i
pyinstaller picard.spec

cd dist
ditto -rsrc --arch x86_64 'MusicBrainz Picard.app' 'MusicBrainz Picard.tmp'
rm -r 'MusicBrainz Picard.app'
mv 'MusicBrainz Picard.tmp' 'MusicBrainz Picard.app'
hdiutil create -volname "MusicBrainz Picard $VERSION" -srcfolder 'MusicBrainz Picard.app' -ov -format UDBZ ../MusicBrainz-Picard-$VERSION.dmg
