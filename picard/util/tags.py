# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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

TAG_NAMES = {
    'acoustid_fingerprint': N_(u'AcoustID Fingerprint'),
    'acoustid_id': N_(u'AcoustID'),
    'album': N_(u'Album'),
    'albumartist': N_(u'Album Artist'),
    'albumartists': N_(u'Album Artists'),
    'albumartistsort': N_(u'Album Artist Sort Order'),
    'albumgenre': N_(u'Album Genre'),
    'albumrating': N_(u'Album Rating'),
    'albumsort': N_(u'Album Sort Order'),
    'arranger': N_(u'Arranger'),
    'artist': N_(u'Artist'),
    'artists': N_(u'Artists'),
    'artistsort': N_(u'Artist Sort Order'),
    'asin': N_(u'Amazon ASIN'),
    'barcode': N_(u'Barcode'),
    'bpm': N_(u'BPM'),
    'catalognumber': N_(u'Catalog Number'),
    'category': N_(u'Category'),
    'comment': N_(u'Comment'),
    'compilation': N_(u'Compilation (iTunes)?'),
    'composer': N_(u'Composer'),
    'composersort': N_(u'Composer Sort Order'),
    'conductor': N_(u'Conductor'),
    'copyright': N_(u'\xa9 Copyright'),
    'country': N_(u'Country'),
    'date': N_(u'Release Date'),
    'discnumber': N_(u'Disc Number'),
    'discsubtitle': N_(u'Disc Subtitle'),
    'djmixer': N_(u'DJ-Mixer'),
    'encodedby': N_(u'Encoded By'),
    'encodersettings': N_(u'Encoder Settings'),
    'encodingtime': N_(u'Encoding Time'),
    'engineer': N_(u'Engineer'),
    # Retired in favour of playdelay which is more flexible - gapless=playdelay==0
    #'gapless': N_(u'Gapless?'),
    'genre': N_(u'Genre'),
    'grouping': N_(u'Grouping'),
    'isrc': N_(u'ISRC'),
    'key': N_(u'Musical Key'),
    'keywords': N_(u'Keywords'),
    'label': N_(u'Record Label'),
    'language': N_(u'Language'),
    'license': N_(u'License Webpage'),
    'lyricist': N_(u'Lyricist'),
    'lyrics': N_(u'Lyrics'),
    'media': N_(u'Media'),
    'mixer': N_(u'Mixer'),
    'mood': N_(u'Mood'),
    'musicbrainz_albumartistid': N_(u'MusicBrainz Release Artist Id'),
    'musicbrainz_albumid': N_(u'MusicBrainz Release Id'),
    'musicbrainz_artistid': N_(u'MusicBrainz Artist Id'),
    'musicbrainz_discid': N_(u'MusicBrainz Disc Id'),
    'musicbrainz_labelid': N_(u'MusicBrainz Label Id'),
    'musicbrainz_original_albumid': N_(u'MusicBrainz Original Release Id'),
    'musicbrainz_original_artistid': N_(u'MusicBrainz Original Artist Id'),
    'musicbrainz_recordingid': N_(u'MusicBrainz Recording Id'),
    'musicbrainz_releasegroupid': N_(u'MusicBrainz Release Group Id'),
    'musicbrainz_trackid': N_(u'MusicBrainz Track Id'),
    'musicbrainz_workid': N_(u'MusicBrainz Work Id'),
    'musicip_fingerprint': N_(u'MusicIP Fingerprint'),
    'musicip_puid': N_(u'MusicIP PUID'), # Retained because it is used to seed AcoustIDs
    'occasion': N_(u'Occasion'),
    'originalalbum': N_(u'Original Album'),
    'originalartist': N_(u'Original Artist'),
    'originaldate': N_(u'Original Release Date'),
    'originallyricist': N_(u'Original Lyricist'),
    'originalyear': N_(u'Original Year'),
    'performer:': N_(u'Performer'),
    'playdelay': N_(u'Playlist Delay (ms)'),
    'producer': N_(u'Producer'),
    'quality': N_(u'Quality'),
    'recordingcopyright': N_(u'\u2117 Recording Copyright'),
    'recordingdate': N_(u'Recording Date'),
    'recordinglocation': N_(u'Recording Location'),
    'releasecountry': N_(u'Country Code'),
    'releasestatus': N_(u'Release Status'),
    'releasetype': N_(u'Release Type'),
    'remixer': N_(u'Remixer'),
    'script': N_(u'Script'),
    'subtitle': N_(u'Subtitle'),
    'tempo': N_(u'Tempo'),
    'title': N_(u'Title'),
    'titlesort': N_(u'Title Sort Order'),
    'totaldiscs': N_(u'Total Discs'),
    'totaltracks': N_(u'Total Tracks'),
    'tracknumber': N_(u'Track Number'),
    'web_coverart': N_(u'Cover Art URL'),
    'web_lyrics': N_(u'Lyrics Webpage'),
    'web_discogs_artist': N_(u'Discogs Webpage Artist'),
    'web_discogs_label': N_(u'Discogs Webpage Label'),
    'web_discogs_release': N_(u'Discogs Webpage Release'),
    'web_discogs_releasegroup': N_(u'Discogs Webpage Release Group'),
    'web_musicbrainz_artist': N_(u'MusicBrainz Webpage Artist'),
    'web_musicbrainz_label': N_(u'MusicBrainz Webpage Label'),
    'web_musicbrainz_recording': N_(u'MusicBrainz Webpage Recording'),
    'web_musicbrainz_release': N_(u'MusicBrainz Webpage Release'),
    'web_musicbrainz_releasegroup': N_(u'MusicBrainz Webpage Release Group'),
    'web_musicbrainz_work': N_(u'MusicBrainz Webpage Work'),
    'web_official_artist': N_(u'Artist Webpage'),
    'web_official_label': N_(u'Label Webpage'),
    'web_official_release': N_(u'Release Webpage'),
    'web_wikipedia_artist': N_(u'Wikipedia Artist Webpage'),
    'web_wikipedia_label': N_(u'Wikipedia Label Webpage'),
    'web_wikipedia_release': N_(u'Wikipedia Release Webpage'),
    'web_wikipedia_work': N_(u'Wikipedia Work Webpage'),
    'work': N_(u'Work'),
    'writer': N_(u'Writer'),
    'year': N_(u'Release Year'),
    '~absolutetracknumber': N_(u'Album Track Number'),
    '~albumartistcomment': N_(u'Album Artist Disambiguation'),
    '~albumartists_sort': N_(u'Album Artists Sort Order'),
    '~artistcomment': N_(u'Artist Disambiguation'),
    '~artists_sort': N_(u'Artists Sort Order'),
    '~dataquality': N_(u'Musicbrainz Data Quality'),
    '~datatrack': N_(u'Data Track?'),
    '~length': N_(u'Length'),
    '~lyrics_sync': N_(u'Synchronised Lyrics'),
    '~multiartist': N_(u'Multi-Artist Album?'),
    '~musicbrainz_tracknumber': N_(u'MusicBrainz Track Number'),
    '~performance_attributes': N_(u'Performance Attributes'),
    '~pregap': N_(u'Pregap Track?'),
    '~primaryreleasetype': N_(u'Primary Release Type'),
    '~rating': N_(u'Track Rating'),
    '~recordingtitle': N_(u'Recording Title'),
    '~recordingcomment': N_(u'Recording Disambiguation'),
    '~releasecomment': N_(u'Release Disambiguation'),
    '~releasegroup': N_(u'Release Group Title'),
    '~releasegroupcomment': N_(u'Release Group Disambiguation'),
    '~secondaryreleasetype': N_(u'Secondary Release Types'),
    '~stereo': N_(u'Stereo Track?'),
    '~tagtime': N_(u'Date Tagged'),
    '~totalalbumtracks': N_(u'Album Total Tracks'),
    '~video': N_(u'Video?'),
    # File information variables
    '~bitrate': N_(u'Bitrate (kbps)'),
    '~bits_per_sample': N_(u'Bits per sample'),
    '~format': N_(u'File format'),
    '~metadata_format': N_(u'Metadata format'),
    '~channels': N_(u'Audio channels'),
    '~codec': N_(u'Codec'),
    '~sample_rate': N_(u'Sample rate (Hz)'),
    '~dirname': N_(u'File path'),
    '~filename': N_(u'File name'),
    '~extension': N_(u'File extension'),
    '~filetime': N_(u'File last modified'),
}


PRESERVED_TAGS = [
    "~bitrate", "~bits_per_sample", "~format", "~channels", "~sample_rate",
    "~dirname", "~filename", "~extension", "~stereo", "~codec", "~length",
    "~metadata_format", "~filetime", "~tagtime",
]


def display_tag_name(name):
    name, desc = name.split(':', 1) if ':' in name else (name, '')
    name = TAG_NAMES.get(name + ':', TAG_NAMES.get(name, name))
    try:
        name = _(name)
    except:
        name = _(name.decode('ascii', 'ignore'))
    if desc:
        return '%s [%s]' % (name, desc)
    else:
        return name
