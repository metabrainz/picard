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
# Copyright (C) 2013-2014, 2019-2021, 2023-2025 Laurent Monin
# Copyright (C) 2013-2015, 2017 Sophist-UK
# Copyright (C) 2019 Zenara Daley
# Copyright (C) 2023, 2025 Bob Swift
# Copyright (C) 2023 certuna
# Copyright (C) 2024 Arnab Chakraborty
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Serial
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


from collections import (
    OrderedDict,
    namedtuple,
)
from collections.abc import MutableSequence
import re


try:
    from markdown import markdown
except ImportError:
    markdown = None

from picard.const import PICARD_URLS
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.profile import profile_setting_title


DocumentLink = namedtuple('DocumentLink', ('title', 'link'))

TEXT_NOTES = N_('Notes:')
TEXT_SETTINGS = N_('Option Settings:')
TEXT_LINKS = N_('Links:')
TEXT_NO_DESCRIPTION = N_('No description available.')

ATTRIB2NOTE = OrderedDict(
    is_preserved=N_('preserved read-only'),
    not_script_variable=N_('not for use in scripts'),
    is_calculated=N_('calculated'),
    is_file_info=N_('info from audio file'),
    not_from_mb=N_('not provided from MusicBrainz data'),
    not_populated_by_picard=N_('not populated by stock Picard'),
)


class TagVar:
    def __init__(
        self, name, shortdesc=None, longdesc=None,
        is_preserved=False, is_hidden=False, is_script_variable=True, is_tag=True, is_calculated=False,
        is_file_info=False, is_from_mb=True, is_populated_by_picard=True, see_also=None, related_options=None,
        doc_links=None
    ):
        """
        shortdesc: Short description (typically one or two words) in title case that is suitable
                   for a column header.
        longdesc: Brief description in sentence case describing the tag/variable.  This should
                  be similar (within reasonable length constraints) to the description in the Picard User
                  Guide documentation, and could be used as a tooltip when reviewing a script.  May
                  contain markup.
        is_preserved: the tag is preserved (boolean, default: False)
        is_hidden: the tag is "hidden", name will be prefixed with "~" (boolean, default: False)
        is_script_variable: the tag cannot be used as script variable (boolean, default: True)
        is_tag: the tag is an actual tag (not a calculated or derived one) (boolean, default: True)
        is_calculated: the tag is obtained by external calculation (boolean, default: False)
        is_file_info: the tag is a file information, displayed in file info box (boolean, default: False)
        is_from_mb: the tag information is provided from the MusicBrainz database (boolean, default: True)
        is_populated_by_picard: the tag information is not populated by stock Picard (boolean, default: False)
        see_also: an iterable containing ids of related tags
        related_options: an iterable containing the related option settings (see picard/options.py)
        doc_links: an iterable containing links to external documentation (DocumentLink tuples)
        """
        self._name = name
        self._shortdesc = shortdesc
        self._longdesc = longdesc
        self.is_preserved = is_preserved
        self.is_hidden = is_hidden
        self.is_script_variable = is_script_variable
        self.is_tag = is_tag
        self.is_calculated = is_calculated
        self.is_file_info = is_file_info
        self.is_from_mb = is_from_mb
        self.is_populated_by_picard = is_populated_by_picard
        self.see_also = see_also
        self.related_options = related_options
        self.doc_links = doc_links

    @property
    def shortdesc(self):
        """default to name"""
        if self._shortdesc:
            return self._shortdesc.strip()
        return str(self)

    @property
    def longdesc(self):
        """default to shortdesc"""
        if self._longdesc:
            return self._longdesc.strip()
        return self.shortdesc

    @property
    def not_from_mb(self):
        return not self.is_from_mb

    @property
    def not_script_variable(self):
        return not self.is_script_variable

    @property
    def not_populated_by_picard(self):
        return not self.is_populated_by_picard

    def __str__(self):
        """hidden marked with a prefix"""
        if self.is_hidden:
            return '~' + self._name
        else:
            return self._name

    def script_name(self):
        """In scripts, ~ prefix is replaced with _ for hidden variables"""
        if self.is_hidden:
            return '_' + self._name
        else:
            return self._name

    def notes(self):
        for attrib, note in ATTRIB2NOTE.items():
            if getattr(self, attrib):
                yield note

    def settings(self):
        if not self.related_options:
            return None
        for setting in self.related_options:
            title = profile_setting_title(setting)
            if title:
                yield _(title)

    def links(self):
        if not self.doc_links:
            return None
        for doclink in self.doc_links:
            yield f"<a href='{doclink.link}'>{doclink.title}</a>"


