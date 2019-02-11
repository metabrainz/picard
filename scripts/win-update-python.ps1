$CurrentVersion = python -c "import sys; print('%s.%s.%s' % sys.version_info[0:3])"
Write-Output "Python installed: $CurrentVersion, wanted: $env:PYTHON_VERSION"

if ($CurrentVersion -ne $env:PYTHON_VERSION) {
  $InstallerUrl = 'https://www.python.org/ftp/python/' + $env:PYTHON_VERSION + '/python-' + $env:PYTHON_VERSION + '-amd64.exe'
  Write-Output "Downloading and installing $InstallerUrl..."
  (new-object net.webclient).DownloadFile($InstallerUrl, 'python-amd64.exe')
  python-amd64.exe /quiet InstallAllUsers=1 TargetDir=%PYTHON% Include_doc=0 Include_tcltk=0 Include_test=0
  python -m ensurepip
}

python --version
pip3 --version
