.. _build-windows:


Building on Windows
###################

This page explains the process of building `MusicBrainz Picard`_ and
the installer for Windows. It only works for Picard 1.2 and newer,
which no longer supports AmpliFIND.



Requirements
============



Python 2.7.x
~~~~~~~~~~~~


+ `http://python.org/download/`_
+ Download and install "Python 2.7.x Windows Installer"
+ Add C:\Python27 to %PATH%




PyQt 4.10.x
~~~~~~~~~~~


+ `http://www.riverbankcomputing.co.uk/software/pyqt/download`_
+ Download and install "PyQt4-4.10.x-gpl-Py2.7-Qt4.8.x-x32.exe"




libdiscid
~~~~~~~~~


+ `http://musicbrainz.org/doc/libdiscid`_
+ Download "libdiscid-0.6.1-win32.zip" and put "discid.dll" in your
  Windows\System32 folder




Pip for Windows
~~~~~~~~~~~~~~~


+ `https://sites.google.com/site/pydatalog/python/pip-for-windows`_
+ Download to a location you find again (no installation)
+ in Pip_Win:

    + `pip install mutagen` for Mutagen (1.22 tested)
    + `pip install discid` for python-discid (1.1.x tested)





gettext
~~~~~~~


+ `http://gnuwin32.sourceforge.net/packages/gettext.htm`_
+ Add the gettext folder to %PATH% (normally C:\Programs\GnuWin32\bin)




Visual C++ 2008 Express
~~~~~~~~~~~~~~~~~~~~~~~


+ `http://go.microsoft.com/?linkid=7729279`_
+ Download and install "vcsetup.exe"




Chromaprint
~~~~~~~~~~~


+ `http://acoustid.org/chromaprint`_
+ Download "chromaprint-fpcalc-1.1-win-i86.zip" and put "fpcalc.exe"
  to the Picard source code directory




Running Picard From Sources
===========================

Before you can run Picard from sources, you need to build the C
extension. Start the VS console using "Visual Studio 2008 Command
Prompt", go to the source directory and run these commands:


::


            python setup.py build_ext -i
            python setup.py build_locales -i


After you have done this, you can run Picard directly from the sources
using:


::


            python tagger.py




Building the Installer
======================

To build the installer executable you need additional Tools:



py2exe 0.6.9
~~~~~~~~~~~~


+ `http://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/`_
+ Download and install "py2exe-0.6.9.win32-py2.7.exe"




NSIS 2.46
~~~~~~~~~


+ `http://nsis.sourceforge.net/Download`_
+ Download and install "nsis-2.46-setup.exe"


Then you need to copy msvcr90.dll and msvcp90.dll from "C:\Program
Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT" to
the source code directory, so that py2exe can find them. You also need
copy discid.dll (libdiscid) to the picard source.

Then you can build the installer using this command:


::


            python setup.py bdist_nsis


The setup is installer\picard-setup-1.x.exe and an executable for your
system is dist\picard.exe, which you can use to create a desktop
shortcut.



Known Issues
============

It is possible that the resulting picard.exe does not show the proper
file icon. This is probably a bug of py2exe on Vista. You can fix the
icon with the tool `Resource Hacker`_ or any other tool, that can edit
the resources in executables.




.. _http://acoustid.org/chromaprint: http://acoustid.org/chromaprint
.. _http://gnuwin32.sourceforge.net/packages/gettext.htm: http://gnuwin32.sourceforge.net/packages/gettext.htm
.. _http://go.microsoft.com/?linkid=7729279: http://go.microsoft.com/?linkid=7729279
.. _http://musicbrainz.org/doc/libdiscid: http://musicbrainz.org/doc/libdiscid
.. _http://nsis.sourceforge.net/Download: http://nsis.sourceforge.net/Download
.. _http://python.org/download/: http://python.org/download/
.. _http://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/: http://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/
.. _https://sites.google.com/site/pydatalog/python/pip-for-windows: https://sites.google.com/site/pydatalog/python/pip-for-windows
.. _http://www.riverbankcomputing.co.uk/software/pyqt/download: http://www.riverbankcomputing.co.uk/software/pyqt/download
.. _MusicBrainz Picard: http://picard.musicbrainz.org/
.. _Resource Hacker: http://angusj.com/resourcehacker/


