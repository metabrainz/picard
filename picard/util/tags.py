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
    'album': N_('Album'),
    'artist': N_('Artist'),
    'title': N_('Title'),
    'date': N_('Date'),
    'originaldate': N_('Original Release Date'),
    'albumartist': N_('Album Artist'),
    'tracknumber': N_('Track Number'),
    'totaltracks': N_('Total Tracks'),
    'discnumber': N_('Disc Number'),
    'totaldiscs': N_('Total Discs'),
    'albumartistsort': N_('Album Artist Sort Order'),
    'artistsort': N_('Artist Sort Order'),
    'titlesort': N_('Title Sort Order'),
    'albumsort': N_('Album Sort Order'),
    'asin': N_('ASIN'),
    'grouping': N_('Grouping'),
    'version': N_('Version'),
    'isrc': N_('ISRC'),
    'mood': N_('Mood'),
    'bpm': N_('BPM'),
    'copyright': N_('Copyright'),
    'license': N_('License'),
    'composer': N_('Composer'),
    'writer': N_('Writer'),
    'conductor': N_('Conductor'),
    'lyricist': N_('Lyricist'),
    'arranger': N_('Arranger'),
    'producer': N_('Producer'),
    'engineer': N_('Engineer'),
    'subtitle': N_('Subtitle'),
    'discsubtitle': N_('Disc Subtitle'),
    'remixer': N_('Remixer'),
    'musicbrainz_trackid': N_('MusicBrainz Recording Id'),
    'musicbrainz_albumid': N_('MusicBrainz Release Id'),
    'musicbrainz_artistid': N_('MusicBrainz Artist Id'),
    'musicbrainz_albumartistid': N_('MusicBrainz Release Artist Id'),
    'musicbrainz_workid': N_('MusicBrainz Work Id'),
    'musicbrainz_releasegroupid': N_('MusicBrainz Release Group Id'),
    'musicbrainz_discid': N_('MusicBrainz Disc Id'),
    'musicbrainz_sortname': N_('MusicBrainz Sort Name'),
    'musicip_puid': N_('MusicIP PUID'),
    'musicip_fingerprint': N_('MusicIP Fingerprint'),
    'acoustid_id': N_('AcoustID'),
    'acoustid_fingerprint': N_('AcoustID Fingerprint'),
    'discid': N_('Disc Id'),
    'website': N_('Website'),
    'compilation': N_('Compilation'),
    'comment:': N_('Comment'),
    'genre': N_('Genre'),
    'encodedby': N_('Encoded By'),
    'performer:': N_('Performer'),
    'releasetype': N_('Release Type'),
    'releasestatus': N_('Release Status'),
    'releasecountry': N_('Release Country'),
    'label': N_('Record Label'),
    'barcode': N_('Barcode'),
    'catalognumber': N_('Catalog Number'),
    'format': N_('Format'),
    'djmixer': N_('DJ-Mixer'),
    'media': N_('Media'),
    'lyrics:': N_('Lyrics'),
    'mixer': N_('Mixer'),
    'language': N_('Language'),
    'script': N_('Script'),
    '~length': N_('Length'),
    '~rating': N_('Rating'),
}

def display_tag_name(name):
    if ':' in name:
        name, desc = name.split(':', 1)
        name = _(TAG_NAMES.get(name + ':', name))
        return '%s [%s]' % (_(name), desc)
    else:
        new_name = TAG_NAMES.get(name)
        if new_name is None:
            new_name = TAG_NAMES.get(name + ':')
            if new_name is None:
                return _(name)
            else:
                return '%s []' % (_(new_name),)
        else:
            return _(new_name)

