# Build a MSIX app package for Windows 10

Param(
  [ValidateScript({ (Test-Path $_ -PathType Leaf) -or (-not $_) })]
  [String]
  $CertificateFile,
  [SecureString]
  $CertificatePassword,
  [Int]
  $BuildNumber
)

# Errors are handled explicitly. Otherwise any output to stderr when
# calling classic Windows exes causes a script error.
$ErrorActionPreference = 'Continue'

If (-Not $BuildNumber) {
  $BuildNumber = 0
}

If (-Not $Certificate -And $CertificateFile) {
  $Certificate = Get-PfxCertificate -FilePath $CertificateFile -Password $CertificatePassword
}

$ScriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
. $ScriptDirectory\win-common.ps1 -CertificateFile $CertificateFile -CertificatePassword $CertificatePassword

Write-Output "Building Windows 10 app package..."

# Set the publisher based on the certificate subject
if ($Certificate) {
  $env:PICARD_APPX_PUBLISHER = $Certificate.Subject
  Write-Output "Publisher: $env:PICARD_APPX_PUBLISHER"
}

# Build
Remove-Item -Path build,dist/picard,locale -Recurse -ErrorAction Ignore
python setup.py clean 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py clean failed"
python setup.py build --build-number=$BuildNumber --disable-autoupdate 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py build failed"
python setup.py build_ext -i 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py build_ext -i failed"

# Package application
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
If ($CertificateFile -or $Certificate) {
  $PackageFile = "dist\MusicBrainz-Picard-$PicardVersion.msix"
} Else {
  $PackageFile = "dist\MusicBrainz-Picard-$PicardVersion-unsigned.msix"
}
MakeAppx pack /o /h SHA256 /d $PackageDir /p $PackageFile
ThrowOnExeError "MakeAppx failed"

CodeSignBinary $PackageFile
