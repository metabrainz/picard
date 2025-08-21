### Custom Columns (User Guide)

Create your own columns in Picard’s File and Album views. You can show a single tag (Field Reference) or the result of a Picard script (Script).

---

### Open the Custom Columns manager

- Right‑click any column header in File or Album view.
- Click “Manage Custom Columns…”.
  - If disabled, uncheck “Lock columns” in the same menu first.

The manager lets you Add…, Edit…, Duplicate, Delete, and “Make It So!” (apply) your changes.

---

### Column types

- **Field Reference**: Show the value of one tag. Enter the field key only, without percent signs. Examples: `artist`, `albumartist`, `catalognumber`, `~bitrate`.
- **Script**: Show the result of a Picard script using functions like `$if()`, `$if2()` and slugs like `%artist%`.

Common options:
- **Field Name**: The column title you’ll see in the header.
- **Type**: Field or Script.
- **Expression**: The field key (Field) or the script (Script).
- **Width**: Leave blank for automatic.
- **Align**: LEFT or RIGHT.
- **Add to views**: Choose File view and/or Album view.
- **Insert after key**: Place the new column after an existing column key (e.g. `title`, `artist`, `album`). Leave empty to append at the end.

Click OK to confirm, then “Make It So!” to apply.

---

### Add a Script column (example)

Goal: Show “Artist – Title” with sensible fallbacks, placed after the Title column.

Steps:
1. Right‑click header → “Manage Custom Columns…” → Add…
2. Set:
   - Field Name: Artist – Title
   - Type: Script
   - Expression:
     ```
     $if(%title%,$if2(%artist%,Unknown Artist) - $if2(%title%,Unknown Title),$if2(%albumartist%,Unknown Artist) - $if2(%album%,Unknown Album))
     ```
   - Align: LEFT
   - Add to views: File view and Album view (both)
   - Insert after key: title
3. Click OK, then “Make It So!”.

Tips:
- Use `%field%` slugs and script functions like `$if()`, `$if2()`, `$upper()`, `$lower()`.
- Keep scripts short for best performance.

---

### Add a Field Reference column (example)

Goal: Show Bitrate as a column in the File view, placed after Length.

Steps:
1. Right‑click header → “Manage Custom Columns…” → Add…
2. Set:
   - Field Name: Bitrate
   - Type: Field
   - Expression: `~bitrate`
   - Align: RIGHT (optional)
   - Add to views: File view (checked), Album view (optional)
   - Insert after key: length
3. Click OK, then “Make It So!”.

Other field ideas: `catalognumber`, `releasecountry`, `media`, `originalyear`, `~channels`.

---

### Show or move your new column

- If you don’t see it immediately, right‑click the header and enable it from the list.
- Drag the header to reorder, or use “Insert after key” when creating/editing.

---

### Edit, duplicate, delete

- Select a row in the manager and click Edit…, Duplicate, or Delete.
- Changes take effect after “Make It So!”. Closing the window also applies pending changes.

---

### Troubleshooting

- Column not visible: Ensure the correct view(s) are selected and enable it from the header menu.
- Wrong position: Provide a valid existing key in “Insert after key” (e.g. `title`, `artist`, `album`, `length`).
- Script errors: Simplify the expression and verify your `%field%` names and functions.

---

### Field Reference keys by context

Use these keys in Field Reference columns (no percent signs). Track and Album rows can show most music tags; File rows can also show technical file info (prefixed here with `~`).

Note: This list focuses on commonly used variables and identifiers. For a complete reference, see Picard’s Variables help.

#### Track (recording/track-level)
- **title**: Track title
- **titlesort**: Title sort name
- **artist**: Track artists (joined)
- **artists**: Track artists (multi-value)
- **artistsort**: Artist sort name(s) (joined)
- **artists_sort**: Artist sort names (multi-value)
- **isrc**: ISRC(s)
- **tracknumber**: Track number on disc
- **musicbrainz_trackid**: Track MBID
- **musicbrainz_recordingid**: Recording MBID
- **musicbrainz_tracknumber**: Track number as shown on release (e.g. A1)
- **recordingtitle**: Recording title
- **recordingcomment**: Recording disambiguation
- **recording_firstreleasedate**: Earliest recording date (YYYY-MM-DD)
- **length**: Track length mins:secs
- **rating**: Community rating 0–5
- **key**: Musical key
- **bpm**: Beats per minute
- **mood**: Mood
- **arranger / conductor / director / engineer / mixer / remixer / djmixer**: Credit roles (multi-value)
- **lyricist / lyricistsort**: Lyricist names / sort
- **writer / writersort**: Writer names / sort
- **performer**: Performers by type (e.g. guitar, vocal)
- **performance_attributes**: e.g. live, cover, medley
- **silence**: 1 if title is “[silence]”
- **video**: 1 if video
- **podcast / podcasturl**: Podcast flag / URL

