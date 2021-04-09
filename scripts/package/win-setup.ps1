Param(
  [Parameter(Mandatory=$true)]
  [String]
  $DiscidVersion,
  [Parameter(Mandatory=$true)]
  [String]
  $FpcalVersion
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

New-Item -Name .\build -ItemType Directory -ErrorAction Ignore

$ArchiveFile = ".\build\libdiscid.zip"
Write-Output "Downloading libdiscid $DiscidVersion to $ArchiveFile..."
DownloadFile -Url "https://github.com/metabrainz/libdiscid/releases/download/v$DiscidVersion/libdiscid-$DiscidVersion-win64.zip" `
  -FileName $ArchiveFile
Expand-Archive -Path $ArchiveFile -DestinationPath .\build\libdiscid -Force
Copy-Item .\build\libdiscid\discid.dll .

$ArchiveFile = ".\build\fpcalc.zip"
Write-Output "Downloading chromaprint-fpcalc $FpcalVersion to $ArchiveFile..."
DownloadFile -Url "https://github.com/acoustid/chromaprint/releases/download/v$FpcalVersion/chromaprint-fpcalc-$FpcalVersion-windows-x86_64.zip" `
    -FileName $ArchiveFile
Expand-Archive -Path $ArchiveFile -DestinationPath .\build\fpcalc -Force
Copy-Item .\build\fpcalc\chromaprint-fpcalc-$FpcalVersion-windows-x86_64\fpcalc.exe .
