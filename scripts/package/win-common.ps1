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

  # Workaround for https://github.com/pyinstaller/pyinstaller/issues/4429
  $OldTRanslationsPath = (Join-Path $Path PyQt5\translations)
  If (Test-Path $OldTRanslationsPath -PathType Container) {
    Move-Item -Path $OldTRanslationsPath -Destination (Join-Path $Path PyQt5\Qt)
  }

  # Delete unused files
  Remove-Item -Path (Join-Path $Path libcrypto-1_1.dll)
  Remove-Item -Path (Join-Path $Path libssl-1_1.dll)
}