#### Album / Release (album-level)
- **album**: Release title
- **albumsort**: Release sort name
- **albumartist**: Release artist(s) (joined)
- **albumartists**: Release artists (multi-value)
- **albumartistsort / albumartists_sort**: Release artist sort names
- **albumartists_countries**: Release artist country codes
- **date / releasedate**: Release date (YYYY-MM-DD)
- **releasecountry / releasecountries**: Release country code(s)
- **releasestatus**: official, promotional, bootleg, etc.
- **releasetype / primaryreleasetype / secondaryreleasetype**: Release group types
- **barcode**: Release barcode
- **asin**: Amazon ASIN
- **label**: Record label(s)
- **catalognumber**: Label catalog number(s)
- **discnumber**: Disc number
- **discsubtitle**: Disc subtitle
- **totaldiscs / totaltracks / totalalbumtracks**: Counts
- **releaseannotation / releasecomment**: Release notes / disambiguation
- **releasegroup / releasegroupcomment**: Release group title / comment
- **releasegroup_firstreleasedate**: Earliest date in release group
- **releaselanguage / script**: Language (ISO 639-3) / Script (ISO 15924)
- **gapless**: Gapless playback indicator
- **compilation**: iTunes compilation flag (1 for VA)
- **musicbrainz_albumid**: Release MBID
- **musicbrainz_releasegroupid**: Release Group MBID
- **musicbrainz_discid / discid / musicbrainz_discids**: Disc IDs

#### Work / Composition
- **work**: Work name
- **movement / movementnumber / movementtotal**: Movement info
- **showmovement**: Show work/movement instead of title (1)
- **language**: Work lyric language
- **workcomment**: Work disambiguation

#### Series (by entity)
- **release_series / release_seriesid / release_seriesnumber / release_seriescomment**
- **releasegroup_series / releasegroup_seriesid / releasegroup_seriesnumber / releasegroup_seriescomment**
- **recording_series / recording_seriesid / recording_seriesnumber / recording_seriescomment**
- **work_series / work_seriesid / work_seriesnumber / work_seriescomment**

#### IDs (MBIDs and fingerprints)
- **musicbrainz_artistid / musicbrainz_albumartistid**: Artist MBIDs (multi-value)
- **musicbrainz_workid**: Work MBIDs (multi-value)
- **acoustid_id / acoustid_fingerprint**: AcoustID ID / fingerprint
- **musicip_puid / musicip_fingerprint**: MusicIP IDs (legacy)

#### File (file-level technical info; often entered with tilde in Field Reference)
- **~format**: File format
- **~sample_rate**: Sample rate
- **~bits_per_sample**: Bits per sample
- **~channels**: Number of channels
- **~bitrate**: Bitrate (kbps)
- **~filesize**: File size (bytes)
- **~filename / ~extension**: Name without extension / extension
- **~filepath / ~dirname**: Full path / containing directory
- **~file_created_timestamp / ~file_modified_timestamp**: File timestamps

Other file flags (rarely needed): **datatrack**, **pregap**, **discpregap**.

#### Loudness & gain (analysis)
- **replaygain_track_gain / _peak / _range**
- **replaygain_album_gain / _peak / _range**
- **replaygain_reference_loudness**
- **r128_track_gain / r128_album_gain**

#### Cluster
- Clusters aggregate unmatched files. Field references generally resolve using available file/guessed metadata. Album-only fields may be empty.

---

### Complete field keys (A–Z)

Use without percent signs in Field Reference columns. Brief descriptions are shown for quick lookup.

