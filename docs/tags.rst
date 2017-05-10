.. _picard-tags:

Tags
####

This page describes both Tags (which are saved inside your music files
and can be read by your music player) and Picard variables which can
be used in Picard scripts (for tagging, for file renaming and in
several other more minor settings).

All tags are also available as variables, but additional variables
which start with '_' are not saved as Tags within your music files.

Variable are used in scripts by wrapping the name between '%'
character e.g. '%title%'.

Some variables can contain more than one value (for example,
musicbrainz_artistid ), and if you want to use only one of the values
then you will need to use special :ref:`script functions <scripting-functions>`
to access / set them.
To access all the multiple values at one, use the variable
normally and Picard will combine them into a single string separated
by '; ' (semicolon space).

If a later version of Picard is shown here than the current official
version on the `downloads`_ page, then these are beta functionality
which will be available in the next official release and a description
of how to gain access to these beta versions for testing can also be
found on the `downloads`_ page.



Basic Tags
==========

The following tags are populated from MusicBrainz data for most
releases, without any special Picard settings.

All of these are also available as variables for use in Picard Scripts
(for tagging, for file renaming and in several other more minor
settings) by wrapping them between '%' symbols e.g. '%title%'.

.. list-table:: Basic Tags
   :widths: 10 30

   * - ``title``
     - `Track Title`_
   * - ``artist``
     - `Track Artist`_ Name(s) (string)
   * - ``artists``
     - `Track Artist`_ Name(s) (multi-value) (since Picard 1.3)
   * - ``artistsort``
     - `Track Artist`_ `Sort Name`_
   * - ``albumartist``
     - `Release Artist`_
   * - ``albumartistsort``
     - `Release Artist`_'s `Sort Name`_
   * - ``releasestatus``
     - `Release Status`_
   * - ``releasetype``
     - `Release Group Type`_ (see also ``_primaryreleasetype`` / ``_secondaryreleasetype``)
   * - ``album``
     - `Release Title`_
   * - ``asin``
     - `ASIN`_
   * - ``language``
     - Work lyric language as per `ISO 639-3`_ if track relationships are enabled in `Options`_ and a related work exists. (since Picard 0.10)
   * - ``script``
     - Release Script (since Picard 0.10)
   * - ``releasecountry``
     - `Release Country`_
   * - ``date``
     - `Release Date`_ (YYYY-MM-DD)
   * - ``originaldate``
     - Original Release Date (YYYY-MM-DD) of the earliest release in the `Release Group`_ intended to provide e.g. the release date of the vinyl version of what you have on CD. (Included as standard from Picard 0.15, and using the Original Release Date plugin if you are still using a non-NGS version earlier than Picard 0.15) Note: If you are storing tags in mp3 files as ID3v23 (which is the Windows / iTunes compatible version) then original date can only be stored as a year.
   * - ``catalognumber``
     - Release `Catalog Number`_ (s)
   * - ``label``
     - Release `Label Name`_ (s)
   * - ``barcode``
     - Release `Barcode`_
   * - ``media``
     - `Release Format`_
   * - ``discnumber``
     - `Disc Number`_ of the disc in this release that this track is on
   * - ``totaldiscs``
     - Total number of discs in this release
   * - ``discsubtitle``
     - The `Media Title`_ given to a specific disc.
   * - ``tracknumber``
     - Track number on the disc
   * - ``totaltracks``
     - Total tracks on this disc
   * - ``isrc``
     - `ISRC`_ (since Picard 0.12)
   * - ``compilation``
     - (since Picard 1.3, compatible with iTunes) 1 for Various Artist albums, 0 otherwise (Picard 1.2 or previous) 1 if multiple track artists (including featured artists), 0 otherwise
   * - ``musicbrainz_trackid``
     - Recording `MusicBrainz Identifier`_
   * - ``musicbrainz_releasetrackid``
     - Release Track `MusicBrainz Identifier`_ (since Picard 1.3)
   * - ``musicbrainz_artistid``
     - `Track Artist`_'s `MusicBrainz Identifier`_
   * - ``musicbrainz_albumid``
     - Release `MusicBrainz Identifier`_
   * - ``musicbrainz_albumartistid``
     - `Release Artist`_'s `MusicBrainz Identifier`_
   * - ``musicbrainz_discid``
     - `Disc ID`_ if album added using CD Lookup (since Picard 0.12)



Basic Variables
===============

