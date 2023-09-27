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

  CodeSignBinary -BinaryPath (Join-Path -Path $Path -ChildPath picard.exe) -ErrorAction Stop
  CodeSignBinary -BinaryPath (Join-Path -Path $Path -ChildPath fpcalc.exe) -ErrorAction Stop
  CodeSignBinary -BinaryPath (Join-Path -Path $Path -ChildPath discid.dll) -ErrorAction Stop

  # Move all Qt6 DLLs into the main folder to avoid conflicts with system wide
  # versions of those dependencies. Since some version PyInstaller tries to
  # maintain the file hierarchy of imported modules, but this easily breaks
  # DLL loading on Windows.
  # Workaround for https://tickets.metabrainz.org/browse/PICARD-2736
  $QtBinDir = (Join-Path -Path $Path -ChildPath PyQt6\Qt6\bin)
  Move-Item -Path (Join-Path -Path $QtBinDir -ChildPath *.dll) -Destination $Path -Force
  Remove-Item -Path $QtBinDir

  # Mitigate libwebp vulnerability allowing for arbitrary code execution (CVE-2023-4863).
  # Disable the Qt webp imageformat plugin.
  Remove-Item -Path (Join-Path -Path $Path -ChildPath PyQt6\Qt6\plugins\imageformats\qwebp.dll)
}