- **absolutetracknumber**: Track number across all discs
- **acoustid_fingerprint**: AcoustID fingerprint
- **acoustid_id**: AcoustID
- **album**: Release title
- **albumartist**: Release artist(s)
- **albumartists**: Release artists (multi)
- **albumartists_countries**: Release artist country codes
- **albumartists_sort / albumartistsort**: Release artist sort names
- **albumsort**: Release sort title
- **arranger**: Arranger(s)
- **artist**: Track artist(s)
- **artists**: Track artists (multi)
- **artists_countries**: Track artist country codes
- **artists_sort / artistsort**: Artist sort names
- **asin**: Amazon ID
- **barcode**: Release barcode
- **bitrate**: Bitrate (kbps)
- **bits_per_sample**: Bits per sample
- **bpm**: Beats per minute
- **catalognumber**: Catalog number(s)
- **channels**: Audio channels
- **comment**: Release disambiguation comment
- **compilation**: iTunes compilation flag (1 for VA)
- **composer**: Composer(s)
- **composersort**: Composer sort name(s)
- **conductor**: Conductor(s)
- **copyright**: Copyright text
- **datatrack**: 1 if data track
- **date**: Release date (YYYY-MM-DD)
- **director**: Director(s)
- **dirname**: Containing directory name
- **discid**: FreeDB Disc ID
- **discnumber**: Disc number
- **discpregap**: 1 if disc has pregap track
- **discsubtitle**: Disc subtitle
- **djmixer**: DJ-Mixer(s)
- **encodedby**: Encoded by
- **encodersettings**: Encoder settings
- **engineer**: Engineer(s)
- **extension**: File extension
- **file_created_timestamp**: File created timestamp
- **file_modified_timestamp**: File modified timestamp
- **filename**: File name (no extension)
- **filepath**: Full file path
- **filesize**: File size (bytes)
- **format**: File format
- **gapless**: Gapless playback indicator
- **genre**: Genre(s)
- **grouping**: Grouping
- **isrc**: ISRC(s)
- **key**: Musical key
- **label**: Record label(s)
- **language**: Work lyric language
- **length**: Track length mins:secs
- **license**: License
- **lyricist**: Lyricist(s)
- **lyricistsort**: Lyricist sort name(s)
- **lyrics**: Lyrics
- **media**: Medium format (e.g. CD)
- **mixer**: Mixer(s)
- **mood**: Mood
- **movement**: Movement name
- **movementnumber**: Movement number
- **movementtotal**: Movement count
- **multiartist**: 1 if album has multiple primary artists
- **musicbrainz_albumartistid**: Release artist MBID(s)
- **musicbrainz_albumid**: Release MBID
- **musicbrainz_artistid**: Track artist MBID(s)
- **musicbrainz_discid**: MusicBrainz DiscID
- **musicbrainz_discids**: All DiscIDs for release
- **musicbrainz_originalalbumid**: Original release MBID
- **musicbrainz_originalartistid**: Original artist MBID(s)
- **musicbrainz_recordingid**: Recording MBID
- **musicbrainz_releasegroupid**: Release Group MBID
- **musicbrainz_trackid**: Track MBID
- **musicbrainz_tracknumber**: Track number as shown (e.g. A1)
- **musicbrainz_workid**: Work MBID(s)
- **musicip_fingerprint**: MusicIP fingerprint
- **musicip_puid**: MusicIP PUID
- **originalalbum**: Original album title
- **originalartist**: Original artist
- **originaldate**: Original release date (YYYY-MM-DD)
- **originalfilename**: Original file name
- **originalyear**: Original release year (YYYY)
- **performance_attributes**: Performance attributes (e.g. live)
- **performer**: Performer(s) by type
- **podcast**: 1 if podcast
- **podcasturl**: Podcast URL
- **pregap**: 1 if track is pregap
- **primaryreleasetype**: Primary release type
- **producer**: Producer(s)
- **r128_album_gain**: R128 album gain
- **r128_track_gain**: R128 track gain
- **rating**: Community rating 0–5
- **recording_firstreleasedate**: Earliest recording date
- **recording_series / _id / _number / _comment**: Recording series info
- **recordingcomment**: Recording disambiguation
- **recordingtitle**: Recording title
- **release_series / _id / _number / _comment**: Release series info
- **releaseannotation**: Release annotation
- **releasecomment**: Release disambiguation
- **releasecountries / releasecountry**: Release country(ies)
- **releasedate**: Release date (scripting use)
- **releasegroup**: Release group title
- **releasegroup_firstreleasedate**: Earliest RG date
- **releasegroup_series / _id / _number / _comment**: RG series info
- **releasegroupcomment**: RG disambiguation
- **releaselanguage**: Release language
- **releasestatus**: Release status
- **releasetype**: Release group types
- **remixer**: Remixer(s)
- **replaygain_album_gain / _peak / _range**: ReplayGain album
- **replaygain_reference_loudness**: ReplayGain reference
- **replaygain_track_gain / _peak / _range**: ReplayGain track
- **sample_rate**: Sample rate
- **script**: Script (ISO 15924)
- **secondaryreleasetype**: Secondary release types
- **show**: Show name
- **showmovement**: Show work & movement flag (1)
- **showsort**: Show sort name
- **silence**: 1 if title is “[silence]”
- **subtitle**: Subtitle
- **syncedlyrics**: Synced lyrics
- **title**: Track title
- **titlesort**: Title sort name
- **totalalbumtracks**: Total tracks across album
- **totaldiscs**: Total discs
- **totaltracks**: Total tracks on disc
- **tracknumber**: Track number
- **video**: 1 if video
- **website**: Artist website
- **work**: Work title
- **work_series / _id / _number / _comment**: Work series info
- **workcomment**: Work disambiguation
- **writer**: Writer(s)
- **writersort**: Writer sort name(s)