These variables are also populated from MusicBrainz data for most
releases, without any special Picard settings.


.. list-table:: Basic Variables
   :widths: 10 30

   * - ``_albumtracknumber``
     - The absolute number of this track disregarding the disc number i.e. %_albumtracknumber% of %_totalalbumtracks% (c.f. %tracknumber% of %totaltracks%). (Since Picard 1.3)
   * - ``_totalalbumtracks``
     - The total number of tracks across all discs of this release.
   * - ``_releasecomment``
     - `Release disambiguation comment`_ (since Picard 0.15)
   * - ``_releaselanguage``
     - `Release Language`_ as per `ISO 639-3`_ (since Picard 0.10)
   * - ``_releasegroup``
     - `Release Group Title`_ which is typically the same as the Album Title, but can be different.
   * - ``_releasegroupcomment``
     - `Release Group disambiguation comment`
   * - ``_primaryreleasetype``
     - `Release Group Primary type`_ i.e. Album, Single, EP, Broadcast, Other.
   * - ``_secondaryreleasetype``
     - Zero or more `Release Group Secondary types`_ i.e. Audiobook, Compilation, DJ-mix, Interview, Live, Mixtape/Street, Remix, Soundtrack, Spokenword
   * - ``_length``
     - The length of the track in format mins:secs.
   * - ``_rating``
     - `Rating`_ 0-5 by Musicbrainz users
   * - ``_dirname``
     - The name of the directory the file is in at the point of being loaded into Picard. (Since Picard 1.1)
   * - ``_filename``
     - The name of the file without extension (since Picard 1.1)
   * - ``_extension``
     - The files extension (since Picard 0.9)
   * - ``_format``
     - Media format of the file e.g. MPEG-1 Audio
   * - ``_bitrate``
     - Approximate bitrate in kbps.
   * - ``_channels``
     - No. of audio channels in the file
   * - ``_sample_rate``
     - Number of digitising samples per second Hz
   * - ``_bits_per_sample``
     - Bits of data per sample
   * - ``_multiartist``
     - 0 if tracks on the album all have the same primary artist, 1 otherwise. (Since Picard 1.3)




Advanced Tags
=============

If you enable tagging with `Advanced Relationships`_, you get these
extra tags:

.. list-table:: Advanced Tags
   :widths: 10 30

   * - ``work``
     - `Work Name`_ (since Picard 1.3)
   * - ``writer``
     - `Writer Relationship Type`_ (since Picard 1.0; not written to most file formats automatically[1]).
   * - ``composer``
     - `Composer Relationship Type`_
   * - ``conductor``
     - Conductor Relationship Type (`releases <http://musicbrainz.org/relationship/9ae9e4d0-f26b-42fb-ab5c-1149a47cf83b>`__, `recordings <http://musicbrainz.org/relationship/234670ce-5f22-4fd0-921b-ef1662695c5d>`_), Chorus Master Relationship Type (`releases <http://musicbrainz.org/relationship/b9129850-73ec-4af5-803c-1c12b97e25d2>`__, `recordings <http://musicbrainz.org/relationship/45115945-597e-4cb9-852f-4e6ba583fcc8>`__)
   * - ``performer:<type>``
     - "Performer Relationship Type (`releases <http://musicbrainz.org/relationship/888a2320-52e4-4fe8-a8a0-7a4c8dfde167>`__ - `vocals <http://musicbrainz.org/relationship/eb10f8a0-0f4c-4dce-aa47-87bcb2bc42f3>`__/`instruments <http://musicbrainz.org/relationship/67555849-61e5-455b-96e3-29733f0115f5>`__, `recordings <http://musicbrainz.org/relationship/628a9658-f54c-4142-b0c0-95f031b544da>`__ - `vocals <http://musicbrainz.org/relationship/0fdbe3c6-7700-4a31-ae54-b53f06ae1cfa>`__/`instruments <http://musicbrainz.org/relationship/59054b12-01ac-43ee-a618-285fd397e461>`__), Orchestra Relationship Type (`releases <http://musicbrainz.org/relationship/23a2e2e7-81ca-4865-8d05-2243848a77bf>`__, `recordings <http://musicbrainz.org/relationship/3b6616c5-88ba-4341-b4ee-81ce1e6d7ebb>`__), <type> can be ""orchestra"", ""vocal"", ""guest guitar"", ..."
   * - ``arranger``
     - `Arranger Relationship Type`_, `Instrumentator Relationship Type`_, `Orchestrator Relationship Type`_ (since Picard 0.10)
   * - ``lyricist``
     - `Lyricist Relationship Type`_
   * - ``remixer``
     - `Remixer Relationship Type`_
   * - ``producer``
     - `Producer Relationship Type`_
   * - ``engineer``
     - `Engineer Relationship Type`_
   * - ``mixer``
     - `Engineer Relationship Type`_ ("Mixed By") (since Picard 0.9)
   * - ``djmixer``
     - `Mix-DJ Relationship Type`_ (since Picard 0.9)
   * - ``license``
     - License Relationship Type (`releases <http://musicbrainz.org/relationship/004bd0c3-8a45-4309-ba52-fa99f3aa3d50>`__, `recordings <http://musicbrainz.org/relationship/f25e301d-b87b-4561-86a0-5d2df6d26c0a>`__) (since Picard 1.0)

