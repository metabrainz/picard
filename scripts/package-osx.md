# Build Mac OS X packages

This is tested on Mac OS X 10.7 with Xcode 4.6.3 installed. You need to download the Xcode package (file named `xcode4630916281a.dmg`) from the Apple Developer site. Xcode 4.6.3 is the last version that works on OS X 10.7.

Download the required packages:

    cd ~/Downloads
    curl -L -O https://download.qt.io/archive/qt/4.8/4.8.5/qt-mac-opensource-4.8.5.dmg
    curl -L -O https://sourceforge.net/projects/pyqt/files/sip/sip-4.19/sip-4.19.tar.gz
    curl -L -O https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.12/PyQt4_gpl_mac-4.12.tar.gz

Open the Qt DMG image, click on `Qt.mpkg` and proceed with the install using the defaults for everything.

Build PyObjC:

    pip install pyobjc-framework-Cocoa

Build SIP:

    tar -C /tmp -xf ~/Downloads/sip-4.19.tar.gz
    cd /tmp/sip-4.19
    python configure.py --arch x86_64
    make
    sudo make install

Build PyQt4:

    tar -C /tmp -xf ~/Downloads/PyQt4_gpl_mac-4.12.tar.gz
    cd /tmp/PyQt4_gpl_mac-4.12
    python configure.py --use-arch x86_64
    make
    sudo make install

Build Picard:

    cd /tmp
    git clone https://github.com/metabrainz/picard
    cd picard
    bash scripts/package-osx.sh
