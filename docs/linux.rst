Installing Picard on Linux
##########################

Setup and install guide for `Picard`_ under Linux. If you don't want
to install third party binary packages, the source is available
from `Picard Official Website <PicardDownloadSource>`_.



Arch Linux
==========

Arch Linux has the picard package in the community repository, simply
run:


::

    sudo pacman -S picard


`wiki.archlinux`_ tells you how to enable the community repository, if
you haven't done this already.



Debian
======

Picard 0.11-2.1 is available in the Debian Repositories for `Stable
(Squeeze)`_.

**Note:** versions prior to 0.15 do not support `NGS`_.

Picard 1.0-1 is available in the Debian Repositories for `Testing
(Wheezy)`_. It may be possible to run a more up-to-date version of
Picard on Debian Stable using apt-pinning.

There is also a .deb of Version 0.12.1-1 for Debian Lenny build by
kaiserbert available for download `here <DebianLennyDeb>`_.
To install the .deb just download and type:

::

    sudo dpkg -i picard_0.12.1-1_i386.deb

You can find a `thread`_ about the .deb for Lenny in the forum.



Fedora 7, 8 and higher
======================

Picard is now in the `official Fedora package collection`_.

Since dependent packages PyQt4 and libdiscid are now also available in
Fedora. Just install with yum:


::

    yum install picard


Currently these packages do not have support for acoustic
fingerprinting because that depends on ffmpeg which isn't available in
Fedora due to patent issues in ffmpeg.

ffmpeg is available from the livna rpm repository. It is necessary to
install the packages ffmpeg and ffmpeg-devel, and rebuild picard from
the source RPM in order to enable PUID generation within picard on
Fedora.



Gentoo
======

Picard Qt is now included in Gentoo Portage. To install Picard, simply
run:


::

    emerge --sync emerge picard


Note that you should enable the USE flag "ffmpeg" if you want
acoustinc fingerprinting, and "cdaudio" if you want to recognize CDs
from your drive.



Mandriva
========

Picard is available in the Mandriva development version Cooker in the
contribs repository.

Cooker users can simply install it by running

::

    urpmi picard



or by selecting it in rpmdrake.



SUSE / OpenSUSE
===============

RPM builds for various SUSE versions can be found as well as 1-click
installed in the `OpenSUSE Software directory`_.

Select the correct one for your OpenSUSE version.

This version does not automatically install optional things like PUID
support. If you want to ensure you've got full functionality, also
make sure RPMs for the following are installed:

libdiscid0 python-mutagen python-qt4 libofa ffmpeg

libdiscid0 is available from the same repository as Picard linked
above.

The other RPMs are available from SUSE default main repository, as
well as `Packman's repository`_.
Just make sure you have Packman's repo set up and search for those
5 RPMs to ensure they are installed.



Ubuntu
======

Available in `Ubuntu's universe repository`_ since Feisty. To install
it run this command or use `Synaptic`_ instead.

::

    sudo apt-get install picard



Latest official packages also available via the main `Launchpad`_
page.

Daily builds available at `MusicBrainz daily PPA <UbuntuDaily>`_.



.. _DebianLennyDeb: http://users.musicbrainz.org/~outsidecontext/picard/picard_0.12.1-1_i386.deb
.. _Launchpad: https://launchpad.net/picard
.. _NGS: https://musicbrainz.org/doc/Server_Release_Notes/20110516
.. _official Fedora package collection: https://admin.fedoraproject.org/pkgdb/packages/name/picard
.. _OpenSuse Software Directory: http://software.opensuse.org/search?p=1&q=picard
.. _Packman's repository: http://packman.links2linux.org
.. _PicardDownloadSource: http://picard.musicbrainz.org/downloads/#source
.. _Picard: http://picard.musicbrainz.org/
.. _Stable (Squeeze): http://packages.debian.org/stable/picard
.. _Synaptic: https://help.ubuntu.com/community/SynapticHowto
.. _Testing (Wheezy): http://packages.debian.org/wheezy/picard
.. _thread: http://forums.musicbrainz.org/viewtopic.php?pid=10501#p10501
.. _UbuntuDaily: https://launchpad.net/~musicbrainz-developers/+archive/ubuntu/daily
.. _Ubuntu's universe repository: http://packages.ubuntu.com/search?keywords=picard&searchon=names&exact=1&suite=all&section=all
.. _wiki.archlinux: http://wiki.archlinux.org/index.php/Pacman#Repositories


