# Apply fixes to the build result

Param(
  [ValidateScript({Test-Path $_ -PathType Container})]
  [String]
  $Path
)

$ErrorActionPreference = 'Stop'

$InternalPath = (Join-Path -Path $Path -ChildPath _internal)
# Move all Qt6 DLLs into the main folder to avoid conflicts with system wide
# versions of those dependencies. Since some version PyInstaller tries to
# maintain the file hierarchy of imported modules, but this easily breaks
# DLL loading on Windows.
# Workaround for https://tickets.metabrainz.org/browse/PICARD-2736
$Qt6Dir = (Join-Path -Path $InternalPath -ChildPath PyQt6\Qt6)
Move-Item -Path (Join-Path -Path $Qt6Dir -ChildPath bin\*.dll) -Destination $Path -Force
Remove-Item -Path (Join-Path -Path $Qt6Dir -ChildPath bin)
