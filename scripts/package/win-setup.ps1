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
  $FpcalcSha256Sum,
  [Parameter(Mandatory=$true)]
  [String]
  $AbextractorVersion,
  [Parameter(Mandatory=$true)]
  [String]
  $AbextractorSha256Sum
)

$ErrorActionPreference = "Stop"

Function DownloadFile {
  Param(
    [Parameter(Mandatory=$true)]
    [String]
    $FileName,
    [Parameter(Mandatory=$true)]
    [String]
    $Url
  )
  $OutputPath = (Join-Path (Resolve-Path .) $FileName)
  (New-Object System.Net.WebClient).DownloadFile($Url, "$OutputPath")
}

Function VerifyHash {
  Param(
    [Parameter(Mandatory = $true)]
    [String]
    $FileName,
    [Parameter(Mandatory = $true)]
    [String]
    $Sha256Sum
  )
  If ((Get-FileHash "$FileName").hash -ne "$Sha256Sum") {
    Throw "Invalid SHA256 hash for $FileName"
  }
}

New-Item -Name .\build -ItemType Directory -ErrorAction Ignore

$ArchiveFile = ".\build\libdiscid.zip"
Write-Output "Downloading libdiscid $DiscidVersion to $ArchiveFile..."
DownloadFile -Url "https://github.com/metabrainz/libdiscid/releases/download/v$DiscidVersion/libdiscid-$DiscidVersion-win64.zip" `
  -FileName $ArchiveFile
VerifyHash -FileName $ArchiveFile -Sha256Sum $DiscidSha256Sum
Expand-Archive -Path $ArchiveFile -DestinationPath .\build\libdiscid -Force
Copy-Item .\build\libdiscid\discid.dll .

$ArchiveFile = ".\build\fpcalc.zip"
Write-Output "Downloading chromaprint-fpcalc $FpcalcVersion to $ArchiveFile..."
DownloadFile -Url "https://github.com/acoustid/chromaprint/releases/download/v$FpcalcVersion/chromaprint-fpcalc-$FpcalcVersion-windows-x86_64.zip" `
  -FileName $ArchiveFile
VerifyHash -FileName $ArchiveFile -Sha256Sum $FpcalcSha256Sum
Expand-Archive -Path $ArchiveFile -DestinationPath .\build\fpcalc -Force
Copy-Item .\build\fpcalc\chromaprint-fpcalc-$FpcalcVersion-windows-x86_64\fpcalc.exe .

$ArchiveFile = ".\build\abz.zip"
Write-Output "Downloading AcousticBrainz extractor $AbextractorVersion to $ArchiveFile..."
DownloadFile -Url "https://ftp.acousticbrainz.org/pub/acousticbrainz/essentia-extractor-$AbextractorVersion-win-i686.zip" `
  -FileName $ArchiveFile
VerifyHash -FileName $ArchiveFile -Sha256Sum $AbextractorSha256Sum
Expand-Archive -Path $ArchiveFile -DestinationPath .\build\abz -Force
Copy-Item .\build\abz\streaming_extractor_music.exe .