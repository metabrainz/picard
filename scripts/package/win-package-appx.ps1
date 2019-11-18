# Build a MSIX app package for Windows 10

Param(
  [System.Security.Cryptography.X509Certificates.X509Certificate]
  $Certificate,
  [Int]
  $BuildNumber
)

If (-Not $BuildNumber) {
  $BuildNumber = 0
}

$ScriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
. $ScriptDirectory\win-common.ps1 -Certificate $Certificate

Write-Output "Building Windows 10 app package..."

# Build
Remove-Item -Path build,dist/picard,locale -Recurse -ErrorAction Ignore
python setup.py clean 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py clean failed"
python setup.py build --build-number=$BuildNumber --disable-autoupdate 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py build failed"
python setup.py build_ext -i 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py build_ext -i failed"

# Package application
Write-Output "Building Windows installer..."
pyinstaller --noconfirm --clean picard.spec 2>&1 | %{ "$_" }
ThrowOnExeError "PyInstaller failed"
$PackageDir = (Resolve-Path dist\picard)
FinalizePackage $PackageDir

# Generate resource files
Copy-Item appxmanifest.xml $PackageDir
$PriConfigFile = (Join-Path (Resolve-Path .\build) priconfig.xml)
Push-Location $PackageDir
MakePri createconfig /ConfigXml $PriConfigFile /Default en-US /Overwrite
ThrowOnExeError "MakePri createconfig failed"
MakePri new /ProjectRoot $PackageDir /ConfigXml $PriConfigFile
ThrowOnExeError "MakePri new failed"
Pop-Location

# Generate msix package
$PicardVersion = (python -c "import picard; print(picard.__version__)")
$PackageFile = "dist\MusicBrainz Picard $PicardVersion.msix"
MakeAppx pack /o /h SHA256 /d $PackageDir /p $PackageFile
ThrowOnExeError "MakeAppx failed"

# Sign package
If ($Certificate) {
  SignTool sign /fd SHA256 /sha1 $Certificate.Thumbprint $PackageFile
  ThrowOnExeError "SignTool failed"
}
