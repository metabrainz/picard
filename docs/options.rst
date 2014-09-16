.. _options:

Picard UI Options
#################



General
=======


+ **Server address:** The domain name for the MusicBrainz database
  server used by Picard to get details of your music. Default value:
  musicbrainz.org (for the main MusicBrainz server).
+ **Port:** The port number for the server. Default value: 80 (for the
  main MusicBrainz server).
+ **Username**: Your MusicBrainz website username, used to submit
  `acoustic fingerprints <AcoustID>`_, retrieve and save items to your collections
  and retrieve personal folksonomy tags.
+ **Password**: Your MusicBrainz website password.
+ **Automatically scan all new files:** Check this box if you want
  Picard to scan each music file you add and look for an `AcoustID`_
  fingerprint. This takes time, but may be helpful for you and
  MusicBrainz. Leave it unchecked if you don't want Picard to do this
  scan automatically. In any case, you can direct Picard to scan a
  particular music file at any time using the Scan button in the
  toolbar.




Metadata
========


+ **Translate artist names to this locale where possible:** When
  checked, Picard will see whether an artist has an `alias`_ for the
  selected locale. If it does, Picard will use that alias instead of the
  `artist name`_ when tagging. When "English" is the selected locale,
  the `artist sort name`_ (which is, by Style Guideline, stored in Latin
  script) is used as a fallback if there is no English alias.
+ **Use standardized artist names:** Check to only use standard
  `Artist`_ names, rather than `Artist Credits`_ which may differ
  slightly across tracks and releases. Note: If the "translate artist
  names" option above is also checked, it will override this option if a
  suitable alias is found.
