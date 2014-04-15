cd deps
tar xf chromaprint-fpcalc-*.tar.gz
rm chromaprint-fpcalc-*.tar.gz
export PATH=`pwd`/`ls | grep chromaprint-fpcalc`:$PATH
cd ..

python2.7 setup.py patch_version --platform=osx
version=`python -c 'import picard; print picard.__version__'`

. e/bin/activate

rm -rf dist build locale
python2.7 setup.py clean
python2.7 setup.py build_ext -i
python2.7 setup.py build_locales -i
python2.7 setup.py py2app

cd dist
ditto -rsrc --arch x86_64 'MusicBrainz Picard.app' 'MusicBrainz Picard.tmp'
rm -r 'MusicBrainz Picard.app'
mv 'MusicBrainz Picard.tmp' 'MusicBrainz Picard.app'
hdiutil create -volname "MusicBrainz Picard $version" -srcfolder 'MusicBrainz Picard.app' -ov -format UDBZ MusicBrainz-Picard-$version.dmg
