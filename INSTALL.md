MusicBrainz Picard Installation
===============================

Dependencies
------------

Before installing Picard from source, you need to check you have the following dependencies installed.

Required:

* [Python 3.6 or newer](http://python.org/download)
* [PyQt 5.10 or newer](http://www.riverbankcomputing.co.uk/software/pyqt/download)
* [Mutagen 1.37 or newer](https://bitbucket.org/lazka/mutagen/downloads)
* [python-dateutil](https://dateutil.readthedocs.io/en/stable/)
* gettext:
  * [Windows](https://mlocati.github.io/articles/gettext-iconv-windows.html)
* a compiler
  * Windows should work with [Visual C++ 2008 Express](http://go.microsoft.com/?linkid=7729279)

Optional but recommended:

* [chromaprint](http://acoustid.org/chromaprint)
  * Required for fingerprinting (scanning) files
* [python-discid](https://python-discid.readthedocs.org/) or [python-libdiscid](https://pypi.org/project/python-libdiscid/)
  * Required for CD lookups.
  * Depends on [libdiscid](http://musicbrainz.org/doc/libdiscid)
   Note: Due to slowdowns in reading the CD TOC, using libdiscid versions
   0.3.0 - 0.4.1 is not recommended.
* [python-markdown](https://python-markdown.github.io/install/)
  * Required for the complete scripting documentation

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

If you want to run Picard from the source directory without installing, you
need to build the C extensions and locales manually:

    python3 setup.py build
    python3 setup.py build_ext -i
    python3 setup.py build_locales -i

And to start Picard use:

    python3 tagger.py


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
