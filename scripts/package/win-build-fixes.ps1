# Apply fixes to the build result

Param(
  [ValidateScript({Test-Path $_ -PathType Container})]
  [String]
  $Path
)

$ErrorActionPreference = 'Stop'

# Move all Qt5 DLLs into the main folder to avoid conflicts with system wide
# versions of those dependencies. Since some version PyInstaller tries to
# maintain the file hierarchy of imported modules, but this easily breaks
# DLL loading on Windows.
# Workaround for https://tickets.metabrainz.org/browse/PICARD-2736
$Qt5BinDir = (Join-Path -Path $Path -ChildPath PyQt5\Qt5\bin)
Move-Item -Path (Join-Path -Path $Qt5BinDir -ChildPath *.dll) -Destination $Path -Force
Remove-Item -Path $Qt5BinDir
