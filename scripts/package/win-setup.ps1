Param(
  [Parameter(Mandatory=$true)]
  [String]
  $DiscidVersion,
  [Parameter(Mandatory=$true)]
  [String]
  $DiscidSha256Sum,
  [Parameter(Mandatory=$true)]
  [String]
  $FpcalcVersion,
  [Parameter(Mandatory=$true)]
  [String]
  $FpcalcSha256Sum
)

$ErrorActionPreference = "Stop"

$ScriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
. $ScriptDirectory\win-common.ps1

New-Item -Name .\build -ItemType Directory -ErrorAction Ignore

$ArchiveFile = ".\build\libdiscid.zip"
Write-Output "Downloading libdiscid $DiscidVersion to $ArchiveFile..."
DownloadFile -Url "http://ftp.musicbrainz.org/pub/musicbrainz/libdiscid/libdiscid-$DiscidVersion-win.zip" `
  -FileName $ArchiveFile
VerifyHash -FileName $ArchiveFile -Sha256Sum $DiscidSha256Sum
Expand-Archive -Path $ArchiveFile -DestinationPath .\build\libdiscid -Force
Copy-Item .\build\libdiscid\libdiscid-$DiscidVersion-win\x64\discid.dll .

$ArchiveFile = ".\build\fpcalc.zip"
Write-Output "Downloading chromaprint-fpcalc $FpcalcVersion to $ArchiveFile..."
DownloadFile -Url "https://github.com/acoustid/chromaprint/releases/download/v$FpcalcVersion/chromaprint-fpcalc-$FpcalcVersion-windows-x86_64.zip" `
  -FileName $ArchiveFile
VerifyHash -FileName $ArchiveFile -Sha256Sum $FpcalcSha256Sum
Expand-Archive -Path $ArchiveFile -DestinationPath .\build\fpcalc -Force
Copy-Item .\build\fpcalc\chromaprint-fpcalc-$FpcalcVersion-windows-x86_64\fpcalc.exe .
