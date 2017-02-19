echo on

set PATH=%PATH%;%CI_PROJECT_DIR%;C:\MinGW\bin;C:\Python27;C:\Python27\Scripts;"C:\Program Files\7-Zip";"C:\Program Files\GnuWin32\bin"
call "C:\Program Files\Microsoft Visual Studio 9.0\Common7\Tools\vsvars32.bat"

copy /Y "C:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\msvcr90.dll" .
copy /Y "C:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\msvcp90.dll" .

wget --no-check-certificate https://github.com/acoustid/chromaprint/releases/download/v%CHROMAPRINT_FPCALC_VERSION%/chromaprint-fpcalc-%CHROMAPRINT_FPCALC_VERSION%-windows-i686.zip -O fpcalc.zip
7z x fpcalc.zip -y
copy /Y chromaprint-fpcalc-%CHROMAPRINT_FPCALC_VERSION%-windows-i686\fpcalc.exe .

wget --no-check-certificate http://ftp.musicbrainz.org/pub/musicbrainz/libdiscid/libdiscid-%DISCID_VERSION%-win32.zip -O libdiscid.zip
7z x libdiscid.zip -y
copy /Y libdiscid-%DISCID_VERSION%-win32\discid.dll .

wget --no-check-certificate https://github.com/metabrainz/picard-plugins/archive/master.zip -O plugins.zip
7z x plugins.zip -y
mkdir .\contrib\
move .\picard-plugins-master\plugins .\contrib\plugins

rmdir /S /Q e
virtualenv --system-site-packages e
set PATH=%CI_PROJECT_DIR%\e\scripts;%PATH%

pip install mutagen==%MUTAGEN_VERSION%
pip install discid==%PYTHON_DISCID_VERSION%

if "%CI_BUILD_TAG%" == "" python setup.py patch_version --platform=win

rmdir /S /Q dist build locale
python setup.py clean
python setup.py build_ext -i
python setup.py build_locales -i
python setup.py bdist_nsis

move installer\*.exe .
