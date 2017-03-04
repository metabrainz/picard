# Build Mac OS X packages

This setup is tested on Mac OS X 10.7 (Lion). First you need to download Xcode and the command line tools for Xcode.
Xcode 4.6.3 is the latest version supported on 10.7. You can download both packages from the Apple Developer site:

https://developer.apple.com/download/more/

Download and install Python 2.7.x and Qt 4.x to the default locations:

    curl -L -O https://www.python.org/ftp/python/2.7.13/python-2.7.13-macosx10.6.pkg
    curl -L -O https://download.qt.io/archive/qt/4.8/4.8.5/qt-mac-opensource-4.8.5.dmg

Install virtualenv:

    /Library/Frameworks/Python.framework/Versions/2.7/bin/pip install virtualenv

Install PyObjC:

    /Library/Frameworks/Python.framework/Versions/2.7/bin/pip install pyobjc-framework-Cocoa

Install SIP:

    curl -L -O https://sourceforge.net/projects/pyqt/files/sip/sip-4.19/sip-4.19.tar.gz
    tar -xf sip-4.19.tar.gz
    cd sip-4.19
    /Library/Frameworks/Python.framework/Versions/2.7/bin/python configure.py --arch x86_64 --deployment-target=10.6
    make
    sudo make install

Install PyQt4:

    curl -L -O https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.12/PyQt4_gpl_mac-4.12.tar.gz
    tar -xf PyQt4_gpl_mac-4.12.tar.gz
    cd PyQt4_gpl_mac-4.12
    /Library/Frameworks/Python.framework/Versions/2.7/bin/python configure.py --use-arch x86_64
    make
    sudo make install

Install gettext:

    curl -L -O http://ftp.gnu.org/pub/gnu/gettext/gettext-0.19.8.1.tar.gz
    tar -xf gettext-0.19.8.1.tar.gz
    cd gettext-0.19.8.1
    ./configure
    make
    sudo make install

Build Picard:

    cd /tmp
    git clone https://github.com/metabrainz/picard
    cd picard
    export PATH=/Library/Frameworks/Python.framework/Versions/2.7/bin:$PATH
    bash scripts/package-osx.sh
