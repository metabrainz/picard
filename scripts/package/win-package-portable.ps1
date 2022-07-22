# Build a portable app

Param(
  [System.Security.Cryptography.X509Certificates.X509Certificate]
  $Certificate,
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
. $ScriptDirectory\win-common.ps1 -Certificate $Certificate

Write-Output "Building portable exe..."

# Build
Remove-Item -Path build,locale -Recurse -ErrorAction Ignore
python setup.py clean 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py clean failed"
python setup.py build --build-number=$BuildNumber 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py build failed"
python setup.py build_ext -i 2>&1 | %{ "$_" }
ThrowOnExeError "setup.py build_ext -i failed"

# Package application
$env:PICARD_BUILD_PORTABLE = '1'
pyinstaller --noconfirm --clean picard.spec 2>&1 | %{ "$_" }
ThrowOnExeError "PyInstaller failed"
CodeSignBinary dist\MusicBrainz-Picard-*.exe
