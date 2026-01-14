# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
# Copyright (C) 2025 Bob Swift
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from picard.const import PICARD_URLS
from picard.i18n import N_
from picard.tags.tagvar import (
    DocumentLink,
    TagVar,
    TagVars,
)
from picard.util import get_url


ALL_TAGS = TagVars(
    TagVar(
        'absolutetracknumber',
        shortdesc=N_('Absolute Track No.'),
        longdesc=N_(
            'The absolute number of this track disregarding the disc number. For example, '
            'this value would be 11 for the second track on disc 2 where disc 1 has 9 tracks.'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'acoustid_fingerprint',
        shortdesc=N_('AcoustID Fingerprint'),
        longdesc=N_(
            'The Acoustic Fingerprint for the track. The fingerprint is based on the audio information '
            'found in a file, and is calculated using the Chromaprint software.'
        ),
        is_calculated=True,
        is_from_mb=False,
        related_options=('fingerprinting_system', 'save_acoustid_fingerprints'),
    ),
    TagVar(
        'acoustid_id',
        shortdesc=N_('AcoustID'),
        longdesc=N_(
            'The AcoustID associated with the track. The AcoustID is the identifier assigned to an audio '
            'file based on its acoustic fingerprint. Multiple fingerprints may be assigned the same AcoustID '
            'if the fingerprints are similar enough.'
        ),
        is_calculated=True,
        is_from_mb=False,
        related_options=('fingerprinting_system', 'save_acoustid_fingerprints'),
    ),
    TagVar(
        'albumartist',
        shortdesc=N_('Album Artist'),
        longdesc=N_(
            'The artists primarily credited on the release, separated by the specified join phrases. '
            'These could be either "standardized" or "as credited" depending on whether the "Use '
            'standardized artist names" metadata option is enabled.'
        ),
        is_filterable=True,
    ),
    TagVar(
        'albumartists',
        shortdesc=N_('Album Artists'),
        longdesc=N_(
            'The artists primarily credited on the release. These could be either "standardized" or '
            '"as credited" depending on whether the "Use standardized artist names" metadata option is enabled.'
        ),
        is_hidden=True,
        is_tag=False,
        is_multi_value=True,
    ),
    TagVar(
        'albumartists_countries',
        shortdesc=N_('Album Artists Countries'),
        longdesc=N_(
            'The country codes for all of the credited album artists, in the same order as the artists. '
            'Duplicate country codes will be shown if there are more than one artist from the same country. '
            'If a country code is not provided by the webservice the code "XX" will be used to indicate an '
            'unknown country.'
        ),
        is_hidden=True,
        is_tag=False,
        is_multi_value=True,
    ),
    TagVar(
        'albumartistsort',
        shortdesc=N_('Album Artist Sort Order'),
        longdesc=N_('The release artists sort names, separated by the specified join phrases. (e.g.: "Beatles, The")'),
    ),
    TagVar(
        'albumartists_sort',
        shortdesc=N_('Album Artists Sort Names'),
        longdesc=N_("The sort names of the album's artists."),
        is_hidden=True,
        is_tag=False,
        is_multi_value=True,
    ),
    TagVar(
        'album',
        shortdesc=N_('Album'),
        longdesc=N_('The title of the release.'),
        is_filterable=True,
    ),
    TagVar(
        'albumsort',
        shortdesc=N_('Album Sort Order'),
        longdesc=N_('The sort name of the title of the release.'),
        is_from_mb=False,
    ),
    TagVar(
        'arranger',
        shortdesc=N_('Arranger'),
        longdesc=N_(
            'The names of the arrangers associated with the track. These can include the instrument '
            'and orchestra arrangers, and could be associated with the release, recording or work.'
        ),
        is_filterable=True,
    ),
    TagVar(
        'artist',
        shortdesc=N_('Artist'),
        longdesc=N_(
            'The track artist names, separated by the specified join phrases. These could be either '
            '"standardized" or "as credited" depending on whether the "Use standardized artist names" '
            'metadata option is enabled.'
        ),
        is_filterable=True,
    ),
    TagVar(
        'artists',
        shortdesc=N_('Artists'),
        longdesc=N_(
            'The track artist names. These could be either "standardized" or "as credited" depending on '
            'whether the "Use standardized artist names" metadata option is enabled.'
        ),
        is_multi_value=True,
    ),
    TagVar(
        'artists_countries',
        shortdesc=N_('Artists Countries'),
        longdesc=N_(
            'The country codes for all of the credited track artists, in the same order as the artists. '
            'Duplicate country codes will be shown if there are more than one artist from the same country. '
            'If a country code is not provided by the webservice the code "XX" will be used to indicate an '
            'unknown country.'
        ),
        is_hidden=True,
        is_tag=False,
        is_multi_value=True,
    ),
    TagVar(
        'artistsort',
        shortdesc=N_('Artist Sort Order'),
        longdesc=N_("The sort names of the track's artists, separated by the specified join phrases."),
    ),
    TagVar(
        'artists_sort',
        shortdesc=N_('Artists Sort Names'),
        longdesc=N_("The sort names of the track's artists."),
        is_hidden=True,
        is_tag=False,
        is_multi_value=True,
    ),
    TagVar(
        'asin',
        shortdesc=N_('ASIN'),
        longdesc=N_('The Amazon Standard Identification Number, which is the number identifying the item on Amazon.'),
        is_filterable=True,
    ),
    TagVar(
        'barcode',
        shortdesc=N_('Barcode'),
        longdesc=N_('The barcode assigned to the release.'),
        doc_links=(
            DocumentLink(N_('Barcode in MusicBrainz documentation'), PICARD_URLS['mb_doc'] + 'Barcode'),
            DocumentLink(
                N_('Barcode mapping in Picard documentation'),
                get_url('/appendices/tag_mapping.html#id6'),
            ),
        ),
        is_filterable=True,
    ),
    TagVar(
        'bpm',
        shortdesc=N_('BPM'),
        longdesc=N_('Beats per minute of the track.'),
        is_from_mb=False,
    ),
    TagVar(
        'bitrate',
        shortdesc=N_('Bitrate'),
        longdesc=N_('Approximate bitrate in kbps.'),
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'bits_per_sample',
        shortdesc=N_('Bits per sample'),
        longdesc=N_('Bits of data per sample.'),
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'catalognumber',
        shortdesc=N_('Catalog Number'),
        longdesc=N_(
            'The catalog numbers assigned to the release by the labels, which can often be found on the spine '
            'or near the barcode. There may be more than one, especially when multiple labels are involved.'
        ),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'channels',
        shortdesc=N_('Channels'),
        longdesc=N_('Number of audio channels in the file.'),
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'comment',
        shortdesc=N_('Comment'),
        longdesc=N_(
            'The disambiguation comment entered to help distinguish one release from another (e.g.: '
            'Deluxe version with 2 bonus tracks).'
        ),
        is_populated_by_picard=False,
        see_also=('_releasecomment',),
    ),
    TagVar(
        'compilation',
        shortdesc=N_('Compilation (iTunes)'),
        longdesc=N_('1 for Various Artist albums, otherwise empty.'),
    ),
    TagVar(
        'composer',
        shortdesc=N_('Composer'),
        longdesc=N_('The names of the composers for the associated work.'),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'composersort',
        shortdesc=N_('Composer Sort Order'),
        longdesc=N_('The sort names of the composers for the associated work.'),
        is_multi_value=True,
    ),
    TagVar(
        'conductor',
        shortdesc=N_('Conductor'),
        longdesc=N_(
            'The names of the conductors associated with the track. These can include the conductor '
            'and chorus master, and could be associated with the release or recording.'
        ),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'copyright',
        shortdesc=N_('Copyright'),
        longdesc=N_(
            'The copyright message for the copyright holder of the original sound, beginning with a '
            'year and a space character.'
        ),
        is_from_mb=False,
    ),
    TagVar(
        'datatrack',
        shortdesc=N_('Data Track'),
        longdesc=N_('Set to 1 if the track is a "data track", otherwise empty.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'date',
        shortdesc=N_('Date'),
        longdesc=N_('The date that the release (album) was issued, in the format `YYYY-MM-DD`.'),
        is_filterable=True,
    ),
    TagVar(
        'director',
        shortdesc=N_('Director'),
        longdesc=N_(
            'The director of a track as provided by the "*Video Director*" or "*Audio Director*" relationship '
            'in MusicBrainz.'
        ),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'dirname',
        shortdesc=N_('Directory name'),
        longdesc=N_('The name of the directory containing the file at the point of being loaded into Picard.'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'discid',
        shortdesc=N_('FreeDB Disc ID'),
        longdesc=N_('The identification number of the disc in the FreeDB database.'),
        see_also=('musicbrainz_discid',),
        doc_links=(
            DocumentLink(N_('FreeDB'), 'https://wikipedia.org/wiki/Freedb'),
            DocumentLink(
                N_('FreeDB DiscID Calculation'),
                'https://wikipedia.org/wiki/CDDB#Example_calculation_of_a_CDDB1_(FreeDB)_disc_ID',
            ),
            DocumentLink(
                N_('FreeDB DiscID including Calculation Example (French)'), 'https://fr.wikipedia.org/wiki/DiscId'
            ),
        ),
        is_filterable=True,
    ),
    TagVar(
        'discnumber',
        shortdesc=N_('Disc Number'),
        longdesc=N_('The number of the disc in the release that contains this track.'),
        is_filterable=True,
    ),
    TagVar(
        'discpregap',
        shortdesc=N_('Disc Has Pregap'),
        longdesc=N_('Set to 1 if the disc the track is on has a "pregap track", otherwise empty.'),
        is_hidden=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'discsubtitle',
        shortdesc=N_('Disc Subtitle'),
        longdesc=N_('The media title given to a specific disc in the release.'),
        is_filterable=True,
    ),
    TagVar(
        'djmixer',
        shortdesc=N_('DJ-Mixer'),
        longdesc=N_('The names of the DJ mixers for the track.'),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'encodedby',
        shortdesc=N_('Encoded By'),
        longdesc=N_('The person or organization that encoded the track.'),
        is_from_mb=False,
    ),
    TagVar(
        'encodersettings',
        shortdesc=N_('Encoder Settings'),
        longdesc=N_('The settings used when encoding the track.'),
        is_from_mb=False,
    ),
    TagVar(
        'engineer',
        shortdesc=N_('Engineer'),
        longdesc=N_('The names of the engineers associated with the track.'),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'extension',
        shortdesc=N_('File Extension'),
        longdesc=N_("The file's extension."),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'file_created_timestamp',
        shortdesc=N_('File Created Timestamp'),
        longdesc=N_('The file creation timestamp in the form `YYYY-MM-DD HH:MM:SS` as reported by the file system.'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'file_modified_timestamp',
        shortdesc=N_('File Modified Timestamp'),
        longdesc=N_(
            'The file modification timestamp in the form `YYYY-MM-DD HH:MM:SS` as reported by the file system.'
        ),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'filename',
        shortdesc=N_('File Name'),
        longdesc=N_('The name of the file without extension.'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
        is_filterable=True,
    ),
    TagVar(
        'filepath',
        shortdesc=N_('File Path'),
        longdesc=N_('Full path and name of the file.'),
        is_hidden=True,
        is_tag=False,
        is_from_mb=False,
        is_filterable=True,
    ),
    TagVar(
        'filesize',
        shortdesc=N_('File Size'),
        longdesc=N_('Size of the file in bytes.'),
        is_file_info=True,
        is_hidden=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'format',
        shortdesc=N_('File Format'),
        longdesc=N_('Media format of the file (e.g.: MPEG-1 Audio).'),
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'gapless',
        shortdesc=N_('Gapless Playback'),
        longdesc=N_('Indicates whether or not there are gaps between the recordings on the release.'),
        is_from_mb=False,
    ),
    TagVar(
        'genre',
        shortdesc=N_('Genre'),
        longdesc=N_('The specified genre information from MusicBrainz.'),
        related_options=('use_genres',),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        # TODO: Check if this actually exists or if it was provided by the last.fm plugin.
        'grouping',
        shortdesc=N_('Grouping'),
        longdesc=N_('Genre grouping associated with the track'),
        is_from_mb=False,
    ),
    TagVar(
        'isrc',
        shortdesc=N_('ISRC'),
        longdesc=N_(
            'The International Standard Recording Code, which is an international standard code for uniquely '
            'identifying sound recordings and music video recordings.'
        ),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'key',
        shortdesc=N_('Key'),
        longdesc=N_('The key of the music.'),
        is_from_mb=False,
    ),
    TagVar(
        'label',
        shortdesc=N_('Record Label'),
        longdesc=N_('The names of the labels associated with the release.'),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'language',
        shortdesc=N_('Language'),
        longdesc=N_('Work lyric language as per ISO 639-3 if a related work exists.'),
        is_filterable=True,
    ),
    TagVar(
        'length',
        shortdesc=N_('Length'),
        longdesc=N_('The length of the track in format mins:secs.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'license',
        shortdesc=N_('License'),
        longdesc=N_('The license associated with the track, either through the release or recording relationships.'),
    ),
    TagVar(
        'lyricist',
        shortdesc=N_('Lyricist'),
        longdesc=N_('The names of the lyricists for the associated work.'),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'lyricistsort',
        shortdesc=N_('Lyricist Sort'),
        longdesc=N_('The sort names of the lyricists for the associated work.'),
        is_multi_value=True,
        is_hidden=True,
    ),
    TagVar(
        'lyrics',
        shortdesc=N_('Lyrics'),
        longdesc=N_('The lyrics for the track.'),
        is_from_mb=False,
        is_filterable=True,
    ),
    TagVar(
        'media',
        shortdesc=N_('Media'),
        longdesc=N_('The media on which the release was distributed (e.g.: CD).'),
        is_filterable=True,
    ),
    TagVar(
        'mixer',
        shortdesc=N_('Mixer'),
        longdesc=N_('The names of the "*Mixed By*" engineers associated with the track.'),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'mood',
        shortdesc=N_('Mood'),
        longdesc=N_('The mood associated with the track.'),
        is_from_mb=False,
    ),
    TagVar(
        'movement',
        shortdesc=N_('Movement'),
        longdesc=N_('Name of the movement (e.g.: "Andante con moto").'),
        is_from_mb=False,
    ),
    TagVar(
        'movementnumber',
        shortdesc=N_('Movement Number'),
        longdesc=N_(
            'Movement number in Arabic numerals (e.g.: "2"). Players explicitly supporting this tag will often '
            'display it in Roman numerals (e.g.: "II").'
        ),
        is_from_mb=False,
    ),
    TagVar(
        'movementtotal',
        shortdesc=N_('Movement Count'),
        longdesc=N_('Total number of movements in the work (e.g.: "4").'),
        is_from_mb=False,
    ),
    TagVar(
        'multiartist',
        shortdesc=N_('Multiple Artists'),
        longdesc=N_('Set to 1 if not all of the tracks on the album have the same primary artist, otherwise empty.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'musicbrainz_albumartistid',
        shortdesc=N_('Release Artist MBID'),
        longdesc=N_('The MusicBrainz Identifiers (MBIDs) for the release artists.'),
        is_multi_value=True,
    ),
    TagVar(
        'musicbrainz_albumid',
        shortdesc=N_('Release MBID'),
        longdesc=N_('The MusicBrainz Identifier (MBID) for the release.'),
    ),
    TagVar(
        'musicbrainz_artistid',
        shortdesc=N_('Artist MBID'),
        longdesc=N_('The MusicBrainz Identifiers (MBIDs) for the track artists.'),
        is_multi_value=True,
    ),
    TagVar(
        'musicbrainz_discid',
        shortdesc=N_('MusicBrainz DiscID'),
        longdesc=N_(
            'The Disc ID is the code number which MusicBrainz uses to link a physical CD to a release listing. '
            'This is based on the table of contents (TOC) information read from the disc. This tag contains the '
            'Disc ID if the album information was retrieved using `Tools > Lookup CD` from the menu.'
        ),
        see_also=('discid',),
        is_calculated=True,
        doc_links=(DocumentLink(N_('Disc ID Calculation'), PICARD_URLS['mb_doc'] + 'Disc_ID_Calculation'),),
    ),
    TagVar(
        'musicbrainz_discids',
        shortdesc=N_('Disc IDs'),
        longdesc=N_(
            'A list of all of the disc ids attached to the selected release. The list provided for each medium only '
            'includes the disc ids attached to that medium.'
        ),
        additionaldesc=N_(
            'For example, the list provided for Disc 1 of a three CD set will not include the disc ids attached to '
            'discs 2 and 3 of the set.'
        ),
        is_hidden=True,
        is_tag=False,
        is_multi_value=True,
    ),
    TagVar(
        'musicbrainz_originalalbumid',
        shortdesc=N_('Original Release MBID'),
        longdesc=N_(
            'The MusicBrainz Identifier (MBID) for the original release. This is only available if the release '
            'has been merged with another release.'
        ),
    ),
    TagVar(
        'musicbrainz_originalartistid',
        shortdesc=N_('Original Artist MBID'),
        longdesc=N_(
            'The MusicBrainz Identifiers (MBIDs) for the track artists of the original recording. This is only '
            'available if the recording has been merged with another recording.'
        ),
        is_multi_value=True,
    ),
    TagVar(
        'musicbrainz_recordingid',
        shortdesc=N_('Recording MBID'),
        longdesc=N_('The MusicBrainz Identifier (MBID) for the recording.'),
    ),
    TagVar(
        'musicbrainz_releasegroupid',
        shortdesc=N_('Release Group MBID'),
        longdesc=N_('The MusicBrainz Identifier (MBID) for the release group.'),
    ),
    TagVar(
        'musicbrainz_trackid',
        shortdesc=N_('Track MBID'),
        longdesc=N_('The MusicBrainz Identifier (MBID) for the track.'),
    ),
    TagVar(
        'musicbrainz_tracknumber',
        shortdesc=N_('Track Number Shown'),
        longdesc=N_('The track number written as on the MusicBrainz release, such as vinyl numbering (A1, A2, etc.)'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'musicbrainz_workid',
        shortdesc=N_('Work MBID'),
        longdesc=N_('The MusicBrainz Identifier (MBID) for the Work if a related work exists.'),
        is_multi_value=True,  # TODO: Need to confirm multi-value.
    ),
    TagVar(
        'musicip_fingerprint',
        shortdesc=N_('MusicIP Fingerprint'),
        longdesc=N_('The MusicIP Fingerprint for the track.'),
        is_from_mb=False,
    ),
    TagVar(
        'musicip_puid',
        shortdesc=N_('MusicIP PUID'),
        longdesc=N_('The MusicIP PUIDs associated with the track.'),
        is_from_mb=False,
    ),
    TagVar(
        'originalalbum',
        shortdesc=N_('Original Album'),
        longdesc=N_(
            'The release title of the earliest release in the release group intended for the title of the '
            'original recording.'
        ),
        is_from_mb=False,
    ),
    TagVar(
        'originalartist',
        shortdesc=N_('Original Artist'),
        longdesc=N_(
            'The track artist of the earliest release in the release group intended for the performers of '
            'the original recording.'
        ),
        is_from_mb=False,
    ),
    TagVar(
        'originaldate',
        shortdesc=N_('Original Release Date'),
        longdesc=N_(
            'The original release date in the format `YYYY-MM-DD`. By default this is set to the earliest '
            'release in the release group. This can provide, for example, the release date of the vinyl '
            'version of what you have on CD.\n\n**Note:** If you are storing tags in MP3 files as '
            'ID3v2.3 then the original date can only be stored as a year.'
        ),
    ),
    TagVar(
        'originalfilename',
        shortdesc=N_('Original Filename'),
        longdesc=N_('The original name of the audio file.'),
        is_from_mb=False,
    ),
    TagVar(
        'originalyear',
        shortdesc=N_('Original Year'),
        longdesc=N_(
            'The year of the original release date in the format `YYYY`. By default this is set to the earliest '
            'release in the release group. This can provide, for example, the release year of the vinyl version '
            'of what you have on CD.'
        ),
    ),
    TagVar(
        'performance_attributes',
        shortdesc=N_('Performance Attributes'),
        longdesc=N_('List of performance attributes for the work (e.g.: "*live*", "*cover*", "*medley*").'),
        additionaldesc=N_(
            'Use `$inmulti()` to check for a specific type (e.g.: `$if($inmulti(%_performance_attributes%,medley), '
            '(Medley),)`).'
        ),
        is_multi_value=True,
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'performer',
        shortdesc=N_('Performer'),
        longdesc=N_(
            'The names of the performers for the specified type. These types include:\n\n'
            '- vocals or instruments for the associated release or recording, where "type" can be "*vocal*", '
            '"*guest guitar*", "*solo violin*", etc.\n'
            '- the orchestra for the associated release or recording, where "type" is "*orchestra*"\n'
            '- the concert master for the associated release or recording, where "type" is "*concertmaster*"'
        ),
        is_multi_value=True,  # TODO: Confirm that this is a multi-value
        is_filterable=True,
    ),
    TagVar(
        'podcast',
        shortdesc=N_('Podcast'),
        longdesc=N_('Indicates whether or not the recording is a podcast.'),
        is_from_mb=False,
    ),
    TagVar(
        'podcasturl',
        shortdesc=N_('Podcast URL'),
        longdesc=N_('The associated URL if the recording is a podcast.'),
        is_from_mb=False,
    ),
    TagVar(
        'pregap',
        shortdesc=N_('Pregap Track'),
        longdesc=N_('Set to 1 if the track is a "pregap track", otherwise empty.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'primaryreleasetype',
        shortdesc=N_('Primary Release Type'),
        longdesc=N_('The primary type of the release group (i.e.: *album*, *single*, *ep*, *broadcast*, or *other*).'),
        is_hidden=True,
        is_tag=False,
        see_also=('releasetype', '_secondaryreleasetype'),
        doc_links=(DocumentLink(N_('Release group types'), PICARD_URLS['mb_doc'] + 'Release_Group/Type'),),
    ),
    TagVar(
        'producer',
        shortdesc=N_('Producer'),
        longdesc=N_('The names of the producers for the associated release or recording.'),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'r128_album_gain',
        shortdesc=N_('R128 Album Gain'),
        longdesc=N_('Album gain as determined by European Broadcasting Union "R 128" analysis.'),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'r128_track_gain',
        shortdesc=N_('R128 Track Gain'),
        longdesc=N_('Track gain as determined by European Broadcasting Union "R 128" analysis.'),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'rating',
        shortdesc=N_('Rating'),
        longdesc=N_('The rating of the track from 0-5 by MusicBrainz users.'),
        is_hidden=True,
    ),
    TagVar(
        'recording_firstreleasedate',
        shortdesc=N_('Recording First Released'),
        longdesc=N_('The date of the earliest recording for a track in the format `YYYY-MM-DD`.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'recording_series',
        shortdesc=N_('Recording Series'),
        longdesc=N_('The series titles associated with the recording.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'recording_seriescomment',
        shortdesc=N_('Recording Series Comment'),
        longdesc=N_('The series disambiguation comments associated with the recording.'),
        is_multi_value=True,
        is_hidden=True,
    ),
    TagVar(
        'recording_seriesid',
        shortdesc=N_('Recording Series MBID'),
        longdesc=N_('The series MusicBrainz Identifiers (MBIDs) associated with the recording.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'recording_seriesnumber',
        shortdesc=N_('Recording Series Number'),
        longdesc=N_('The series numbers associated with the recording.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'recordingcomment',
        shortdesc=N_('Recording Comment'),
        longdesc=N_('The disambiguation comment for the recording associated with a track.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'recordingtitle',
        shortdesc=N_('Recording Title'),
        longdesc=N_('Recording title - normally the same as the track title, but can be different.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releaseannotation',
        shortdesc=N_('Release Annotation'),
        longdesc=N_('The annotation comment for the release.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasecomment',
        shortdesc=N_('Release Comment'),
        longdesc=N_('The disambiguation comment for the release.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasecountries',
        shortdesc=N_('Release Countries'),
        longdesc=N_('The complete list of release countries for the release.'),
        is_hidden=True,
        is_tag=False,
        is_multi_value=True,
    ),
    TagVar(
        'releasecountry',
        shortdesc=N_('Release Country'),
        longdesc=N_(
            'The two-character code for the country in which the release was issued. If more than one release country '
            'was specified, this tag will contain the first one in the list.'
        ),
        is_filterable=True,
    ),
    TagVar(
        'releasedate',
        shortdesc=N_('Release Date'),
        longdesc=N_('The date that the release (album) was issued, in the format `YYYY-MM-DD`.'),
        additionaldesc=N_(
            'This tag exists for specific use in scripts and plugins, but is not filled by default. In most cases it is '
            'recommended to use the `%date%` tag instead for compatibility with existing software.'
        ),
        is_from_mb=False,
        see_also=('date',),
    ),
    TagVar(
        'releasegroup',
        shortdesc=N_('Release Group'),
        longdesc=N_(
            'The title of the release group. This is typically the same as the album title, but can be different.'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasegroup_firstreleasedate',
        shortdesc=N_('RG First Released'),
        longdesc=N_(
            'The date of the earliest release in the release group in the format `YYYY-MM-DD`. This is intended to '
            'provide, for example, the release date of the vinyl version of what you have on CD.'
        ),
        is_hidden=True,
        is_tag=False,
        see_also=('originaldate',),
    ),
    TagVar(
        'releasegroup_series',
        shortdesc=N_('RG Series'),
        longdesc=N_('The series titles associated with the release group.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'releasegroup_seriescomment',
        shortdesc=N_('RG Series Comment'),
        longdesc=N_('The series disambiguation comments associated with the release group.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'releasegroup_seriesid',
        shortdesc=N_('RG Series MBID'),
        longdesc=N_('The series MusicBrainz Identifiers (MBIDs) associated with the release group.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'releasegroup_seriesnumber',
        shortdesc=N_('RG Series Number'),
        longdesc=N_('The series numbers associated with the release group.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'releasegroupcomment',
        shortdesc=N_('RG Comment'),
        longdesc=N_('The disambiguation comment for the release group.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releaselanguage',
        shortdesc=N_('Release Language'),
        longdesc=N_('The language of the release as per ISO 639-3.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'release_series',
        shortdesc=N_('Release Series'),
        longdesc=N_('The series titles associated with the release.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'release_seriescomment',
        shortdesc=N_('Release Series Comment'),
        longdesc=N_('The series disambiguation comments associated with the release.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'release_seriesid',
        shortdesc=N_('Release Series MBID'),
        longdesc=N_('The series MusicBrainz Identifiers (MBIDs) associated with the release.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'release_seriesnumber',
        shortdesc=N_('Release Series Number'),
        longdesc=N_('The series numbers associated with the release.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'releasestatus',
        shortdesc=N_('Release Status'),
        longdesc=N_(
            'An indicator of the "official" status of the release. Possible values include "*official*", '
            '"*promotional*", "*bootleg*", and "*pseudo-release*".'
        ),
        is_filterable=True,
    ),
    TagVar(
        'releasetype',
        shortdesc=N_('Release Type'),
        longdesc=N_('The types of release assigned to the release group.'),
        is_multi_value=True,
        see_also=('_primaryreleasetype', '_secondaryreleasetype'),
        doc_links=(DocumentLink(N_('Release group types'), PICARD_URLS['mb_doc'] + 'Release_Group/Type'),),
        is_filterable=True,
    ),
    TagVar(
        'remixer',
        shortdesc=N_('Remixer'),
        longdesc=N_('The names of the remixer engineers associated with the track.'),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'replaygain_album_gain',
        shortdesc=N_('ReplayGain Album Gain'),
        longdesc=N_('Album gain setting resulting from ReplayGain analysis of the album.'),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_album_peak',
        shortdesc=N_('ReplayGain Album Peak'),
        longdesc=N_('Album peak setting resulting from ReplayGain analysis of the album.'),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_album_range',
        shortdesc=N_('ReplayGain Album Range'),
        longdesc=N_('Album range setting resulting from ReplayGain analysis of the album.'),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_reference_loudness',
        shortdesc=N_('ReplayGain Reference Loudness'),
        longdesc=N_('Album reference loudness setting resulting from ReplayGain analysis of the album.'),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_track_gain',
        shortdesc=N_('ReplayGain Track Gain'),
        longdesc=N_('Track gain setting resulting from ReplayGain analysis of the track.'),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_track_peak',
        shortdesc=N_('ReplayGain Track Peak'),
        longdesc=N_('Track peak setting resulting from ReplayGain analysis of the track.'),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_track_range',
        shortdesc=N_('ReplayGain Track Range'),
        longdesc=N_('Track range setting resulting from ReplayGain analysis of the track.'),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'sample_rate',
        shortdesc=N_('Sample Rate'),
        longdesc=N_('The sample rate of the audio file.'),
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'script',
        shortdesc=N_('Script'),
        longdesc=N_(
            "The script used to write the release's track list. The possible values are taken from the "
            'ISO 15924 standard.'
        ),
        is_filterable=True,
    ),
    TagVar(
        'secondaryreleasetype',
        shortdesc=N_('Secondary Release Type'),
        longdesc=N_(
            'Zero or more secondary types (i.e.: *audiobook*, *compilation*, *dj-mix*, *interview*, '
            '*live*, *mixtape/street*, *remix*, *soundtrack*, or *spokenword*) for the release group.'
        ),
        is_hidden=True,
        is_tag=False,
        is_multi_value=True,
        see_also=('releasetype', '_primaryreleasetype'),
        doc_links=(DocumentLink(N_('Release group types'), PICARD_URLS['mb_doc'] + 'Release_Group/Type'),),
    ),
    TagVar(
        'silence',
        shortdesc=N_('Silence'),
        longdesc=N_('1 if the track title is "[silence]"'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'show',
        shortdesc=N_('Show Name'),
        longdesc=N_('The name of the show if the recording is associated with a television program.'),
        is_from_mb=False,
    ),
    TagVar(
        'showmovement',
        shortdesc=N_('Show Work & Movement'),
        longdesc=N_(
            'Show work and movement. If this tag is set to "1" players supporting this tag, such as iTunes and MusicBee, '
            'will display the work, movement number and movement name instead of the track title.'
        ),
        additionaldesc=N_(
            'For example, the track will be displayed as "Symphony no. 5 in C minor, op. 67: II. Andante con moto" '
            'regardless of the value of the title tag.'
        ),
        is_from_mb=False,
    ),
    TagVar(
        'showsort',
        shortdesc=N_('Show Name Sort Order'),
        longdesc=N_('The sort name of the show if the recording is associated with a television program.'),
        is_from_mb=False,
    ),
    TagVar(
        'subtitle',
        shortdesc=N_('Subtitle'),
        longdesc=N_('This is used for information directly related to the contents title.'),
        is_from_mb=False,
    ),
    TagVar(
        'syncedlyrics',
        shortdesc=N_('Synced Lyrics'),
        longdesc=N_('Synchronized lyrics for the track.'),
        is_from_mb=False,
    ),
    TagVar(
        'title',
        shortdesc=N_('Title'),
        longdesc=N_('The title of the track.'),
        is_filterable=True,
    ),
    TagVar(
        'titlesort',
        shortdesc=N_('Title Sort Order'),
        longdesc=N_('The sort name of the track title.'),
        is_from_mb=False,
    ),
    TagVar(
        'totalalbumtracks',
        shortdesc=N_('Total Album Tracks'),
        longdesc=N_('The total number of tracks across all discs of this release.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'totaldiscs',
        shortdesc=N_('Total Discs'),
        longdesc=N_('The total number of discs in this release.'),
    ),
    TagVar(
        'totaltracks',
        shortdesc=N_('Total Tracks'),
        longdesc=N_('The total number of tracks on this disc.'),
    ),
    TagVar(
        'tracknumber',
        shortdesc=N_('Track Number'),
        longdesc=N_('The number of the track on the disc.'),
    ),
    TagVar(
        'video',
        shortdesc=N_('Video'),
        longdesc=N_('Set to "1" if the track is a video.'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'website',
        shortdesc=N_('Artist Website'),
        longdesc=N_('The official website for the artist.'),
        is_filterable=True,
    ),
    TagVar(
        'work',
        shortdesc=N_('Work'),
        longdesc=N_('The name of the work associated with the track (e.g.: "Symphony no. 5 in C minor, op. 67").'),
        additionaldesc=N_(
            'Note: If you are using iTunes together with MP3 files you should activate the "Save iTunes compatible '
            'grouping and work" option in order for the work to be displayed correctly.'
        ),
        related_options=('itunes_compatible_grouping',),
        is_filterable=True,
    ),
    TagVar(
        'work_series',
        shortdesc=N_('Work Series'),
        longdesc=N_('The series titles associated with the work.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'work_seriescomment',
        shortdesc=N_('Work Series Comment'),
        longdesc=N_('The series disambiguation comments associated with the work.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'work_seriesid',
        shortdesc=N_('Work Series MBID'),
        longdesc=N_('The series MusicBrainz Identifiers (MBIDs) associated with the work.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'work_seriesnumber',
        shortdesc=N_('Work Series Number'),
        longdesc=N_('The series numbers associated with the work.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'workcomment',
        shortdesc=N_('Work Comment'),
        longdesc=N_('The disambiguation comment associated with the work.'),
        is_hidden=True,
    ),
    TagVar(
        'writer',
        shortdesc=N_('Writer'),
        longdesc=N_(
            'The names of the writers associated with the related work. This is not written to most file formats '
            'automatically.'
        ),
        additionaldesc=N_('You can merge this with composers with a script like `$copymerge(composer,writer)`.'),
        is_multi_value=True,
        is_filterable=True,
    ),
    TagVar(
        'writersort',
        shortdesc=N_('Writer Sort'),
        longdesc=N_('The sort names of the writers for the work.'),
        is_hidden=True,
        is_multi_value=True,
    ),
    TagVar(
        'broadcast_date',
        shortdesc=N_('Broadcast Date'),
        longdesc=N_('The date the recording was broadcasted.'),
        is_hidden=True,
    ),
)
