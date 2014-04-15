set PATH=%PATH%;%WORKSPACE%;C:\MinGW\bin;C:\Python27;C:\Python27\Scripts;"C:\Program Files\7-Zip"
call "C:\Program Files\Microsoft Visual Studio 9.0\Common7\Tools\vsvars32.bat"

del installer\*.exe

copy /Y "C:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\msvcr90.dll" .
copy /Y "C:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\msvcp90.dll" .

7z e -odeps deps\chromaprint-fpcalc-*.zip
copy /Y deps\fpcalc.exe .

REM virtualenv --system-site-packages e
set PATH=%WORKSPACE%\e\scripts;%PATH%

pip install -U discid
pip install -U mutagen

python setup.py patch_version --platform=win

rmdir /S /Q dist
python setup.py clean
python setup.py build_ext -i
python setup.py build_locales -i
python setup.py bdist_nsis
