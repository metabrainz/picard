MusicBrainz Picard Installation
===============================

Dependencies
------------

Before installing Picard from source, you need to check you have the following dependencies installed.

Required:

* [Python 3.7 or newer](https://python.org/download)
* [PyQt 5.11 or newer](https://riverbankcomputing.com/software/pyqt/download)
* [Mutagen 1.37 or newer](https://mutagen.readthedocs.io/)
* [PyYAML 5.1 or newer](https://pyyaml.org/)
* [python-dateutil](https://dateutil.readthedocs.io/en/stable/)
* gettext:
  * [Windows](https://mlocati.github.io/articles/gettext-iconv-windows.html)
* a compiler
  * Windows should work with [Visual Studio Community 2019](https://aka.ms/vs/16/release/vs_community.exe)

Optional but recommended:

* [chromaprint](https://acoustid.org/chromaprint)
  * Required for fingerprinting (scanning) files
* [python-discid](https://python-discid.readthedocs.org/) or [python-libdiscid](https://pypi.org/project/python-libdiscid/)
  * Required for CD lookups.
  * Depends on [libdiscid](https://musicbrainz.org/doc/libdiscid)
   Note: Due to slowdowns in reading the CD TOC, using libdiscid versions
   0.3.0 - 0.4.1 is not recommended.
* [python-markdown](https://python-markdown.github.io/install/)
  * Required for the complete scripting documentation
* [PyJWT 1.7 or newer](https://pyjwt.readthedocs.io/)
  * Required for the add cluster as release / add file as recording functionality
* [charset_normalizer](https://pypi.org/project/charset-normalizer/) or [chardet](https://pypi.org/project/chardet/)
  * Required for character encoding detection in CD ripping log files

We recommend you use [pip](https://pip.pypa.io/en/stable/) to install the Python
dependencies:

Run the following command to install PyQt5, Mutagen and discid:

    pip3 install -r requirements.txt

The binaries for Python, GetText (`msgfmt`), `fpcalc` and `discid.dll` have to be
in the `%PATH%` on Windows.


Installation using pip
----------------------

The recommended way to install Picard from source is using pip. After installing
the dependencies, you can install Picard as a pip package by running:

    pip3 install .

To start Picard now you can use:

    picard

To uninstall Picard run:

    pip3 uninstall picard


Installation using setup.py
---------------------------

You can also install Picard with `setup.py` by running:

    sudo python3 setup.py install

This will automatically build and install all required Python modules.
On Windows you need to have Administrator rights, but don't put `sudo`
in front of the command.

To start Picard now you can use:

    picard

If you want to be able to easily uninstall Picard again, run `setup.py`
with the `--record installed-files.txt` command line argument. This will record
all files generated during installation into the file `installed-files.txt`.

    sudo python3 setup.py install --record installed-files.txt

To uninstall Picard again simply remove all the files listed in
`installed-files.txt`, e.g. by running:

    rm -vI $(cat installed-files.txt)


Running From the Source Tree
----------------------------

If you want to run Picard from the source directory without installing,
or want to develop, you need to follow those steps.

On Debian-based systems:

    apt install python3-pyqt5 python3-venv python3-dev

For discid support (optional):

    apt install libdiscid0

For embedded multimedia player support (optional):

    apt install python3-pyqt5.qtmultimedia libqt5multimedia5-plugins

For other distributions, check your distribution's documentation
on how to install the packages for Qt5, PyQt5, Python3 C headers,
and Python3 venv.

At top of source directory, create a .venv directory:

    python3 -m venv --system-site-packages .venv

Activate it:

    . .venv/bin/activate

Install requirements (here we also install build & dev requirements):

    pip install -r requirements.txt -r requirements-build.txt -r requirements-dev.txt

You then need to build the C extensions and locales manually.
C extension will require header file `Python.h`.

Then you can build Picard dependencies:

    python3 setup.py build
    python3 setup.py build_ext -i
    python3 setup.py build_locales -i

And to start Picard use:

    python3 tagger.py

Or, to enable debug mode:

    python3 tagger.py -d


Running the Test Suite
----------------------

To run the included tests, follow the instructions for "Running From
the Source Tree".  Afterward you can run the tests using setup.py:

    python3 setup.py test


Packaging
---------

Picard supports packaging binaries and uploading them to PyPi.

To submit a package run:

    python3 setup.py sdist
    twine upload dist/*


Code Signatures
---------------

The official software packages of MusicBrainz Picard for macOS and Windows as
well as the official source archives are all digitally signed.

If you are packaging Picard for an operating system (e.g. a Linux distribution)
we recommend that you use the source archives from the
[official file server](https://data.musicbrainz.org/pub/musicbrainz/picard/).
The source archives are named `picard-x.y.z.tar.gz` and there is a corresponding
GPG signature file `picard-x.y.z.tar.gz.asc` signed with the GPG key listed
below.

You can verify the signature with e.g.:

    gpg --verify picard-2.9.tar.gz.asc

Make sure the key fingerprint in the output matches the fingerprint of the
GPG key below.

The signing certificates and keys currently in use are:

| Certificate          | Expiration | Fingerprint                              |
|----------------------|------------|------------------------------------------|
| Windows Code Signing | 2024-10-25 | 4d0c868847e2a5e44ae734e1279a9c7007fd6d4c |
| Apple Code Signing   | 2027-02-01 | deb351206f7dc9361e1cf3d864edce98a8d3302d |
| MBP Developers GPG   | 2026-10-28 | [68990dd0b1edc129b856958167997e14d563da7c](https://keyserver.ubuntu.com/pks/lookup?op=vindex&search=0x67997e14d563da7c) |
