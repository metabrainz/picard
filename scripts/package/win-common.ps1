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

  # Move all Qt5 DLLs into the main folder to avoid conflicts with system wide
  # versions of those dependencies. Since some version PyInstaller tries to
  # maintain the file hierarchy of imported modules, but this easily breaks
  # DLL loading on Windows.
  # Workaround for https://tickets.metabrainz.org/browse/PICARD-2736
  $Qt5BinDir = (Join-Path $Path PyQt5 Qt5 bin)
  Move-Item (Join-Path $Qt5BinDir *.dll) $Path -Force
  Remove-Item $Qt5BinDir
}