class TagVars(MutableSequence):
    """Mutable sequence for TagVar items
    It maintains an internal dict object for display names.
    Also it doesn't allow to add a TagVar of the same name more than once.
    """
    def __init__(self, *tagvars):
        self._items = []
        self._name2item = dict()
        self.extend(tagvars)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def _get_name(self, tagvar):
        if not isinstance(tagvar, TagVar):
            raise TypeError(f"Value isn't a TagVar instance: {tagvar}")
        name = str(tagvar)
        if name in self._name2item:
            raise ValueError(f"Already an item with same name: {name}")
        return name

    def __setitem__(self, index, tagvar):
        name = self._get_name(tagvar)
        self._name2item[name] = self._items[index] = tagvar

    def __delitem__(self, index):
        name = str(self._items[index])
        del self._items[index]
        del self._name2item[name]

    def insert(self, index, tagvar):
        name = self._get_name(tagvar)
        self._items.insert(index, tagvar)
        self._name2item[name] = self._items[index]

    def __repr__(self):
        return f"TagVars({self._items!r})"

    def item_from_name(self, name):
        if ':' in name:
            name, tagdesc = name.split(':', 1)
        else:
            tagdesc = None

        if name and name.startswith('_'):
            search_name = name.replace('_', '~', 1)
        elif name and name.startswith('~'):
            search_name = name
            name = name.replace('~', '_')
        else:
            search_name = name

        item: TagVar = self._name2item.get(search_name, None)

        return name, tagdesc, search_name, item

    def display_name(self, name):
        name, tagdesc, search_name, item = self.item_from_name(name)

        if item and item.shortdesc:
            title = _(item.shortdesc)
        else:
            title = search_name
        if tagdesc:
            return '%s [%s]' % (title, tagdesc)
        else:
            return title

    @staticmethod
    def _add_section(title, text):
        return f"<p><strong>{title}</strong> {'; '.join(text)}.</p>"

    def display_tooltip(self, name):
        name, tagdesc, _search_name, item = self.item_from_name(name)

        title = _(item.longdesc) if item and item.longdesc else _(TEXT_NO_DESCRIPTION)

        if markdown is None:
            title = '<p>' + title.replace('\n', '<br />') + '</p>'
        else:
            title = markdown(title)

        notes = tuple(item.notes()) if item else tuple()
        if notes:
            title += self._add_section(_(TEXT_NOTES), notes)

        if tagdesc:
            return f"<p><em>%{name}%</em> [{tagdesc}]</p>{title}"
        else:
            return f"<p><em>%{name}%</em></p>{title}"

    def display_full_description(self, name):
        name, tagdesc, _search_name, item = self.item_from_name(name)

        title = _(item.longdesc) if item and item.longdesc else _(TEXT_NO_DESCRIPTION)

        if markdown is None:
            title = '<p>' + title.replace('\n', '<br />') + '</p>'
        else:
            title = markdown(title)

        notes = tuple(item.notes()) if item else tuple()
        if notes:
            title += self._add_section(_(TEXT_NOTES), notes)

        settings = tuple(item.settings()) if item else tuple()
        if settings:
            title += self._add_section(_(TEXT_SETTINGS), settings)

        links = tuple(item.links()) if item else tuple()
        if links:
            title += self._add_section(_(TEXT_LINKS), links)

        if tagdesc:
            return f"<p><em>%{name}%</em> [{tagdesc}]</p>{title}"
        else:
            return f"<p><em>%{name}%</em></p>{title}"

    def names(self, selector=None):
        for item in self._items:
            if selector is None or selector(item):
                yield str(item)