+ **Convert Unicode punctuation characters to ASCII:** Converts
  Unicode punctuation characters in MusicBrainz data to ASCII for
  consistent use of punctuation in tags. For example, right single
  quotation marks (’) are converted to ASCII apostrophes ('), and
  horizontal ellipses (…) are converted to three full stops (.).
+ **Use release relationships:** Check to retrieve and write release-
  level relationships to your files, e.g. URLs, composer, lyricist,
  performer, conductor, DJ mixer, etc. (You must have this enabled to
  use Picard to retrieve cover art)
+ **Use track relationships:** Check to write track-level
  relationships to your files, e.g. composer, lyricist, performer,
  remixer, etc.
+ **Use folksonomy tags as genres:** Check to write MusicBrainz
  folksonomy tags as genres. (See options under "Folksonomy Tags")
+ **Various artists:** Choose how you want the 'Various Artists'
  artist spelled.
+ **Non-album tracks:** Choose how you want 'non-album tracks'
  (`Recordings`_ that do not belong to any `Release`_) to be grouped.




Preferred Releases
~~~~~~~~~~~~~~~~~~


+ **Preferred release types**: Adjust the sliders for various release
  types to tweak how likely Picard is to match a file or cluster to
  releases of various types. You can use this to decrease the likelihood
  of Picard matching a file or album to a Compilation or Live version,
  for example.



+ **Preferred release countries**: Add one or more countries into the
  list to make Picard prefer matching clusters/files to releases from
  the chosen countries. This list is also used to prioritise files in
  the "Other Releases" context menu.
+ **Preferred release formats**: Add one or more formats into the list
  to make Picard prefer matching clusters/files to releases of the
  specified format. This list is also used to prioritise files in the
  "Other Releases" context menu.




Folksonomy tags
~~~~~~~~~~~~~~~

The following settings are only applicable if you enable the use
folksonomy tags as genres option.


+ **Ignore tags:** Comma-separated list of tags to ignore when writing
  genres.
+ **Only use my tags:** Check to only write genres with tags that you
  personally have submitted to MusicBrainz. You'll need to set your
  username and password to use this feature.
+ **Minimal tag usage:** Choose how popular the tag must be before it
  is written by Picard. Default: 90%. Lowering the value here will lead
  to more tags in your files, but possibly less relevant tags.
+ **Maximum number of tags:** Choose how many tags to write as genres.
  Default: 5. If you only want a single genre, set this to 1.
+ **Join multiple tags with:** Select which character should be used
  to separate multiple tags.




Ratings
~~~~~~~


+ **Enable track ratings:** Check to write track ratings to your
  files.
+ **Submit ratings to MusicBrainz:** Check to submit ratings to
  MusicBrainz. The tracks will be rated with your account.




Tags
====


+ **Write tags to files:** Uncheck to disable Picard from writing
  data. Picard may still move/rename your files according to your
  settings.
+ **Preserve timestamps of tagged files:** If checked, does not update
  the Last Modified date and time of your music files when it writes new
  tags to them.




Before Tagging
~~~~~~~~~~~~~~


+ **Clear existing tags:** Checking this will remove all existing
  metadata and leave your files with only MusicBrainz metadata.
  Information you may have added through another media player such as
  `genre`, `comments` or `ratings` will be removed.
+ **Remove ID3 tags from FLAC files:** Check to remove ID3 tags from
  FLAC files – Vorbis Comments are recommended for FLAC files. Picard
  will write Vorbis Comments to FLACs regardless of this setting.
+ **Remove APEv2 tags from MP3 files:** Check to remove APEv2 tags
  from MP3 files – ID3 is recommended for MP3s. Picard will write ID3
  tags to MP3s regardless of this setting.



+ **Preserve these tags from being cleared or overwritten with
  MusicBrainz data:** This is an advanced option: If you have tags which
  you need to preserve, enter their names here to stop Picard from
  overwriting them.




Tag Compatibility
~~~~~~~~~~~~~~~~~


+ **ID3v2 version:** Although id3v2.4 is the latest version, its
  support in music players is **still** lacking. Whilst software such as
  `foobar2000`_ and `MediaMonkey`_ have no problem using version 2.4
  tags, you will not be able to read the tags in Windows Explorer or
  Windows Media Player (in any Windows or WMP version, including those
  in Windows 8.1). Apple iTunes is also still based in id3v23, and
  support for id3v24 in other media players (such as smartphones) is
  variable. Other than native support for multi-valued tags in v2.4, the
  :ref:`Picard Tag Mapping <mappings>` will show you what you lose when
  choosing v2.3 instead of v2.4.
+ **ID3v2 text encoding:** The default for version 2.4 is UTF-8, the
  default for version 2.3 is UTF-16. Use ISO-8859-1 **only** if you face
  compatibility issues with your player.
+ **Join id3v23 tags with:** As mentioned above, id3v23 does not
  support multi-value tags, and so Picard flattens these to strings
  before saving them to id3v23 tags. This setting defines the string
  used to separate the values when flattened. Use '; ' for the greatest
  compatibility (rather than '/' since tags more often contain a / than
  a;) and for the best visual compatibility in Picard between id3v23 and
  other tagging formats.
+ **Also include ID3v1 tags in the files:** Not recommended at all.
  ID3v1.1 tags are obsolete and may not work with non-latin scripts.




Cover art
=========

.. note:: You must enable "Option / Metadata / Use release relationships" for
    Picard to be able to download cover art.

In versions of Picard prior to 1.2, you will also require the Cover
Art Downloader plugin available on the `Picard Plugins`_ page



Location
~~~~~~~~


+ **Embed cover images into tags:** Enables images to be embedded
  directly into your music files. Whilst this will use more storage
  space than storing it as a separate image file in the same folder,
  some music players will only display embedded images and don't find
  the separate files.
+ **Only embed a front image:** Embeds only a front image into your
  music files. Many music players will only display a single embedded
  image, so embedding additional images may not add any functionality.
+ **Save cover images as separate files:** In the file name mask you
  can use any variable or function from :ref:`Picard Tags <picard-tags>` and
  :ref:`Picard Scripting <picard-scripting>`.
  The mask should **not** contain a file extension; this is
  added automatically based on the actual image type. The default value
  is `cover`. If you change this to `folder`, Windows will use it to
  preview the containing folder.
+ **Overwrite the file if it already exists:** Check this to replace
  existing files. This is especially recommended if trying to write
  "folder" previews for Windows.




Cover Art Providers
~~~~~~~~~~~~~~~~~~~

Picard can download Cover Art from a number of sources, and you can
choose which sources you want Picard to download cover art from:


+ **Cover Art Archive:** The Cover Art Archive (CAA) is MusicBrainz
  own archive of cover art in cooperation with the Internet Archive
  (archive.org). If art is available there, the Cover Art Archive is the
  most comprehensive database of cover art (front covers, back covers,
  booklets, CDs etc.).
+ **Amazon:** Amazon often has cover art when other sites don't,
  however whilst this art is almost always for the correct Artist/Album,
  it may not be the absolute correct cover art for the specific Release
  that you have tagged your music with.
+ **Sites on the whitelist:** See
  `Style/Relationships/URLs/Cover_art_whitelist`_


Note: CD Baby and other whitelist sites are no longer being used by
MusicBrainz for new Cover Art.



Cover Art Archive
~~~~~~~~~~~~~~~~~

In this section you can decide which types of cover art you would like
to download from the Cover Art Archive, and what quality (size) you
want to download. Obviously, the better the quality, the larger the
size of the files.

Most music players will display only one piece of cover art for the
album, and most people select Front (cover) for that.

Since Picard 1.3, you can also decide to use the image from the release
group (if any) if no front image is found for the release.
In this case, the cover may not match the exact release you are tagging
(eg. a 1979 vinyl front cover may be used in place of the Deluxe 2010
CD reissue).


File Naming
===========

This page tells Picard whether it should move your audio files to a
new directory when it saves metadata in them. One use for this is to
keep your work organised: all untagged files are under directory A,
and when Picard tags them it moves them to directory B. When directory
A is empty, your tagging work is done. Check this box, and select a
destination directory, if you want Picard to move files this way.
Uncheck the box if you want Picard to leave the files under the same
directory.

The Rename Files and Move Files options are independent. Rename Files
refers to Picard changing file names typically based on artist and
track names. Move Files refers to Picard moving files to new
directories, based on a stated parent directory and sub-directories
typically based on album artist name and release title. However, they
both use the same "file naming string". Move files uses the portion up
until the last '/'; rename files the part after that.


+ **Rename files when saving:** Check to let Picard change file and
  directory names of your files when it saves metadata in them, in order
  to make the file and directory names consistent with the new metadata.
+ **Replace non-ASCII characters:** Check to replace non-ASCII
  characters with their ASCII equivalent, e.g. á,ä,ǎ, with a; é,ě,ë,
  with e; æ with ae, etc. For more information on ASCII characters read
  the Wikipedia page on `ASCII`_.
+ **Replace Windows-incompatible characters:** Check to replace
  Windows-incompatible characters with an underscore. Enabled by default
  on Windows with no option to disable.
+ **Move files to this directory when saving:** Choose a destination
  parent directory to move saved files to.

    + If you use the directory "," they will be removed relative to their
      current location. If they are already in some sort of folder
      structure, this will probably not do what you want!

+ **Delete empty directories:** Check to have Picard remove
  directories that have become empty once a move is completed. Leave
  unchecked if you want Picard to leave the source directory structure
  unchanged. Checking this box may be convenient if you are using the
  move files option to organise your work. An empty directory has no
  more work for you to do, and deleting the directory makes that clear.
+ **Move additional files:** Enter wildcard patterns that match any
  other files you want Picard to move when saving files, e.g.
  `Folder.jpg`, `*.png`, `*.cue`, `*.log`. Using default settings, when
  these additional files are moved they will end up in the release
  directory with your files. In a wildcard, `*` matches zero or more
  characters. Other text, like `.jpg`, matches those exact characters.
  Thus `*.jpg` matches "cover.jpg", "liner.jpg", "a.jpg", and ".jpg", but
  not "nomatch.jpg2". Put spaces between wildcard patterns.



+ **Name files like this:** An edit box that contains a formatting
  string that tells Picard what the new name of the file and its
  containing directories should be, in terms of various metadata values.
  The formatting string is in Picard's :ref:`scripting language <picard-scripting>`
  where dark blue text starting with a "$" is a function name and names
  in light blue within "%" signs are Picard's :ref:`tag names <picard-tags>`.
  Note that the use of a "/" in the formatting string means that
  everything before the string is a directory name, and everything after
  the last "/" becomes the file's name.
  The formatting string is allowed to have zero, one, or multiple, "/".




Fingerprinting
==============

If you select a file or cluster in the Left side of the Picard screen
and click Scan, Picard will invoke a program to scan the file and
produce a fingerprint that can then be used to look up the file on
MusicBrainz.

MusicBrainz currently supports only `AcoustID`_ (an Open Source
`acoustic fingerprinting`_ system created by `Lukáš Lalinský`_) but
has previously supported TRM and MusicID PUID.



CD lookup
=========

This is where you tell Picard which CD drive it should use for looking
up CDs.



Windows
~~~~~~~

On Windows, Picard has a pulldown menu listing the various CD drives
it has found. Pull down the menu and select the drive you want.



OS X
~~~~

In OS X, this option is currently a text field. The device is usually
/dev/rdisk1.

If that doesn't work, one way is to simply keep increasing the number
(e.g. /dev/rdisk2) until it does work. A less trial and error method
is to open Terminal and type `mount`. The output should include a line
such as `/dev/disk2 on /Volumes/Audio CD (local, nodev, nosuid, read-
only)`. You need to replace /dev/disk with /dev/rdisk, so if, for
example, it says /dev/disk2, you should enter **/dev/rdisk2** in
Picard's preferences.



Linux
~~~~~

In Linux, Picard has a pulldown menu like in Windows. If you're using
an older version with a text field, you should enter the device name
(typically /dev/cdrom) here.



Other platforms
~~~~~~~~~~~~~~~

On other platforms, the CD Lookup option is a text field and you
should enter the path to the CD drive here.



Plugins
=======

Here you may enable/disable any of the plugins you have installed in
Picard. Note that some plugins have their own option page which will
appear under here.

For a list of plugins see `Picard Plugins`_.



Advanced
========



Web proxy
~~~~~~~~~

If you need a proxy to make an outside connection you may specify one
here.



Matching
~~~~~~~~

It is recommended for most users to not change these settings. However
for advanced users, it allows you to tune the way Picard matches your
files and clusters to to MusicBrainz releases and tracks.


+ **Minimal similarity for file lookups:** The higher then %, the more
  similar an individual file's metadata must be to MusicBrainz's
  metadata for it to be moved/matched to a release on the right-hand
  side.
+ **Minimal similarity for cluster lookups:** The higher then %, the
  more similar a cluster of files from the left-hand pane must be to a
  MusicBrainz release for the entire cluster to be moved/matched to a
  release on the right-hand side.
+ **Minimal similarity for matching files to tracks:** The higher
  then %, the more similar an individual file's metadata must be to
  MusicBrainz's metadata for it to be moved/matched to a release on the
  right-hand side.


If you have absolutely no metadata in your current files, and you are
using **Scan** to match tracks, you may find you need to lower Minimal
similarity for matching files to tracks in order to get Picard to
match the files within a release. Otherwise you may find that Picard
matches the track to a release but then is not sure which track is
correct; and leaves it in an "unmatched files" group within that
release.

As a general rule, lowering the percentages may increase the chance of
finding a match at the risk of false positives and incorrect matches.



Scripting
~~~~~~~~~

For scripting help see :ref:`Picard Scripting <picard-scripting>`
and :ref:`Picard Tags <picard-tags>` for variables available to script with.



User interface
~~~~~~~~~~~~~~


+ **Show text labels under icon:** Uncheck to make the toolbar a
  little smaller.
+ **Allow selection of multiple directories:** Check to bypass the
  native directory selector and use QT's file dialog since the native
  directory selector usually doesn't allow you to select more than one
  directory. This applies for the 'Add folder' dialog, the file browser
  always allows multiple directory selection.
+ **Use advanced query syntax:** Check to enable `advanced query
  syntax`_ parsing on your searches. This only applies for the search
  box at the top right of Picard, not the lookup buttons.
+ **Show a quit confirmation dialog for unsaved changes:** Check to
  show a dialog when you try to quit Picard with unsaved files loaded.
  This may help prevent accidentally losing tag changes you've made, but
  not yet saved.
+ **Begin browsing in the following directory:** By default, Picard
  remembers the last directory you loaded files from. If you check this
  box and provide a directory, Picard will start in the directory
  provided instead.
+ **User interface language:** By default, Picard will display in the
  language displayed by your operating system, however you can override
  this here if needed.




.. _acoustic fingerprinting: http://musicbrainz.org/doc/Fingerprinting
.. _AcoustID: http://musicbrainz.org/doc/AcoustID
.. _advanced query syntax: http://musicbrainz.org/doc/Text_Search_Syntax
.. _alias: http://musicbrainz.org/doc/Aliases
.. _Artist Credits: http://musicbrainz.org/doc/Artist_Credit
.. _Artist: http://musicbrainz.org/doc/Artist
.. _artist name: http://musicbrainz.org/doc/Artist_Name
.. _artist sort name: http://musicbrainz.org/doc/Artist_Sort_Name
.. _ASCII: http://en.wikipedia.org/wiki/ASCII
.. _foobar2000: http://www.foobar2000.org
.. _Lukáš Lalinský: http://musicbrainz.org/doc/User:LukasLalinsky
.. _MediaMonkey: http://www.mediamonkey.com
.. _Picard Plugins: http://picard.musicbrainz.org/plugins/
.. _Recordings: http://musicbrainz.org/doc/Recording
.. _Release: http://musicbrainz.org/doc/Release
.. _Style/Relationships/URLs/Cover_art_whitelist: http://musicbrainz.org/doc/Style/Relationships/URLs/Cover_art_whitelist

