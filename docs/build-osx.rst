.. _build-osx:


Building on OSX
###############

This guide details the process I've used to build Tiger-compatible
Picard app bundles on OS X. There are many ways to achieve this, but
I've found these steps to be the simplest and most compatible after
much trial and error.

This guide was tested in a VM running Leopard. If you're using
anything above Snow Leopard (Lion, Mountain Lion) you won't be able to
install XCode 3, so this guide won't work.

**Last updated** on 2012-06-03 for Picard 1.0.



Avoid MacPorts
==============

There are a lot of architecture issues in MacPorts that took days to
debug. After working around those, Qt4 had broken functionality, such
as drag and drop from Finder not working. Qt4 takes an entire day to
build on my machine, whereas the precompiled Qt package from Nokia
works just fine. The rest of the dependencies will be installed
manually to /usr/local.



Prerequisites
=============


+ XCode 3.2.6, with the 10.4 SDK installed at
  /Developer/SDKs/MacOSX10.4u.sdk (it's a selectable option in the
  installer).
+ Python 2.7.3

  Since we want compatibility with Tiger/i386, make sure
  to install this one: `python-2.7.3-macosx10.3.dmg`_. Use the provided
  Update Shell Profile.command to make this your default Python. Note:
  this is required. You can't use the system Python that comes with OS
  X! py2app won't allow you to build standalone app bundles with it.
+ Qt 4.7.3

  Install this one: `qt-mac-carbon-opensource-4.7.3.dmg`_.
  Qt 4.8 and up no longer support 10.4/Carbon.




Set up your environment
=======================

Make sure /usr/local/bin is in your PATH, and have the following
variables set in your .profile or .bash_profile (or do it manually):


::


  export CFLAGS="-arch i386 -isysroot /Developer/SDKs/MacOSX10.4u.sdk -mmacosx-version-min=10.4 -I/usr/local/include"
  export CXXFLAGS="$CFLAGS"
  export LDFLAGS="-arch i386 -Xlinker -headerpad_max_install_names -L/usr/local/lib"
  export MACOSX_DEPLOYMENT_TARGET="10.4"


Make sure you're using gcc 4.0.2. On Snow Leopard, I had to change the
symlinks, because setting CC= didn't work for some dependencies. (`I
did this`_, but for 4.0 instead of 4.2.)



Dependencies
============

Now you have to install a bunch of dependencies by hand. Or, that's
what you would have to do if I hadn't written this super-convenient
(hacked-together) script for you: `build-deps.sh`_. `chmod +x` and run
from an empty directory.

I have no doubt the script will break somewhere for someone—help me
fix it.:)

To enable `AcoustID`_ fingerprinting in Picard, you also need the
fpcalc binary. Download that from `here`_ and place it in
/usr/local/bin.

Finally, you'll need two Python modules: py2app and mutagen. Install
them manually or just use easy_install. Be sure to install them for
the correct Python version!



Building Picard
===============

Create the file build.cfg in the source directory. Mine looks like
this:


::


    [libofa]
    libs = -arch i386 -L/usr/local/lib -lofa
    cflags = -arch i386 -I/usr/local/include

    [avcodec]
    libs = -arch i386 -L/usr/local/lib -lavcodec -lavformat -lavutil -lvorbis -lvorbisenc -logg -lmp3lame -lfaac
    cflags = -arch i386 -I/usr/local/include

    [build]
    with-directshow = False
    with-avcodec = True
    with-libofa = True


Now we should be able to build a Picard app bundle. This requires a
few commands, so I use a bash script to run them all:


::


    #!/bin/bash
    rm -rf build dist
    python setup.py clean
    python setup.py build_ext -i
    python setup.py py2app
    cd dist
    # Strip any non-i386 code from the app bundle
    ditto -rsrc --arch i386 MusicBrainz\ Picard.app MusicBrainz\ Picard.tmp
    rm -r MusicBrainz\ Picard.app
    mv MusicBrainz\ Picard.tmp MusicBrainz\ Picard.app


If all goes well, you'll end up with an app bundle in the dist
directory. We're done! Yay!



.. _AcoustID: http://musicbrainz.org/doc/AcoustID
.. _build-deps.sh: http://users.musicbrainz.org/bitmap/build-deps.sh
.. _here: https://github.com/downloads/lalinsky/chromaprint/chromaprint-fpcalc-0.6-osx-i386.tar.gz
.. _I did this: http://stackoverflow.com/questions/1165361/setting-gcc-4-2-as-the-default-compiler-on-mac-os-x-leopard
.. _python-2.7.3-macosx10.3.dmg: http://www.python.org/ftp/python/2.7.3/python-2.7.3-macosx10.3.dmg
.. _qt-mac-carbon-opensource-4.7.3.dmg: http://download.qt-project.org/archive/qt/4.7/qt-mac-carbon-opensource-4.7.3.dmg