ALL_TAGS = TagVars(
    TagVar(
        'absolutetracknumber',
        shortdesc=N_('FIXME:absolutetracknumber'),
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
    ),
    TagVar(
        'albumartist',
        shortdesc=N_('Album Artist'),
        longdesc=N_(
            'The artists primarily credited on the release, separated by the specified join phrases. '
            'These could be either "standardized" or "as credited" depending on whether the "Use '
            'standardized artist names" metadata option is enabled.'
        ),
    ),
    TagVar(
        'albumartists',
        shortdesc=N_('FIXME:albumartists'),
        longdesc=N_(
            "A multi-value variable containing the names of the album's artists. These could be "
            'either "standardized" or "as credited" depending on whether the "Use standardized '
            'artist names" metadata option is enabled.'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'albumartists_countries',
        shortdesc=N_('FIXME:albumartists_countries'),
        longdesc=N_(
            'A multi-value variable containing the country codes for all of the credited album artists, '
            'in the same order as the artists. Duplicate country codes will be shown if there are more '
            'than one artist from the same country. If a country code is not provided by the webservice '
            'the code "XX" will be used to indicate an unknown country.'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'albumartistsort',
        shortdesc=N_('Album Artist Sort Order'),
        longdesc=N_(
            'The release artists sort names, separated by the specified join phrases. (e.g.: "Beatles, The")'
        ),
    ),
    TagVar(
        'albumartists_sort',
        shortdesc=N_('FIXME:albumartists_sort'),
        longdesc=N_("A multi-value variable containing the sort names of the album's artists."),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'album',
        shortdesc=N_('Album'),
        longdesc=N_('The title of the release.'),
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
    ),
    TagVar(
        'artist',
        shortdesc=N_('Artist'),
        longdesc=N_(
            'The track artist names, separated by the specified join phrases. These could be either '
            '"standardized" or "as credited" depending on whether the "Use standardized artist names" '
            'metadata option is enabled.'
        ),
    ),
    TagVar(
        'artists',
        shortdesc=N_('Artists'),
        longdesc=N_(
            'A multi-value tag containing the track artist names. These could be either "standardized" '
            'or "as credited" depending on whether the "Use standardized artist names" metadata option '
            'is enabled.'
        ),
    ),
    TagVar(
        'artists_countries',
        shortdesc=N_('FIXME:artists_countries'),
        longdesc=N_(
            'A multi-value variable containing the country codes for all of the credited track artists, '
            'in the same order as the artists. Duplicate country codes will be shown if there are more '
            'than one artist from the same country. If a country code is not provided by the webservice '
            'the code "XX" will be used to indicate an unknown country.'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'artistsort',
        shortdesc=N_('Artist Sort Order'),
        longdesc=N_('The track artists sort names, separated by the specified join phrases.'),
    ),
    TagVar(
        'artists_sort',
        shortdesc=N_('FIXME:artists_sort'),
        longdesc=N_("A multi-value variable containing the sort names of the track's artists."),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'asin',
        shortdesc=N_('ASIN'),
        longdesc=N_('The Amazon Standard Identification Number - the number identifying the item on Amazon.'),
    ),
    TagVar(
        'barcode',
        shortdesc=N_('Barcode'),
        longdesc=N_('The barcode assigned to the release.'),
        doc_links=(
            DocumentLink(N_('Barcode in MusicBrainz documentation'), PICARD_URLS['mb_doc'] + 'Barcode'),
            DocumentLink(N_('Barcode mapping in Picard documentation'),  PICARD_URLS['documentation'] + 'appendices/tag_mapping.html#id6'),
        ),
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
            'A multi-value tag contining the numbers assigned to the release by the labels, '
            'which can often be found on the spine or near the barcode. There may be more than '
            'one, especially when multiple labels are involved.'
        ),
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
        see_also=('releasecomment', ),
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
    ),
    TagVar(
        'composersort',
        shortdesc=N_('Composer Sort Order'),
        longdesc=N_('The sort names of the composers for the associated work.'),
    ),
    TagVar(
        'conductor',
        shortdesc=N_('Conductor'),
        longdesc=N_(
            'The names of the conductors associated with the track. These can include the conductor '
            'and chorus master, and could be associated with the release or recording.'
        ),
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
        shortdesc=N_('FIXME:datatrack'),
        longdesc=N_('Set to 1 if the track is a "data track", otherwise empty.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'date',
        shortdesc=N_('Date'),
        longdesc=N_('The date that the release (album) was issued, in the format `YYYY-MM-DD`.'),
    ),
    TagVar(
        'director',
        shortdesc=N_('Director'),
        longdesc=N_(
            'The director of a track as provided by the "*Video Director*" or "*Audio Director*" relationship '
            'in MusicBrainz.'
        ),
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
        # TODO: Check if this actually exists or if it should be %_musicbrainz_discid%
        'discid',
        shortdesc=N_('Disc Id'),
        longdesc=N_(''),
        see_also=('musicbrainz_discid', ),
    ),
    TagVar(
        'discnumber',
        shortdesc=N_('Disc Number'),
        longdesc=N_('The number of the disc in the release that contains this track.'),
    ),
    TagVar(
        'discpregap',
        shortdesc=N_('FIXME:discpregap'),
        longdesc=N_('Set to 1 if the disc the track is on has a "pregap track", otherwise empty.'),
        is_hidden=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'discsubtitle',
        shortdesc=N_('Disc Subtitle'),
        longdesc=N_('The media title given to a specific disc in the release.'),
    ),
    TagVar(
        'djmixer',
        shortdesc=N_('DJ-Mixer'),
        longdesc=N_('The names of the DJ mixers for the track.'),
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
    ),
    TagVar(
        'extension',
        shortdesc=N_('File extension'),
        longdesc=N_("The file's extension."),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'file_created_timestamp',
        shortdesc=N_('File created timestamp'),
        longdesc=N_('The file creation timestamp in the form `YYYY-MM-DD HH:MM:SS` as reported by the file system.'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'file_modified_timestamp',
        shortdesc=N_('File modified timestamp'),
        longdesc=N_('The file modification timestamp in the form `YYYY-MM-DD HH:MM:SS` as reported by the file system.'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'filename',
        shortdesc=N_('File name'),
        longdesc=N_('The name of the file without extension.'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'filepath',
        shortdesc=N_('File Path'),
        longdesc=N_('Full path and name of the file.'),
        is_hidden=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'filesize',
        shortdesc=N_('File size'),
        longdesc=N_('Size of the file in bytes.'),
        is_file_info=True,
        is_hidden=True,
        is_tag=False,
        is_from_mb=False,
    ),
    TagVar(
        'format',
        shortdesc=N_('File format'),
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
        longdesc=N_(
            'A multi-value tag containing the specified genre information from MusicBrainz.'
        ),
        related_options=('use_genres', ),
    ),
    TagVar(
        # TODO: Check if this actually exists or if it was provided by the last.fm plugin.
        'grouping',
        shortdesc=N_('Grouping'),
        longdesc=N_(''),
        is_from_mb=False,
    ),
    TagVar(
        'isrc',
        shortdesc=N_('ISRC'),
        longdesc=N_(
            'The International Standard Recording Code - an international standard code for uniquely '
            'identifying sound recordings and music video recordings.'
        ),
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
        longdesc=N_('A multi-value tag containing the names of the labels associated with the release.'),
    ),
    TagVar(
        'language',
        shortdesc=N_('Language'),
        longdesc=N_('Work lyric language as per ISO 639-3 if a related work exists.'),
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
        longdesc=N_('The licenses associated with the track, either through the release or recording relationships.'),
    ),
    TagVar(
        'lyricist',
        shortdesc=N_('Lyricist'),
        longdesc=N_('The names of the lyricists for the associated work.'),
    ),
    TagVar(
        'lyricistsort',
        shortdesc=N_('Lyricist Sort'),
        longdesc=N_('The sort names of the lyricists for the associated work.'),
        is_hidden=True,
    ),
    TagVar(
        'lyrics',
        shortdesc=N_('Lyrics'),
        longdesc=N_('The lyrics for the track.'),
        is_from_mb=False,
    ),
    TagVar(
        'media',
        shortdesc=N_('Media'),
        longdesc=N_('The media on which the release was distributed (e.g.: CD).'),
    ),
    TagVar(
        'mixer',
        shortdesc=N_('Mixer'),
        longdesc=N_('The names of the "*Mixed By*" engineers associated with the track.'),
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
        shortdesc=N_('FIXME:multiartist'),
        longdesc=N_(
            'Set to 1 if not all of the tracks on the album have the same primary artist, otherwise empty.'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'musicbrainz_albumartistid',
        shortdesc=N_('MusicBrainz Release Artist Id'),
        longdesc=N_('A multi-value tag containing the MusicBrainz Identifiers (MBIDs) for the release artists.'),
    ),
    TagVar(
        'musicbrainz_albumid',
        shortdesc=N_('MusicBrainz Release Id'),
        longdesc=N_('The MusicBrainz Identifier (MBID) for the release.'),
    ),
    TagVar(
        'musicbrainz_artistid',
        shortdesc=N_('MusicBrainz Artist Id'),
        longdesc=N_('A multi-value tag containing the MusicBrainz Identifiers (MBIDs) for the track artists.'),
    ),
    TagVar(
        'musicbrainz_discid',
        shortdesc=N_('MusicBrainz Disc Id'),
        longdesc=N_(
            'The Disc ID is the code number which MusicBrainz uses to link a physical CD to a release listing. '
            'This is based on the table of contents (TOC) information read from the disc. This tag contains the '
            'Disc ID if the album information was retrieved using `Tools > Lookup CD` from the menu.'
        ),
    ),
    TagVar(
        'musicbrainz_discids',
        shortdesc=N_('FIXME:musicbrainz_discids'),
        longdesc=N_(
            'A multi-value variable containing a list of all of the disc ids attached to the selected release. '
            'The list provided for each medium only includes the disc ids attached to that medium. For example, '
            'the list provided for Disc 1 of a three CD set will not include the disc ids attached to discs 2 '
            'and 3 of the set.'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'musicbrainz_originalalbumid',
        shortdesc=N_('MusicBrainz Original Release Id'),
        longdesc=N_(
            'The MusicBrainz Identifier (MBID) for the original release. This is only available if the release '
            'has been merged with another release.'
        ),
    ),
    TagVar(
        'musicbrainz_originalartistid',
        shortdesc=N_('MusicBrainz Original Artist Id'),
        longdesc=N_(
            'A multi-value tag containing the MusicBrainz Identifiers (MBIDs) for the track artists of the original '
            'recording. This is only available if the recording has been merged with another recording.'
        ),
    ),
    TagVar(
        'musicbrainz_recordingid',
        shortdesc=N_('MusicBrainz Recording Id'),
        longdesc=N_('The MusicBrainz Identifier (MBID) for the recording.'),
    ),
    TagVar(
        'musicbrainz_releasegroupid',
        shortdesc=N_('MusicBrainz Release Group Id'),
        longdesc=N_('The MusicBrainz Identifier (MBID) for the release group.'),
    ),
    TagVar(
        'musicbrainz_trackid',
        shortdesc=N_('MusicBrainz Track Id'),
        longdesc=N_('The MusicBrainz Identifier (MBID) for the track.'),
    ),
    TagVar(
        'musicbrainz_tracknumber',
        shortdesc=N_('FIXME:musicbrainz_tracknumber'),
        longdesc=N_(
            'The track number written as on the MusicBrainz release, such as vinyl numbering (A1, A2, etc.)'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'musicbrainz_workid',
        shortdesc=N_('MusicBrainz Work Id'),
        longdesc=N_('The MusicBrainz Identifier (MBID) for the Work if a related work exists.'),
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
        shortdesc=N_('FIXME:performance_attributes'),
        longdesc=N_(
            'List of performance attributes for the work (e.g.: "*live*", "*cover*", "*medley*"). Use `$inmulti()` '
            'to check for a specific type (e.g.: `$if($inmulti(%_performance_attributes%,medley), (Medley),)`).'
        ),
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
        longdesc=N_('The associated url if the recording is a podcast.'),
        is_from_mb=False,
    ),
    TagVar(
        'pregap',
        shortdesc=N_('FIXME:pregap'),
        longdesc=N_('Set to 1 if the track is a "pregap track", otherwise empty.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'primaryreleasetype',
        shortdesc=N_('FIXME:primaryreleasetype'),
        longdesc=N_(
            'The primary type of the release group (i.e.: *album*, *single*, *ep*, *broadcast*, or *other*).'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'producer',
        shortdesc=N_('Producer'),
        longdesc=N_('The names of the producers for the associated release or recording.'),
    ),
    TagVar(
        'r128_album_gain',
        shortdesc=N_('R128 Album Gain'),
        longdesc=N_(''),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'r128_track_gain',
        shortdesc=N_('R128 Track Gain'),
        longdesc=N_(''),
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
        shortdesc=N_('FIXME:recording_firstreleasedate'),
        longdesc=N_('The date of the earliest recording for a track in the format `YYYY-MM-DD`.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'recording_series',
        shortdesc=N_('FIXME:recording_series'),
        longdesc=N_('A multi-value variable containing the series titles associated with the recording.'),
        is_hidden=True,
    ),
    TagVar(
        'recording_seriescomment',
        shortdesc=N_('FIXME:recording_seriescomment'),
        longdesc=N_('A multi-value variable containing the series disambiguation comments associated with the recording.'),
        is_hidden=True,
    ),
    TagVar(
        'recording_seriesid',
        shortdesc=N_('FIXME:recording_seriesid'),
        longdesc=N_('A multi-value variable containing the series MusicBrainz Identifiers (MBIDs) associated with the recording.'),
        is_hidden=True,
    ),
    TagVar(
        'recording_seriesnumber',
        shortdesc=N_('FIXME:recording_seriesnumber'),
        longdesc=N_('A multi-value variable containing the series numbers associated with the recording.'),
        is_hidden=True,
    ),
    TagVar(
        'recordingcomment',
        shortdesc=N_('FIXME:recordingcomment'),
        longdesc=N_('The disambiguation comment for the recording associated with a track.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'recordingtitle',
        shortdesc=N_('FIXME:recordingtitle'),
        longdesc=N_('Recording title - normally the same as the track title, but can be different.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releaseannotation',
        shortdesc=N_('FIXME:releaseannotation'),
        longdesc=N_('The annotation comment for the release.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasecomment',
        shortdesc=N_('FIXME:releasecomment'),
        longdesc=N_('The disambiguation comment for the release.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasecountries',
        shortdesc=N_('FIXME:releasecountries'),
        longdesc=N_('A multi-value variable containing the complete list of release countries for the release.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasecountry',
        shortdesc=N_('Release Country'),
        longdesc=N_(
            'The two-character code for the country in which the release was issued. If more than one release country '
            'was specified, this tag will contain the first one in the list.'
        ),
    ),
    TagVar(
        'releasedate',
        shortdesc=N_('Release Date'),
        longdesc=N_(
            'The date that the release (album) was issued, in the format `YYYY-MM-DD`.'
            'This tag exists for specific use in scripts and plugins, but is not filled by default. In most cases it is '
            'recommended to use the `%date%` tag instead for compatibility with existing software.'
        ),
        is_from_mb=False,
        see_also=('date', ),
    ),
    TagVar(
        'releasegroup',
        shortdesc=N_('FIXME:releasegroup'),
        longdesc=N_(
            'The title of the release group. This is typically the same as the album title, but can be different.'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasegroup_firstreleasedate',
        shortdesc=N_('FIXME:releasegroup_firstreleasedate'),
        longdesc=N_(
            'The date of the earliest release in the release group in the format `YYYY-MM-DD`. This is intended to '
            'provide, for example, the release date of the vinyl version of what you have on CD.'
        ),
        is_hidden=True,
        is_tag=False,
        see_also=('originaldate', )
    ),
    TagVar(
        'releasegroup_series',
        shortdesc=N_('RG Series'),
        longdesc=N_('A multi-value variable containing the series titles associated with the release group.'),
        is_hidden=True,
    ),
    TagVar(
        'releasegroup_seriescomment',
        shortdesc=N_('RG Series Comment'),
        longdesc=N_('A multi-value variable containing the series disambiguation comments associated with the release group.'),
        is_hidden=True,
    ),
    TagVar(
        'releasegroup_seriesid',
        shortdesc=N_('RG Series Id'),
        longdesc=N_('A multi-value variable containing the series MusicBrainz Identifiers (MBIDs) associated with the release group.'),
        is_hidden=True,
    ),
    TagVar(
        'releasegroup_seriesnumber',
        shortdesc=N_('RG Series Number'),
        longdesc=N_('A multi-value variable containing the series numbers associated with the release group.'),
        is_hidden=True,
    ),
    TagVar(
        'releasegroupcomment',
        shortdesc=N_('FIXME:releasegroupcomment'),
        longdesc=N_('The disambiguation comment for the release group.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releaselanguage',
        shortdesc=N_('FIXME:releaselanguage'),
        longdesc=N_('The language of the release as per ISO 639-3.'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'release_series',
        shortdesc=N_('Release Series'),
        longdesc=N_('A multi-value variable containing the series titles associated with the release.'),
        is_hidden=True,
    ),
    TagVar(
        'release_seriescomment',
        shortdesc=N_('Release Series Comment'),
        longdesc=N_('A multi-value variable containing the series disambiguation comments associated with the release.'),
        is_hidden=True,
    ),
    TagVar(
        'release_seriesid',
        shortdesc=N_('Release Series Id'),
        longdesc=N_('A multi-value variable containing the series MusicBrainz Identifiers (MBIDs) associated with the release.'),
        is_hidden=True,
    ),
    TagVar(
        'release_seriesnumber',
        shortdesc=N_('Release Series Number'),
        longdesc=N_('A multi-value variable containing the series numbers associated with the release.'),
        is_hidden=True,
    ),
    TagVar(
        'releasestatus',
        shortdesc=N_('Release Status'),
        longdesc=N_(
            'An indicator of the "official" status of the release. Possible values include "*official*", '
            '"*promotional*", "*bootleg*", and "*pseudo-release*".'
        ),
    ),
    TagVar(
        'releasetype',
        shortdesc=N_('Release Type'),
        longdesc=N_(
            'A multi-value tag containing the types of release assigned to the release group.'
        ),
        see_also=('primaryreleasetype', 'secondaryreleasetype'),
    ),
    TagVar(
        'remixer',
        shortdesc=N_('Remixer'),
        longdesc=N_('The names of the remixer engineers associated with the track.'),
    ),
    TagVar(
        'replaygain_album_gain',
        shortdesc=N_('ReplayGain Album Gain'),
        longdesc=N_(''),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_album_peak',
        shortdesc=N_('ReplayGain Album Peak'),
        longdesc=N_(''),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_album_range',
        shortdesc=N_('ReplayGain Album Range'),
        longdesc=N_(''),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_reference_loudness',
        shortdesc=N_('ReplayGain Reference Loudness'),
        longdesc=N_(''),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_track_gain',
        shortdesc=N_('ReplayGain Track Gain'),
        longdesc=N_(''),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_track_peak',
        shortdesc=N_('ReplayGain Track Peak'),
        longdesc=N_(''),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'replaygain_track_range',
        shortdesc=N_('ReplayGain Track Range'),
        longdesc=N_(''),
        is_calculated=True,
        is_from_mb=False,
    ),
    TagVar(
        'sample_rate',
        shortdesc=N_('File sample rate'),
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
    ),
    TagVar(
        'secondaryreleasetype',
        shortdesc=N_('FIXME:secondaryreleasetype'),
        longdesc=N_(
            'Zero or more secondary types (i.e.: *audiobook*, *compilation*, *dj-mix*, *interview*, '
            '*live*, *mixtape/street*, *remix*, *soundtrack*, or *spokenword*) for the release group.'
        ),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'silence',
        shortdesc=N_('FIXME:silence'),
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
            'will display the work, movement number and movement name instead of the track title. For example, the track '
            'will be displayed as "Symphony no. 5 in C minor, op. 67: II. Andante con moto" regardless of the value of the '
            'title tag.'
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
    ),
    TagVar(
        'titlesort',
        shortdesc=N_('Title Sort Order'),
        longdesc=N_('The sort name of the track title.'),
        is_from_mb=False,
    ),
    TagVar(
        'totalalbumtracks',
        shortdesc=N_('FIXME:totalalbumtracks'),
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
        shortdesc=N_('File video flag'),
        longdesc=N_('Set to "1" if the track is a video.'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'website',
        shortdesc=N_('Artist Website'),
        longdesc=N_('The official website for the artist.'),
    ),
    TagVar(
        'work',
        shortdesc=N_('Work'),
        longdesc=N_(
            'The name of the work associated with the track (e.g.: "Symphony no. 5 in C minor, op. 67").\n\nNote: If you '
            'are using iTunes together with MP3 files you should activate the "Save iTunes compatible grouping and work" '
            'option in order for the work to be displayed correctly.'
        ),
    ),
    TagVar(
        'work_series',
        shortdesc=N_('Work Series'),
        longdesc=N_('A multi-value variable containing the series titles associated with the work.'),
        is_hidden=True,
    ),
    TagVar(
        'work_seriescomment',
        shortdesc=N_('Work Series Comment'),
        longdesc=N_('A multi-value variable containing the series disambiguation comments associated with the work.'),
        is_hidden=True,
    ),
    TagVar(
        'work_seriesid',
        shortdesc=N_('Work Series Id'),
        longdesc=N_('A multi-value variable containing the series MusicBrainz Identifiers (MBIDs) associated with the work.'),
        is_hidden=True,
    ),
    TagVar(
        'work_seriesnumber',
        shortdesc=N_('Work Series Number'),
        longdesc=N_('A multi-value variable containing the series numbers associated with the work.'),
        is_hidden=True,
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
            'A multi-value tag containing the names of the writers associated with the related work. This is '
            'not written to most file formats automatically. You can merge this with composers with a script '
            'like:\n\n`$copymerge(composer, writer)`'
        ),
    ),
    TagVar(
        'writersort',
        shortdesc=N_('Writer Sort'),
        longdesc=N_('The sort names of the writers for the work.'),
        is_hidden=True,
    ),
)


def tag_names():
    yield from ALL_TAGS.names(selector=lambda tv: tv.is_tag)


def preserved_tag_names():
    """Tags that should be preserved by default"""
    yield from ALL_TAGS.names(selector=lambda tv: tv.is_preserved)


def calculated_tag_names():
    """
    Tags that got generated in some way from the audio content.
    Those can be set by Picard but the new values usually should be kept
    when moving the file between tags.
    """
    yield from ALL_TAGS.names(selector=lambda tv: tv.is_calculated)


def file_info_tag_names():
    """Tags that contains infos related to files"""
    yield from ALL_TAGS.names(selector=lambda tv: tv.is_file_info)


def script_variable_tag_names():
    """Tag names available to scripts (used by script editor completer)"""
    yield from (
        tagvar.script_name()
        for tagvar in ALL_TAGS
        if not tagvar.not_script_variable
    )


def display_tag_name(name):
    return ALL_TAGS.display_name(name)


def display_tag_tooltip(name):
    return ALL_TAGS.display_tooltip(name)


def display_tag_full_description(name):
    return ALL_TAGS.display_full_description(name)


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

    match_ = RE_COMMENT_LANG.match(desc)
    if match_:
        lang = match_.group(1)
        desc = desc[4:]
        return lang, desc

    # Special case for unspecified language + empty description
    if desc == 'XXX':
        lang = 'XXX'
        desc = ''

    return lang, desc


def parse_subtag(name):
    """
    Parses a tag name like "lyrics:XXX:desc", where XXX is the language.
    If language is not set, the colons are still mandatory, and "eng" is
    assumed by default.
    """
    split = name.split(':')
    if len(split) > 1 and split[1]:
        lang = split[1]
    else:
        lang = 'eng'

    if len(split) > 2:
        desc = split[2]
    else:
        desc = ''

    return lang, desc