And if you enable folksonomy tags, you get:

.. list-table:: Advanced Tags with folksonomy
   :widths: 10 30

   * - ``genre``
     - Pseudo-genre based on folksonomy tags


Advanced Variables
==================

If you enable tagging with `Advanced Relationships`_, you get these
extra variables:

.. list-table:: Advanced Variables
   :widths: 10 30

   * - ``_recordingtitle``
     - `Recording`_ title - normally the same as the Track title, but can be different.
   * - ``_recordingcomment``
     - `Recording disambiguation comment`_ (since Picard 0.15)


Plugins
=======

Plugins from `Picard Plugins`_ can add more tags.



Last.fm
~~~~~~~

.. list-table:: Last.fm Advanced Variables
   :widths: 10 30

   * - ``genre``
     - Pseudo-genre based on folksonomy tags


Last.fm Plus
~~~~~~~~~~~~

The `LastFMPlus`_ plugin is a sophisticated plugin that tries to
provide stable and meaningful genre selections from the ever-changing
and idiosyncratic list provided by lastFM.

The `LastFMPlus`_ plugin is very configurable and examples provided here
are based on the default lists provided on the Tag Filter List tab of
the LastFMPlus options page.

.. list-table:: Last.fm Plus Advanced Variables
   :widths: 10 30

   * - ``grouping``
     - Top-level genres - default list: Audiobooks, Blues, Classic rock, Classical, Country, Dance, Electronica, Folk, Hip-hop, Indie, Jazz, Kids, Metal, Pop, Punk, Reggae, Rock, Soul, Trance
   * - ``genre``
     - Specific detailed genres, e.g. if group is Rock, genre could be one of Acid rock, Acoustic rock, Alternative metal, Alternative rock, Art rock, Blues rock, Boogie rock, Brit rock, Christian rock, College rock, Country rock etc.
   * - ``mood``
     - How a track 'feels' e.g. Happy, Introspective, Drunk etc.
   * - ``Comment:songs-db_Occassion``
     - Good situations to play a track e.g. Driving, Love, Party etc.
   * - ``Comment:songs-db_Custom1``
     - Decade e.g. 1970s
   * - ``Comment:songs-db_Custom2``
     - Category e.g. Female Vocalist, Singer-Songwriter etc.
   * - ``Comment:songs-db_Custom3``
     - Country e.g. British
   * - ``Original Year``
     - Original Year that the track was released (compared to Original Release Date, the earliest release date of the entire Album)


Note 1: This plugin makes a large number of web services calls to get
track-specific data, so loading a large number of albums / tracks
could take a significant amount of time.

Note 2: Original Year does not seem to be working correctly at
present.



Other Information
=================

For technical details on how these tags are written into files, see
:ref:`Picard Tag Mapping <mappings>`.

If you set new variables, these will be saved as new tags in ID3,
APEv2 and VORBIS based files. For ID3 based files these will be saved
to, and reloaded from, ID3 user defined text information (TXXX)
frames. They will not be saved in ASF, MP4 or WAV based files.

For ID3 based tags i.e. mp3 files, you can also set ID3 tags directly
from your scripts by setting a special variable starting '_id3:'.
Currently these tags are not loaded into variables when you reload the
file into Picard.</code>. (Since Picard 0.9)



Footnotes
=========


#. You can merge this with composers with a :ref:`script <picard-scripting>` like

::

    $copymerge(composer, writer)





