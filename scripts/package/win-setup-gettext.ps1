Param(
  [Parameter(Mandatory = $true)]
  [String]
  $GettextVersion,
  [Parameter(Mandatory = $true)]
  [String]
  $GettextSha256Sum
)

$ErrorActionPreference = "Stop"

$ScriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
. $ScriptDirectory\win-common.ps1

$ArchiveFile = ".\gettext-tools-windows.zip"
Write-Output "Downloading gettext-tools-windows $GettextVersion to $ArchiveFile..."
DownloadFile -Url "https://github.com/vslavik/gettext-tools-windows/releases/download/v$GettextVersion/gettext-tools-windows-$GettextVersion.zip" `
  -FileName $ArchiveFile
VerifyHash -FileName $ArchiveFile -Sha256Sum $GettextSha256Sum
Expand-Archive -Path $ArchiveFile -DestinationPath .\gettext -Force
