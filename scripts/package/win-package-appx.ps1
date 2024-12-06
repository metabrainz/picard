# Build a MSIX app package for Windows 10

Param(
  [ValidateScript({ Test-Path $_ -PathType Container })]
  [String]
  $PackageDir
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

$PackageDir = (Resolve-Path $PackageDir)

# Generate resource files
Copy-Item appxmanifest.xml $PackageDir
$PriConfigFile = (Join-Path (Resolve-Path .\build) priconfig.xml)
Push-Location $PackageDir
MakePri createconfig /ConfigXml $PriConfigFile /Default en-US /Overwrite
MakePri new /ProjectRoot $PackageDir /ConfigXml $PriConfigFile
Pop-Location

# Generate msix package
$PackageFile = "dist\MusicBrainz-Picard-${PicardVersion}_unsigned.msix"
MakeAppx pack /o /h SHA256 /d $PackageDir /p $PackageFile
