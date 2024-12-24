# Common functions for Windows packaging scripts

Param(
  [ValidateScript({ (Test-Path $_ -PathType Leaf) -or (-not $_) })]
  [String]
  $CertificateFile,
  [SecureString]
  $CertificatePassword
)

Function DownloadFile {
  Param(
    [Parameter(Mandatory = $true)]
    [String]
    $FileName,
    [Parameter(Mandatory = $true)]
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
