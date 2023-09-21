# Build a Windows installer

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

$ScriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
. $ScriptDirectory\win-common.ps1 -CertificateFile $CertificateFile -CertificatePassword $CertificatePassword

Write-Output "Building Windows installer..."

# Build
Remove-Item -Path build,dist/picard,locale -Recurse -ErrorAction Ignore
python setup.py clean 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py clean failed"
python setup.py build --build-number=$BuildNumber 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py build failed"
python setup.py build_ext -i 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py build_ext -i failed"

# Package application
pyinstaller --noconfirm --clean picard.spec 2>&1 | %{ "$_" }
ThrowOnExeError "PyInstaller failed"
FinalizePackage dist\picard

# Build the installer
makensis.exe /INPUTCHARSET UTF8 installer\picard-setup.nsi 2>&1 | %{ "$_" }
ThrowOnExeError "NSIS failed"
CodeSignBinary installer\picard-setup-*.exe
