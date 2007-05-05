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

tag_names = {
    'album': N_('Album'),
    'artist': N_('Artist'),
    'title': N_('Title'),
    'date': N_('Date'),
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
    'composer': N_('Composer'),
    'conductor': N_('Conductor'),
    'lyricist': N_('Lyricist'),
    'arranger': N_('Arranger'),
    'producer': N_('Producer'),
    'engineer': N_('Engineer'),
    'subtitle': N_('Subtitle'),
    'discsubtitle': N_('Disc Subtitle'),
    'remixer': N_('Remixer'),
    'musicbrainz_trackid': N_('MusicBrainz Track Id'),
    'musicbrainz_albumid': N_('MusicBrainz Release Id'),
    'musicbrainz_artistid': N_('MusicBrainz Artist Id'),
    'musicbrainz_albumartistid': N_('MusicBrainz Release Artist Id'),
    'musicbrainz_trmid': N_('MusicBrainz TRM Id'),
    'musicip_puid': N_('MusicIP PUID'),
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
    'djmixer': N_('DJ-Mixer'),
    'media': N_('Media'),
    'lyrics': N_('Lyrics'),
    'mixer': N_('Mixer'),
}

def display_tag_name(name):
    if ':' in name:
        name, desc = name.split(':', 1)
        name = _(tag_names.get(name + ':', name))
        return '%s [%s]' % (_(name), desc)
    else:
        return _(tag_names.get(name, name))
