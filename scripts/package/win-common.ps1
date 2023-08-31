# Common functions for Windows packaging scripts

Param(
  [System.Security.Cryptography.X509Certificates.X509Certificate]
  $Certificate
)

Function CodeSignBinary {
  Param(
    [ValidateScript({Test-Path $_ -PathType Leaf})]
    [String]
    $BinaryPath
  )
  If ($Certificate) {
    Set-AuthenticodeSignature -FilePath $BinaryPath -Certificate $Certificate `
      -ErrorAction Stop
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

  CodeSignBinary (Join-Path $Path picard.exe)
  CodeSignBinary (Join-Path $Path fpcalc.exe)
  CodeSignBinary (Join-Path $Path discid.dll)
}