.. _Advanced Relationships: http://musicbrainz.org/doc/Advanced_Relationship
.. _Arranger Relationship Type: http://musicbrainz.org/doc/index.php?title=Arranger_Relationship_Type&action=edit&redlink=1
.. _ASIN: http://musicbrainz.org/doc/ASIN
.. _Barcode: http://musicbrainz.org/doc/Barcode
.. _Catalog Number: http://musicbrainz.org/doc/Catalog_Number
.. _Composer Relationship Type: http://musicbrainz.org/relationship/d59d99ea-23d4-4a80-b066-edca32ee158f
.. _Disc ID: http://musicbrainz.org/doc/Disc_ID
.. _Disc Number: http://musicbrainz.org/doc/Disc_Number
.. _downloads: http://picard.musicbrainz.org/downloads/
.. _Engineer Relationship Type: http://musicbrainz.org/doc/index.php?title=Engineer_Relationship_Type&action=edit&redlink=1
.. _Instrumentator Relationship Type: http://musicbrainz.org/doc/index.php?title=Instrumentator_Relationship_Type&action=edit&redlink=1
.. _ISO 639-3: http://www.sil.org/iso639-3
.. _ISRC: http://musicbrainz.org/doc/ISRC
.. _Label Name: http://musicbrainz.org/doc/Label_Name
.. _LastFMPlus: http://musicbrainz.org/doc/index.php?title=LastFMPlus&action=edit&redlink=1
.. _Lyricist Relationship Type: http://musicbrainz.org/relationship/3e48faba-ec01-47fd-8e89-30e81161661c
.. _Media Title: http://musicbrainz.org/doc/Release_Status#Title_2
.. _Mix-DJ Relationship Type: http://musicbrainz.org/doc/index.php?title=Mix-DJ_Relationship_Type&action=edit&redlink=1
.. _MusicBrainz Identifier: http://musicbrainz.org/doc/MusicBrainz_Identifier
.. _Options: :ref:`options`
.. _Orchestrator Relationship Type: http://musicbrainz.org/doc/index.php?title=Orchestrator_Relationship_Type&action=edit&redlink=1
.. _Picard Plugins: http://picard.musicbrainz.org/plugins/
.. _Producer Relationship Type: http://musicbrainz.org/doc/index.php?title=Producer_Relationship_Type&action=edit&redlink=1
.. _Rating: http://musicbrainz.org/doc/Rating_System
.. _Recording disambiguation comment: http://musicbrainz.org/doc/Recording#Disambiguation_comment
.. _Recording: http://musicbrainz.org/doc/Recording
.. _Release Artist: http://musicbrainz.org/doc/Release_Artist
.. _Release Country: http://musicbrainz.org/doc/Release_Country
.. _Release Date: http://musicbrainz.org/doc/Release_Date
.. _Release disambiguation comment: http://musicbrainz.org/doc/Release#Disambiguation_comment
.. _Release Format: http://musicbrainz.org/doc/Release_Format
.. _Release Group disambiguation comment: http://musicbrainz.org/doc/Release_Group#Disambiguation_comment
.. _Release Group: http://musicbrainz.org/doc/Release_Group
.. _Release Group Primary type: http://musicbrainz.org/doc/Release_Group/Type#Primary_types
.. _Release Group Secondary types: http://musicbrainz.org/doc/Release_Group/Type#Secondary_types
.. _Release Group Title: http://musicbrainz.org/doc/Release_Group#Title
.. _Release Group Type: http://musicbrainz.org/doc/Release_Group/Type
.. _Release: http://musicbrainz.org/doc/Release
.. _Release Language: http://musicbrainz.org/doc/Release_Language#Language_and_script
.. _Release Status: http://musicbrainz.org/doc/Release_Status
.. _Release Title: http://musicbrainz.org/doc/Release#Title
.. _Remixer Relationship Type: http://musicbrainz.org/doc/index.php?title=Remixer_Relationship_Type&action=edit&redlink=1
.. _Sort Name: http://musicbrainz.org/doc/Style/Artist/Sort_Name
.. _Track Artist: http://musicbrainz.org/doc/Track_Artist
.. _Track Title: http://musicbrainz.org/doc/Track_Title
.. _Work Name: http://musicbrainz.org/doc/Work
.. _Writer Relationship Type: http://musicbrainz.org/relationship/a255bca1-b157-4518-9108-7b147dc3fc68


