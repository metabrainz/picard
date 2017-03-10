curl -L -O https://github.com/acoustid/chromaprint/releases/download/v$CHROMAPRINT_FPCALC_VERSION/chromaprint-fpcalc-$CHROMAPRINT_FPCALC_VERSION-macos-x86_64.tar.gz
tar --strip-components 1 -xf chromaprint-fpcalc-$CHROMAPRINT_FPCALC_VERSION-macos-x86_64.tar.gz chromaprint-fpcalc-$CHROMAPRINT_FPCALC_VERSION-macos-x86_64/fpcalc

curl -L -O http://ftp.musicbrainz.org/pub/musicbrainz/libdiscid/libdiscid-$DISCID_VERSION-mac.zip
unzip -jx libdiscid-$DISCID_VERSION-mac.zip libdiscid-$DISCID_VERSION-mac/intel64/libdiscid.0.dylib
export LD_LIBRARY_PATH=`pwd`:$LD_LIBRARY_PATH

curl -L -o plugins.zip https://github.com/metabrainz/picard-plugins/archive/master.zip
unzip -x plugins.zip
mkdir contrib
mv picard-plugins-master/plugins contrib/plugins

rm -rf e
virtualenv -p python2.7 --system-site-packages e
. e/bin/activate

pip install mutagen==$MUTAGEN_VERSION
pip install discid==$PYTHON_DISCID_VERSION
pip install py2app==$PY2APP_VERSION

perl -pi -e 's{plugin_dir = (.*)$}{plugin_dir = "/Developer/Applications/Qt/plugins"}' e/lib/python2.7/site-packages/py2app/recipes/sip.py

echo 'from __future__ import absolute_import' > e/lib/python2.7/site-packages/py2app/recipes/sip.py.new
cat e/lib/python2.7/site-packages/py2app/recipes/sip.py >> e/lib/python2.7/site-packages/py2app/recipes/sip.py.new
mv e/lib/python2.7/site-packages/py2app/recipes/sip.py.new e/lib/python2.7/site-packages/py2app/recipes/sip.py

if [ -z "$CI_BUILD_TAG" ]
then
    python setup.py patch_version --platform=osx
fi
VERSION=`python -c 'import picard; print picard.__version__'`

rm -rf dist build locale
python setup.py clean
python setup.py build_ext -i
python setup.py build_locales -i
python setup.py py2app

cd dist
ditto -rsrc --arch x86_64 'MusicBrainz Picard.app' 'MusicBrainz Picard.tmp'
rm -r 'MusicBrainz Picard.app'
mv 'MusicBrainz Picard.tmp' 'MusicBrainz Picard.app'
hdiutil create -volname "MusicBrainz Picard $VERSION" -srcfolder 'MusicBrainz Picard.app' -ov -format UDBZ ../MusicBrainz-Picard-$VERSION.dmg
