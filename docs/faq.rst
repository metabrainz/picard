.. _picard-faq:

FAQ
###



Using Picard
============



How do I tag files with Picard?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is a separate page that :ref:`explains the tagging process <guide>`.



The green "Tagger" icon disappeared from MusicBrainz.org, how do I get it back?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This icon shows up when a manual lookup is performed via Picard (using
the bottom "Lookup" button).

Alternatively the parameter `?tport=8000` can be added to the end of
almost any MusicBrainz URL and the green tagger icons will continue to
show up from then on.



I'm using Windows Vista or Windows 7, why doesn't drag and drop work?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's a known problem when running Picard from the installer.
Restarting Picard should fix it.

For the technically minded, this is because the installer runs with
elevated privileges; but your Windows Explorer does not.



I'm using OS X, where are my network folders or drives?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These should show up OK in the add file and add folder dialogs, but
they aren't visible by default in the file browser pane. If you want
to see them in the file browser pane, right click in the pane and
select "show hidden files". They should then be visible in the
/Volumes folder.



File Formats
============



What formats does Picard support?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Picard supports MP3, Ogg Vorbis, FLAC, MP4 (AAC), Musepack, WavPack,
Speex, The True Audio and Windows Media Audio.

WAVs cannot be tagged due to the lack of a standard for doing so,
however, they can be fingerprinted and renamed.



What formats will Picard support?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Picard is intended to eventually support all formats (including
fingerprinting), but this is a complex (arguably never-ending)
process, and will take some time.



Which tags can Picard write to my files?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See :ref:`Picard Tags <picard-tags>` for information on which 
MusicBrainz fields get written to tags by Picard. 
:ref:`Picard Tag Mapping <mappings>` contains more
technical information on how these are further mapped into each tag
format.



How to I edit several tags at once? Why is it not easier do so?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please realise that Picard is not designed as a general purpose tag
editor. Its primary goal is to get community-maintained MusicBrainz
data into your tags. Some secondary goals include


+ allowing rule-based (:ref:`scripts <picard-scripting>`, `plugins`_)
  customisation of that data
+ encouraging users to create an account, fix and update data via the
  MusicBrainz website, thus sharing their work with the rest of the
  community - rather than fixing their tags locally.


To that end, Picard is likely to never have as much development focus
on manual bulk editing of tags as other general purpose editors (e.g.
`Jaikoz`_, `Mp3tag`_, `foobar2000`_ or even many library managers such
as iTunes, Windows Media Player, MediaMonkey). That doesn't mean that
the team won't welcome patches in this area!

Having said all this, it is still possible in Picard:


#. Click and select several files with CTRL or SHIFT
#. Right click on one of them, then click **Details...**
#. On the popup dialog you can see the tags, with entries that denote
   where tags are different across files. You can edit or add new tags
   here.
#. On exiting the dialog, you have changed the tags in memory. You
   need to click Save in order to persist these changes to your files.


This process should work in both panes.



I am using Fedora, why doesn't acoustic fingerprinting work?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Acoustic fingerprinting in Picard uses a tool called `fpcalc`, which
is not available in Fedora. You can get it by installing the
`chromaprint-tools` package from the `RPM Fusion`_ repository. This
functionality is not contained in the main Fedora `picard` package
because it requires the `ffmpeg` package which `cannot be distributed
by Fedora`_. After `enabling`_ the "rpmfusion-free" RPM Fusion
repository, install the package using (as root):


::

    yum install chromaprint-tools




Configuration
=============



I tagged a file in Picard, but iTunes is not seeing the tags!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Firstly, you need to force iTunes to re-read the information from your
tags and update its library.
This is discussed in the `iTunes Guide`_.

Additionally, iTunes has a known bug in its ID3v2.4 implementation,
which makes it unable to read such tags if they contain also embedded
cover art. As a work-around, you can configure Picard to write ID3v2.3
tags.



My tags are truncated to 30 characters in Windows Media Player!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prior to version 0.14, Picard's default settings were to write ID3v2.4
and ID3v1 tags to files. WMP can't read ID3v2.4, so it falls back to
ID3v1 which has a limitation of 30 characters per title. To solve this
on versions prior to 0.14, configure Picard to write ID3v2.3 tags
instead.

Starting with version 0.14, the default settings have been changed to
ID3v2.3 and this should no longer be an issue.



How do I tell Picard which browser to use?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On Windows, GNOME and KDE, Picard uses the standard browser for these
systems. On other systems, you can use the `BROWSER` environment
variable.

For example:


::

    export BROWSER="firefox '%s' &"


Another approach that works in some GNU/Linux systems is the following
command:


::

    sudo update-alternatives --config x-www-browser


This should present you with a list of existing browsers in your
system, allowing you to select the one to be the default.




.. _cannot be distributed by Fedora: http://fedoraproject.org/wiki/Forbidden_items
.. _enabling: http://rpmfusion.org/Configuration
.. _foobar2000: http://www.foobar2000.org/
.. _iTunes Guide: http://musicbrainz.org/doc/iTunes_Guide
.. _Jaikoz: http://musicbrainz.org/doc/Jaikoz
.. _Mp3tag: http://www.mp3tag.de/en/
.. _Picard Forum: http://forums.musicbrainz.org/viewforum.php?id=2
.. _plugins: http://picard.musicbrainz.org/plugins/
.. _RPM Fusion: http://rpmfusion.org/


