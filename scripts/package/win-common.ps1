# Common functions for Windows packaging scripts

Param(
  [ValidateScript({ (Test-Path $_ -PathType Leaf) -or (-not $_) })]
  [String]
  $CertificateFile,
  [SecureString]
  $CertificatePassword
)

# RFC 3161 timestamp server for code signing
$TimeStampServer = 'http://ts.ssl.com'

Function CodeSignBinary {
  Param(
    [ValidateScript({Test-Path $_ -PathType Leaf})]
    [String]
    $BinaryPath
  )
  If ($CertificateFile) {
    SignTool sign /v /fd SHA256 /tr "$TimeStampServer" /td sha256 `
      /f "$CertificateFile" /p (ConvertFrom-SecureString -AsPlainText $CertificatePassword) `
      $BinaryPath
    ThrowOnExeError "SignTool failed"
  } Else {
    Write-Output "Skip signing $BinaryPath"
  }
}

Function ThrowOnExeError {
  Param( [String]$Message )
  If ($LastExitCode -ne 0) {
    Throw $Message
  }
}

Function FinalizePackage {
  Param(
    [ValidateScript({Test-Path $_ -PathType Container})]
    [String]
    $Path
  )

  $InternalPath = (Join-Path -Path $Path -ChildPath _internal)

  CodeSignBinary -BinaryPath (Join-Path -Path $Path -ChildPath picard.exe) -ErrorAction Stop
  CodeSignBinary -BinaryPath (Join-Path -Path $InternalPath -ChildPath fpcalc.exe) -ErrorAction Stop
  CodeSignBinary -BinaryPath (Join-Path -Path $InternalPath -ChildPath discid.dll) -ErrorAction Stop
}

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
