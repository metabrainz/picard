# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009, 2018-2021, 2023 Philipp Wolfer
# Copyright (C) 2011 Johannes Weißl
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013-2014, 2019-2021 Laurent Monin
# Copyright (C) 2013-2015, 2017 Sophist-UK
# Copyright (C) 2019 Zenara Daley
# Copyright (C) 2023 Bob Swift
# Copyright (C) 2023 certuna
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


import re


TAG_NAMES = {
    'acoustid_fingerprint': N_('AcoustID Fingerprint'),
    'acoustid_id': N_('AcoustID'),
    'albumartist': N_('Album Artist'),
    'albumartistsort': N_('Album Artist Sort Order'),
    'album': N_('Album'),
    'albumsort': N_('Album Sort Order'),
    'arranger': N_('Arranger'),
    'artist': N_('Artist'),
    'artists': N_('Artists'),
    'artistsort': N_('Artist Sort Order'),
    'asin': N_('ASIN'),
    'barcode': N_('Barcode'),
    'bpm': N_('BPM'),
    'catalognumber': N_('Catalog Number'),
    'comment': N_('Comment'),
    'compilation': N_('Compilation (iTunes)'),
    'composer': N_('Composer'),
    'composersort': N_('Composer Sort Order'),
    'conductor': N_('Conductor'),
    'copyright': N_('Copyright'),
    'date': N_('Date'),
    'director': N_('Director'),
    'discid': N_('Disc Id'),
    'discnumber': N_('Disc Number'),
    'discsubtitle': N_('Disc Subtitle'),
    'djmixer': N_('DJ-Mixer'),
    'encodedby': N_('Encoded By'),
    'encodersettings': N_('Encoder Settings'),
    'engineer': N_('Engineer'),
    'gapless': N_('Gapless Playback'),
    'genre': N_('Genre'),
    'grouping': N_('Grouping'),
    'isrc': N_('ISRC'),
    'key': N_('Key'),
    'label': N_('Record Label'),
    'language': N_('Language'),
    '~length': N_('Length'),
    'license': N_('License'),
    'lyricist': N_('Lyricist'),
    'lyrics': N_('Lyrics'),
    'media': N_('Media'),
    'mixer': N_('Mixer'),
    'mood': N_('Mood'),
    'movement': N_('Movement'),
    'movementnumber': N_('Movement Number'),
    'movementtotal': N_('Movement Count'),
    'musicbrainz_albumartistid': N_('MusicBrainz Release Artist Id'),
    'musicbrainz_albumid': N_('MusicBrainz Release Id'),
    'musicbrainz_artistid': N_('MusicBrainz Artist Id'),
    'musicbrainz_discid': N_('MusicBrainz Disc Id'),
    'musicbrainz_originalalbumid': N_('MusicBrainz Original Release Id'),
    'musicbrainz_originalartistid': N_('MusicBrainz Original Artist Id'),
    'musicbrainz_recordingid': N_('MusicBrainz Recording Id'),
    'musicbrainz_releasegroupid': N_('MusicBrainz Release Group Id'),
    'musicbrainz_trackid': N_('MusicBrainz Track Id'),
    'musicbrainz_workid': N_('MusicBrainz Work Id'),
    'musicip_fingerprint': N_('MusicIP Fingerprint'),
    'musicip_puid': N_('MusicIP PUID'),
    'originalalbum': N_('Original Album'),
    'originalartist': N_('Original Artist'),
    'originaldate': N_('Original Release Date'),
    'originalfilename': N_('Original Filename'),
    'originalyear': N_('Original Year'),
    'performer': N_('Performer'),
    'podcast': N_('Podcast'),
    'podcasturl': N_('Podcast URL'),
    'producer': N_('Producer'),
    'r128_album_gain': N_('R128 Album Gain'),
    'r128_track_gain': N_('R128 Track Gain'),
    '~rating': N_('Rating'),
    'releasecountry': N_('Release Country'),
    'releasedate': N_('Release Date'),
    'releasestatus': N_('Release Status'),
    'releasetype': N_('Release Type'),
    'remixer': N_('Remixer'),
    'replaygain_album_gain': N_('ReplayGain Album Gain'),
    'replaygain_album_peak': N_('ReplayGain Album Peak'),
    'replaygain_album_range': N_('ReplayGain Album Range'),
    'replaygain_reference_loudness': N_('ReplayGain Reference Loudness'),
    'replaygain_track_gain': N_('ReplayGain Track Gain'),
    'replaygain_track_peak': N_('ReplayGain Track Peak'),
    'replaygain_track_range': N_('ReplayGain Track Range'),
    'script': N_('Script'),
    'show': N_('Show Name'),
    'showsort': N_('Show Name Sort Order'),
    'showmovement': N_('Show Work & Movement'),
    'subtitle': N_('Subtitle'),
    'title': N_('Title'),
    'titlesort': N_('Title Sort Order'),
    'totaldiscs': N_('Total Discs'),
    'totaltracks': N_('Total Tracks'),
    'tracknumber': N_('Track Number'),
    'website': N_('Artist Website'),
    'work': N_('Work'),
    'writer': N_('Writer'),
}

PRESERVED_TAGS = (
    '~bitrate',
    '~bits_per_sample',
    '~channels',
    '~dirname',
    '~extension',
    '~filename',
    '~file_created_timestamp',
    '~file_modified_timestamp',
    '~format',
    '~sample_rate',
    '~video',
)

# Tags that got generated in some way from the audio content.
# Those can be set by Picard but the new values usually should be kept
# when moving the file between tags.
CALCULATED_TAGS = {
    'acoustid_fingerprint',
    'acoustid_id',
    'replaygain_album_gain',
    'replaygain_album_peak',
    'replaygain_album_range',
    'replaygain_reference_loudness',
    'replaygain_track_gain',
    'replaygain_track_peak',
    'replaygain_track_range',
    'r128_album_gain',
    'r128_track_gain',
}


def display_tag_name(name):
    if ':' in name:
        name, desc = name.split(':', 1)
        if desc:
            return '%s [%s]' % (_(TAG_NAMES.get(name, name)), desc)
    return _(TAG_NAMES.get(name, name))


RE_COMMENT_LANG = re.compile('^([a-zA-Z]{3}):')
def parse_comment_tag(name):  # noqa: E302
    """
    Parses a tag name like "comment:XXX:desc", where XXX is the language.
    If language is not set ("comment:desc") "eng" is assumed as default.
    Returns a (lang, desc) tuple.
    """
    lang = 'eng'
    desc = ''

    split = name.split(':', 1)
    if len(split) > 1:
        desc = split[1]

    match = RE_COMMENT_LANG.match(desc)
    if match:
        lang = match.group(1)
        desc = desc[4:]
        return lang, desc

    # Special case for unspecified language + empty description
    if desc == 'XXX':
        lang = 'XXX'
        desc = ''

    return lang, desc
