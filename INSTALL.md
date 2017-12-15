MusicBrainz Picard Installation
===============================

Dependencies
------------

Before installing Picard, you need to have these:

* [Python 3.5 or newer](http://python.org/download)

* [PyQt 5.7.1 or newer](http://www.riverbankcomputing.co.uk/software/pyqt/download)

* [Mutagen 1.37 or newer](https://bitbucket.org/lazka/mutagen/downloads)

* gettext:
  * [Windows](http://gnuwin32.sourceforge.net/packages/gettext.htm)

* a compiler
  * Windows should work with [Visual C++ 2008 Express](http://go.microsoft.com/?linkid=7729279)

* [chromaprint](http://acoustid.org/chromaprint) (optional)
  For fingerprinting (scanning) files

* [python-discid or python-libdiscid](https://python-discid.readthedocs.org/) (optional)
  Required for CD lookups.
  Depends on [libdiscid](http://musicbrainz.org/doc/libdiscid)
  Due to slowdowns in reading the CD TOC, using libdiscid versions
  0.3.0 - 0.4.1 is not recommended.

We recommend you use [pip](https://pip.pypa.io/en/stable/) to install the Python
dependencies:

Run the following command to install PyQt5, Mutagen and discid:

    pip3 install -r requirements.txt

The binaries for Python, GetText (msgfmt), fpcalc and discid.dll have to be
in the %PATH% on Windows.


Installation
------------

After installing the dependencies, you can install Picard by running:

    sudo python3 setup.py install

This will automatically build and install all required Python modules.
On Windows you need to have Administrator rights, but don't put "sudo"
in front of the command.
To start Picard now you can use:

    picard


Running From the Source Tree
----------------------------

If you want to run Picard from the source directory without installing, you
need to build the C extensions and locales manually:

```python
python3 setup.py build_ext -i
python3 setup.py build_locales -i
```

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

    python setup.py sdist upload -r pypi
