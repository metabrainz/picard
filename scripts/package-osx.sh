export PATH=/Library/Frameworks/Python.framework/Versions/2.7/bin:$PATH
export LD_LIBRARY_PATH=`pwd`:$LD_LIBRARY_PATH

cd deps
tar xf chromaprint-fpcalc-*.tar.gz
rm chromaprint-fpcalc-*.tar.gz
export PATH=`pwd`/`ls | grep chromaprint-fpcalc`:$PATH
cd ..

if [ "$PATCH_VERSION" = "1" ]
then
    python2.7 setup.py patch_version --platform=osx
fi
version=`python -c 'import picard; print picard.__version__'`

rm -rf e
virtualenv -p python2.7 --system-site-packages e
. e/bin/activate

pip install mutagen==1.27
pip install https://github.com/JonnyJD/python-discid/archive/dmg.zip
pip install py2app==0.9

perl -pi -e 's{plugin_dir = (.*)$}{plugin_dir = "/Developer/Applications/Qt/plugins"}' e/lib/python2.7/site-packages/py2app/recipes/sip.py

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
