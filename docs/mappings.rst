.. _mappings:

Tag Mappings
############

Table of mapping between `Picard`_ internal tag names and various
tagging formats.

.. list-table:: Tag Mappings
   :header-rows: 1
   :class: table-bordered

   * - Name
     - Internal Name
     - ID3v2
     - Vorbis
     - APEv2
     - iTunes MP4
     - ASF/Windows Media
   * - `Album <http://musicbrainz.org/doc/Release_Title>`__
     - ``album``
     - ``TALB``
     - ``ALBUM``
     - ``Album``
     - ``©alb``
     - ``WM/AlbumTitle``
   * - `Track Title <http://musicbrainz.org/doc/Track_Title>`__
     - ``title``
     - ``TIT2``
     - ``TITLE``
     - ``Title``
     - ``©nam``
     - ``Title``
   * - `Artist <http://musicbrainz.org/doc/Artist>`__
     - ``artist``
     - ``TPE1``
     - ``ARTIST``
     - ``Artist``
     - ``©ART``
     - ``Author``
   * - `Album Artist <http://musicbrainz.org/doc/Release_Artist>`__
     - ``albumartist``
     - ``TPE2``
     - ``ALBUMARTIST``
     - ``Album Artist``
     - ``aART``
     - ``WM/AlbumArtist``
   * - `Release Date <http://musicbrainz.org/doc/Release_Date>`__
     - ``date``
     - ``TDRC`` *(id3v24)* ``TYER``+ ``TDAT`` *(id3v23)*
     - ``DATE``
     - ``Year``
     - ``©day``
     - ``WM/Year``
   * - Original Release Date [#f1]_
     - ``originaldate``
     - ``TDOR`` *(id3v24)* ``TORY`` *(id3v23)*
     - ``ORIGINALDATE``
     - 
     - 
     - ``WM/OriginalReleaseYear``
   * - `Composer <http://musicbrainz.org/relationship/d59d99ea-23d4-4a80-b066-edca32ee158f>`__
     - ``composer``
     - ``TCOM``
     - ``COMPOSER``
     - ``Composer``
     - ``©wrt``
     - ``WM/Composer``
   * - `Lyricist <http://musicbrainz.org/relationship/3e48faba-ec01-47fd-8e89-30e81161661c>`__
     - ``lyricist``
     - ``TEXT``
     - ``LYRICIST``
     - ``Lyricist``
     - ``----:com.apple.iTunes:LYRICIST``
     - ``WM/Writer``
   * - `Writer <http://musicbrainz.org/relationship/a255bca1-b157-4518-9108-7b147dc3fc68>`__ [#f2]_
     - ``writer``
     - ``TXXX:Writer`` *(Picard>=1.3)*
     - ``WRITER``
     - ``Writer``
     - 
     - 
   * - `Conductor <http://musicbrainz.org/relationship/234670ce-5f22-4fd0-921b-ef1662695c5d>`__
     - ``conductor``
     - ``TPE3``
     - ``CONDUCTOR``
     - ``Conductor``
     - ``----:com.apple.iTunes:CONDUCTOR``
     - ``WM/Conductor``
   * - Performer (`1 <http://musicbrainz.org/relationship/888a2320-52e4-4fe8-a8a0-7a4c8dfde167>`__, `2 <http://musicbrainz.org/relationship/eb10f8a0-0f4c-4dce-aa47-87bcb2bc42f3>`__, `3 <http://musicbrainz.org/relationship/67555849-61e5-455b-96e3-29733f0115f5>`__, `4 <http://musicbrainz.org/relationship/628a9658-f54c-4142-b0c0-95f031b544da>`__, `5 <http://musicbrainz.org/relationship/0fdbe3c6-7700-4a31-ae54-b53f06ae1cfa>`__, `6 <http://musicbrainz.org/relationship/59054b12-01ac-43ee-a618-285fd397e461>`__) [instrument]
     - ``performer:instrument``
     - ``TMCL:instrument`` *(id3v24)* ``IPLS:instrument`` *(id3v23)*
     - ``PERFORMER``=*artist* ( ``instrument``)
     - ``Performer``=*artist* ( ``instrument``)
     - 
     - 
   * - `Remixer <http://musicbrainz.org/doc/index.php?title=Remixer_Relationship_Type&action=edit&redlink=1>`__
     - ``remixer``
     - ``TPE4``
     - ``REMIXER``
     - ``MixArtist``
     - ``----:com.apple.iTunes:REMIXER``
     - ``WM/ModifiedBy``
   * - `Arranger <http://musicbrainz.org/doc/index.php?title=Arranger_Relationship_Type&action=edit&redlink=1>`__
     - ``arranger``
     - ``TIPL:arranger`` *(id3v24)* ``IPLS:arranger`` *(id3v23)*
     - ``ARRANGER``
     - ``Arranger``
     - 
     - 
   * - `Engineer <http://musicbrainz.org/doc/index.php?title=Engineer_Relationship_Type&action=edit&redlink=1>`__
     - ``engineer``
     - ``TIPL:engineer`` *(id3v24)* ``IPLS:engineer`` *(id3v23)*
     - ``ENGINEER``
     - ``Engineer``
     - ``----:com.apple.iTunes:ENGINEER``
     - ``WM/Engineer``
   * - `Producer <http://musicbrainz.org/doc/index.php?title=Producer_Relationship_Type&action=edit&redlink=1>`__
     - ``producer``
     - ``TIPL:producer`` *(id3v24)* ``IPLS:producer`` *(id3v23)*
     - ``PRODUCER``
     - ``Producer``
     - ``----:com.apple.iTunes:PRODUCER``
     - ``WM/Producer``
   * - `Mix-DJ <http://musicbrainz.org/doc/index.php?title=Mix-DJ_Relationship_Type&action=edit&redlink=1>`__
     - ``djmixer``
     - ``TIPL:DJ-mix`` *(id3v24)* ``IPLS:DJ-mix`` *(id3v23)*
     - ``DJMIXER``
     - ``DJMixer``
     - ``----:com.apple.iTunes:DJMIXER``
     - ``WM/DJMixer``
   * - `Mixer <http://musicbrainz.org/doc/index.php?title=Mix_Engineer_Relationship_Type&action=edit&redlink=1>`__
     - ``mixer``
     - ``TIPL:mix`` *(id3v24)* ``IPLS:mix`` *(id3v23)*
     - ``MIXER``
     - ``Mixer``
     - ``----:com.apple.iTunes:MIXER``
     - ``WM/Mixer``
   * - Grouping [#f3]_
     - ``grouping``
     - ``TIT1``
     - ``GROUPING``
     - ``Grouping``
     - ``©grp``
     - ``WM/ContentGroupDescription``
   * - Subtitle [#f4]_
     - ``subtitle``
     - ``TIT3``
     - ``SUBTITLE``
     - ``Subtitle``
     - ``----:com.apple.iTunes:SUBTITLE``
     - ``WM/SubTitle``
   * - Disc Subtitle
     - ``discsubtitle``
     - ``TSST`` *(id3v24 only)*
     - ``DISCSUBTITLE``
     - ``DiscSubtitle``
     - ``----:com.apple.iTunes:DISCSUBTITLE``
     - ``WM/SetSubTitle``
   * - Track Number
     - ``tracknumber``
     - ``TRCK``
     - ``TRACKNUMBER``
     - ``Track``
     - ``trkn``
     - ``WM/TrackNumber``
   * - Total Tracks
     - ``totaltracks``
     - ``TRCK``
     - ``TRACKTOTAL and TOTALTRACKS``
     - ``Track``
     - ``trkn``
     - 
   * - Disc Number
     - ``discnumber``
     - ``TPOS``
     - ``DISCNUMBER``
     - ``Disc``
     - ``disk``
     - ``WM/PartOfSet``
   * - Total Discs
     - ``totaldiscs``
     - ``TPOS``
     - ``DISCTOTAL and TOTALDISCS``
     - ``Disc``
     - ``disk``
     - 
   * - Compilation (iTunes) [#f5]_
     - ``compilation``
     - ``TCMP``
     - ``COMPILATION``
     - ``Compilation``
     - ``cpil``
     - ``WM/IsCompilation``
   * - Comment [#f4]_
     - ``comment:description``
     - ``COMM:description``
     - ``COMMENT``
     - ``Comment``
     - ``©cmt``
     - ``Description``
   * - `Genre <http://musicbrainz.org/doc/Folksonomy_Tagging>`__
     - ``genre``
     - ``TCON``
     - ``GENRE``
     - ``Genre``
     - ``©gen``
     - ``WM/Genre``
   * - `Rating <http://musicbrainz.org/doc/Rating_System>`__
     - ``_rating``
     - ``POPM``
     - ``RATING:user@email``
     - 
     - 
     - ``WM/SharedUserRating``
   * - BPM [#f4]_
     - ``bpm``
     - ``TBPM``
     - ``BPM``
     - ``BPM``
     - ``tmpo``
     - ``WM/BeatsPerMinute``
   * - Mood [#f3]_
     - ``mood``
     - ``TMOO`` *(id3v24 only)*
     - ``MOOD``
     - ``Mood``
     - ``----:com.apple.iTunes:MOOD``
     - ``WM/Mood``
   * - `ISRC <http://musicbrainz.org/doc/ISRC>`__
     - ``isrc``
     - ``TSRC``
     - ``ISRC``
     - ``ISRC``
     - ``----:com.apple.iTunes:ISRC``
     - ``WM/ISRC``
   * - Copyright [#f4]_
     - ``copyright``
     - ``TCOP``
     - ``COPYRIGHT``
     - ``Copyright``
     - ``cprt``
     - ``Copyright``
   * - Lyrics [#f4]_
     - ``lyrics:description``
     - ``USLT:description``
     - ``LYRICS``
     - ``Lyrics``
     - ``©lyr``
     - ``WM/Lyrics``
   * - `Media <http://musicbrainz.org/doc/Release_Format>`__
     - ``media``
     - ``TMED``
     - ``MEDIA``
     - ``Media``
     - ``----:com.apple.iTunes:MEDIA``
     - ``WM/Media``
   * - `Record Label <http://musicbrainz.org/doc/Label_Name>`__
     - ``label``
     - ``TPUB``
     - ``LABEL``
     - ``Label``
     - ``----:com.apple.iTunes:LABEL``
     - ``WM/Publisher``
   * - `Catalog Number <http://musicbrainz.org/doc/Release_Catalog_Number>`__
     - ``catalognumber``
     - ``TXXX:CATALOGNUMBER``
     - ``CATALOGNUMBER``
     - ``CatalogNumber``
     - ``----:com.apple.iTunes:CATALOGNUMBER``
     - ``WM/CatalogNo``
   * - `Barcode <http://musicbrainz.org/doc/Barcode>`__
     - ``barcode``
     - ``TXXX:BARCODE``
     - ``BARCODE``
     - ``Barcode``
     - ``----:com.apple.iTunes:BARCODE``
     - ``WM/Barcode``
   * - Encoded By [#f4]_
     - ``encodedby``
     - ``TENC``
     - ``ENCODEDBY``
     - ``EncodedBy``
     - ``©too``
     - ``WM/EncodedBy``
   * - Encoder Settings [#f4]_
     - ``encodersettings``
     - ``TSSE``
     - ``ENCODERSETTINGS``
     - ``EncoderSettings``
     - 
     - ``WM/EncoderSettings``
   * - Album Sort Order [#f4]_
     - ``albumsort``
     - ``TSOA``
     - ``ALBUMSORT``
     - ``ALBUMSORT``
     - ``soal``
     - ``WM/AlbumSortOrder``
   * - Album Artist Sort Order
     - ``albumartistsort``
     - ``TSO2`` *(Picard>=1.2)* ``TXXX:ALBUMARTISTSORT`` *(Picard<=1.1)*
     - ``ALBUMARTISTSORT``
     - ``ALBUMARTISTSORT``
     - ``soaa``
     - ``WM/AlbumArtistSortOrder``
   * - Artist Sort Order
     - ``artistsort``
     - ``TSOP``
     - ``ARTISTSORT``
     - ``ARTISTSORT``
     - ``soar``
     - ``WM/ArtistSortOrder``
   * - Title Sort Order [#f4]_
     - ``titlesort``
     - ``TSOT``
     - ``TITLESORT``
     - ``TITLESORT``
     - ``sonm``
     - ``WM/TitleSortOrder``
   * - Composer Sort Order
     - ``composersort``
     - ``TSOC`` *(Picard>=1.3)* ``TXXX:COMPOSERSORT`` *(Picard<=1.2)*
     - ``COMPOSERSORT``
     - ``COMPOSERSORT``
     - ``soco``
     - ``WM/ComposerSortOrder`` *(Picard>=1.3)*
   * - Show Name Sort Order [#f4]_
     - ``showsort``
     - 
     - 
     - 
     - ``sosn``
     - 
   * - `MusicBrainz Recording Id <http://musicbrainz.org/doc/MusicBrainz_Identifier>`__
     - ``musicbrainz_recordingid``
     - ``UFID:http://musicbrainz.org``
     - ``MUSICBRAINZ_TRACKID``
     - ``MUSICBRAINZ_TRACKID``
     - ``----:com.apple.iTunes:MusicBrainz Track Id``
     - ``MusicBrainz/Track Id``
   * - `MusicBrainz Track Id <http://musicbrainz.org/doc/MusicBrainz_Identifier>`__
     - ``musicbrainz_trackid``
     - ``TXXX:MusicBrainz Release Track Id``
     - ``MUSICBRAINZ_RELEASETRACKID``
     - ``MUSICBRAINZ_RELEASETRACKID``
     - ``----:com.apple.iTunes:MusicBrainz Release Track Id``
     - ``MusicBrainz/Release Track Id``
   * - `MusicBrainz Release Id <http://musicbrainz.org/doc/MusicBrainz_Identifier>`__
     - ``musicbrainz_albumid``
     - ``TXXX:MusicBrainz Album Id``
     - ``MUSICBRAINZ_ALBUMID``
     - ``MUSICBRAINZ_ALBUMID``
     - ``----:com.apple.iTunes:MusicBrainz Album Id``
     - ``MusicBrainz/Album Id``
   * - `MusicBrainz Artist Id <http://musicbrainz.org/doc/MusicBrainz_Identifier>`__
     - ``musicbrainz_artistid``
     - ``TXXX:MusicBrainz Artist Id``
     - ``MUSICBRAINZ_ARTISTID``
     - ``MUSICBRAINZ_ARTISTID``
     - ``----:com.apple.iTunes:MusicBrainz Artist Id``
     - ``MusicBrainz/Artist Id``
   * - `MusicBrainz Release Artist Id <http://musicbrainz.org/doc/MusicBrainz_Identifier>`__
     - ``musicbrainz_albumartistid``
     - ``TXXX:MusicBrainz Album Artist Id``
     - ``MUSICBRAINZ_ALBUMARTISTID``
     - ``MUSICBRAINZ_ALBUMARTISTID``
     - ``----:com.apple.iTunes:MusicBrainz Album Artist Id``
     - ``MusicBrainz/Album Artist Id``
   * - `MusicBrainz TRM Id <http://musicbrainz.org/doc/TRM>`__
     - ``musicbrainz_trmid``
     - ``TXXX:MusicBrainz TRM Id``
     - ``MUSICBRAINZ_TRMID``
     - ``MUSICBRAINZ_TRMID``
     - ``----:com.apple.iTunes:MusicBrainz TRM Id``
     - ``MusicBrainz/TRM Id``
   * - `MusicBrainz Disc Id <http://musicbrainz.org/doc/Disc_ID>`__
     - ``musicbrainz_discid``
     - ``TXXX:MusicBrainz Disc Id``
     - ``MUSICBRAINZ_DISCID``
     - ``MUSICBRAINZ_DISCID``
     - ``----:com.apple.iTunes:MusicBrainz Disc Id``
     - ``MusicBrainz/Disc Id``
   * - `MusicIP PUID <http://musicbrainz.org/doc/PUID>`__
     - ``musicip_puid``
     - ``TXXX:MusicIP PUID``
     - ``MUSICIP_PUID``
     - ``MUSICIP_PUID``
     - ``----:com.apple.iTunes:MusicIP PUID``
     - ``MusicIP/PUID``
   * - MusicIP Fingerprint
     - ``musicip_fingerprint``
     - ``TXXX:MusicMagic Fingerprint``
     - ``FINGERPRINT=MusicMagic Fingerprint`` *{fingerprint}*
     - 
     - ``----:com.apple.iTunes:fingerprint``
     - 
   * - `Release Status <http://musicbrainz.org/doc/Release_Status>`__
     - ``releasestatus``
     - ``TXXX:MusicBrainz Album Status``
     - ``RELEASESTATUS``
     - ``MUSICBRAINZ_ALBUMSTATUS``
     - ``----:com.apple.iTunes:MusicBrainz Album Status``
     - ``MusicBrainz/Album Status``
   * - `Release Type <http://musicbrainz.org/doc/Release_Type>`__
     - ``releasetype``
     - ``TXXX:MusicBrainz Album Type``
     - ``RELEASETYPE``
     - ``MUSICBRAINZ_ALBUMTYPE``
     - ``----:com.apple.iTunes:MusicBrainz Album Type``
     - ``MusicBrainz/Album Type``
   * - `Release Country <http://musicbrainz.org/doc/Release_Country>`__
     - ``releasecountry``
     - ``TXXX:MusicBrainz Album Release Country``
     - ``RELEASECOUNTRY``
     - ``RELEASECOUNTRY``
     - ``----:com.apple.iTunes:MusicBrainz Album Release Country``
     - ``MusicBrainz/Album Release Country``
   * - `ASIN <http://musicbrainz.org/doc/ASIN>`__
     - ``asin``
     - ``TXXX:ASIN``
     - ``ASIN``
     - ``ASIN``
     - ``----:com.apple.iTunes:ASIN``
     - 
   * - Gapless Playback [#f4]_
     - ``gapless``
     - 
     - 
     - 
     - ``pgap``
     - 
   * - Podcast [#f4]_
     - ``podcast``
     - 
     - 
     - 
     - ``pcst``
     - 
   * - Podcast URL [#f4]_
     - ``podcasturl``
     - 
     - 
     - 
     - ``purl``
     - 
   * - Show Name [#f4]_
     - ``show``
     - 
     - 
     - 
     - ``tvsh``
     - 
   * - Script
     - ``script``
     - ``TXXX:SCRIPT``
     - ``SCRIPT``
     - ``Script``
     - ``----:com.apple.iTunes:SCRIPT``
     - ``WM/Script``
   * - Language
     - ``language``
     - ``TLAN``
     - ``LANGUAGE``
     - ``Language``
     - ``----:com.apple.iTunes:LANGUAGE``
     - ``WM/Language``
   * - MusicBrainz Release Group Id
     - ``musicbrainz_releasegroupid``
     - ``TXXX:MusicBrainz Release Group Id``
     - ``MUSICBRAINZ_RELEASEGROUPID``
     - ``MUSICBRAINZ_RELEASEGROUPID``
     - ``----:com.apple.iTunes:MusicBrainz Release Group Id``
     - ``MusicBrainz/Release Group Id``
   * - MusicBrainz Work Id
     - ``musicbrainz_workid``
     - ``TXXX:MusicBrainz Work Id``
     - ``MUSICBRAINZ_WORKID``
     - ``MUSICBRAINZ_WORKID``
     - ``----:com.apple.iTunes:MusicBrainz Work Id``
     - ``MusicBrainz/Work Id``
   * - License [#f6]_ [#f7]_
     - ``license``
     - ``WCOP`` *(single URL)* ``TXXX:LICENSE`` (multiple or non-URL)
     - ``LICENSE``
     - ``LICENSE``
     - ``----:com.apple.iTunes:LICENSE``
     - ``LICENSE``
   * - Original Year [#f3]_
     - ``originalyear``
     - ``TXXX:originalyear``
     - ``ORIGINALYEAR``
     - ``ORIGINALYEAR``
     - 
     - 
   * - AcoustID
     - ``acoustid_id``
     - ``TXXX:Acoustid Id``
     - ``ACOUSTID_ID``
     - ``ACOUSTID_ID``
     - ``----:com.apple.iTunes:Acoustid Id``
     - ``Acoustid/Id``
   * - AcoustID Fingerprint
     - ``acoustid_fingerprint``
     - ``TXXX:Acoustid Fingerprint``
     - ``ACOUSTID_FINGERPRINT``
     - ``ACOUSTID_FINGERPRINT``
     - ``----:com.apple.iTunes:Acoustid Fingerprint``
     - ``Acoustid/Fingerprint``
   * - Website (official artist website)
     - ``website``
     - ``WOAR``
     - ``WEBSITE``
     - ``Weblink``
     - 
     - 
   * - Work Title (Picard>=1.3)
     - ``work``
     - ``TOAL``
     - ``WORK``
     - ``WORK``
     - 
     - 


.. rubric:: Footnotes

.. [#f1] Taken from the earliest release in the release group
.. [#f2] Used when uncertain whether composer or lyricist.
.. [#f3] This is populated by LastFMPlus plugin and not by stock Picard.
.. [#f4] This is not able to be populated by stock Picard. It may be used and populated by certain plugins.
.. [#f5] For Picard>=1.3 this indicates a VA album; for Picard<=1.2 this
   indicates albums with tracks by different artists (which is incorrect
   e.g. an original album with a duet with a feat. artist would show as a
   Compilation). In neither case does this indicate a MusicBrainz Release
   Group subtype of compilation.
.. [#f6] `Release-level license relationship type`_
.. [#f7] `Recording-level license relationship type`_



.. _Picard: http://picard.musicbrainz.org
.. _Recording-level license relationship type: http://musicbrainz.org/relationship/f25e301d-b87b-4561-86a0-5d2df6d26c0a
.. _Release-level license relationship type: http://musicbrainz.org/relationship/004bd0c3-8a45-4309-ba52-fa99f3aa3d50

