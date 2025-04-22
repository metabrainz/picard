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
# Copyright (C) 2013-2014, 2019-2021, 2023-2024 Laurent Monin
# Copyright (C) 2013-2015, 2017 Sophist-UK
# Copyright (C) 2019 Zenara Daley
# Copyright (C) 2023 Bob Swift
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


from collections.abc import MutableSequence
import re

from picard.i18n import (
    N_,
    gettext as _,
)


class TagVar:
    def __init__(
        self, name, shortdesc=None, longdesc=None,
        is_preserved=False, is_hidden=False, is_script_variable=True,
        is_tag=True, is_calculated=False, is_file_info=False
    ):
        """
        shortdesc: Short description (typically one or two words) in title case that is suitable
                   for a column header.
        longdesc: Brief description in sentence case describing the tag/variable.  This should
                  be similar (within reasonable length constraints) to the description in the Picard User
                  Guide documentation, and could be used as a tooltip when reviewing a script.
        is_preserved: the tag is preserved (boolean, default: False)
        is_hidden: the tag is "hidden", name will be prefixed with "~" (boolean, default: False)
        is_script_variable: the tag can be used as script variable (boolean, default: True)
        is_tag: the tag is an actual tag (not a calculated or derived one) (boolean, default: True)
        is_calculated: the tag is obtained by external calculation (boolean, default: False)
        is_file_info: the tag is a file information, displayed in file info box (boolean, default: False)
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

    @property
    def shortdesc(self):
        """default to name"""
        if self._shortdesc:
            return self._shortdesc
        return str(self)

    @property
    def longdesc(self):
        """default to shortdesc"""
        if self._longdesc:
            return self._longdesc
        return self.shortdesc

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

    def display_name(self, name):
        tagdesc = None
        if ':' in name:
            name, tagdesc = name.split(':', 1)

        item = self._name2item.get(name, None)
        if item and item.shortdesc:
            title = _(item.shortdesc)
        else:
            title = name

        if tagdesc:
            return '%s [%s]' % (title, tagdesc)
        else:
            return title

    def names(self, selector=None):
        for item in self._items:
            if selector is None or selector(item):
                yield str(item)


ALL_TAGS = TagVars(
    TagVar(
        'absolutetracknumber',
        shortdesc=N_('FIXME:absolutetracknumber'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'acoustid_fingerprint',
        shortdesc=N_('AcoustID Fingerprint'),
        is_calculated=True,
    ),
    TagVar(
        'acoustid_id',
        shortdesc=N_('AcoustID'),
        is_calculated=True,
    ),
    TagVar(
        'albumartist',
        shortdesc=N_('Album Artist'),
    ),
    TagVar(
        'albumartists',
        shortdesc=N_('FIXME:albumartists'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'albumartists_countries',
        shortdesc=N_('FIXME:albumartists_countries'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'albumartistsort',
        shortdesc=N_('Album Artist Sort Order'),
    ),
    TagVar(
        'albumartists_sort',
        shortdesc=N_('FIXME:albumartists_sort'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'album',
        shortdesc=N_('Album'),
    ),
    TagVar(
        'albumsort',
        shortdesc=N_('Album Sort Order'),
    ),
    TagVar(
        'arranger',
        shortdesc=N_('Arranger'),
    ),
    TagVar(
        'artist',
        shortdesc=N_('Artist'),
    ),
    TagVar(
        'artists',
        shortdesc=N_('Artists'),
    ),
    TagVar(
        'artists_countries',
        shortdesc=N_('FIXME:artists_countries'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'artistsort',
        shortdesc=N_('Artist Sort Order'),
    ),
    TagVar(
        'artists_sort',
        shortdesc=N_('FIXME:artists_sort'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'asin',
        shortdesc=N_('ASIN'),
    ),
    TagVar(
        'barcode',
        shortdesc=N_('Barcode'),
    ),
    TagVar(
        'bpm',
        shortdesc=N_('BPM'),
    ),
    TagVar(
        'bitrate',
        shortdesc=N_('Bitrate'),
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'bits_per_sample',
        shortdesc=N_('Bits per sample'),
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'catalognumber',
        shortdesc=N_('Catalog Number'),
    ),
    TagVar(
        'channels',
        shortdesc=N_('Channels'),
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),

    TagVar(
        'comment',
        shortdesc=N_('Comment'),
    ),
    TagVar(
        'compilation',
        shortdesc=N_('Compilation (iTunes)'),
    ),
    TagVar(
        'composer',
        shortdesc=N_('Composer'),
    ),
    TagVar(
        'composersort',
        shortdesc=N_('Composer Sort Order'),
    ),
    TagVar(
        'conductor',
        shortdesc=N_('Conductor'),
    ),
    TagVar(
        'copyright',
        shortdesc=N_('Copyright'),
    ),
    TagVar(
        'datatrack',
        shortdesc=N_('FIXME:datatrack'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'date',
        shortdesc=N_('Date'),
    ),
    TagVar(
        'director',
        shortdesc=N_('Director'),
    ),
    TagVar(
        'dirname',
        shortdesc=N_('Directory name'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'discid',
        shortdesc=N_('Disc Id'),
    ),
    TagVar(
        'discnumber',
        shortdesc=N_('Disc Number'),
    ),
    TagVar(
        'discpregap',
        shortdesc=N_('FIXME:discpregap'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'discsubtitle',
        shortdesc=N_('Disc Subtitle'),
    ),
    TagVar(
        'djmixer',
        shortdesc=N_('DJ-Mixer'),
    ),
    TagVar(
        'encodedby',
        shortdesc=N_('Encoded By'),
    ),
    TagVar(
        'encodersettings',
        shortdesc=N_('Encoder Settings'),
    ),
    TagVar(
        'engineer',
        shortdesc=N_('Engineer'),
    ),
    TagVar(
        'extension',
        shortdesc=N_('File extension'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'file_created_timestamp',
        shortdesc=N_('File created timestamp'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'file_modified_timestamp',
        shortdesc=N_('File modified timestamp'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'filename',
        shortdesc=N_('File name'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'filepath',
        shortdesc=N_('File Path'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'filesize',
        shortdesc=N_('File size'),
        is_file_info=True,
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'format',
        shortdesc=N_('File format'),
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'gapless',
        shortdesc=N_('Gapless Playback'),
    ),
    TagVar(
        'genre',
        shortdesc=N_('Genre'),
    ),
    TagVar(
        'grouping',
        shortdesc=N_('Grouping'),
    ),
    TagVar(
        'isrc',
        shortdesc=N_('ISRC'),
    ),
    TagVar(
        'key',
        shortdesc=N_('Key'),
    ),
    TagVar(
        'label',
        shortdesc=N_('Record Label'),
    ),
    TagVar(
        'language',
        shortdesc=N_('Language'),
    ),
    TagVar(
        'length',
        shortdesc=N_('Length'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'license',
        shortdesc=N_('License'),
    ),
    TagVar(
        'lyricist',
        shortdesc=N_('Lyricist'),
    ),
    TagVar(
        'lyrics',
        shortdesc=N_('Lyrics'),
    ),
    TagVar(
        'media',
        shortdesc=N_('Media'),
    ),
    TagVar(
        'mixer',
        shortdesc=N_('Mixer'),
    ),
    TagVar(
        'mood',
        shortdesc=N_('Mood'),
    ),
    TagVar(
        'movement',
        shortdesc=N_('Movement'),
    ),
    TagVar(
        'movementnumber',
        shortdesc=N_('Movement Number'),
    ),
    TagVar(
        'movementtotal',
        shortdesc=N_('Movement Count'),
    ),
    TagVar(
        'multiartist',
        shortdesc=N_('FIXME:multiartist'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'musicbrainz_albumartistid',
        shortdesc=N_('MusicBrainz Release Artist Id'),
    ),
    TagVar(
        'musicbrainz_albumid',
        shortdesc=N_('MusicBrainz Release Id'),
    ),
    TagVar(
        'musicbrainz_artistid',
        shortdesc=N_('MusicBrainz Artist Id'),
    ),
    TagVar(
        'musicbrainz_discid',
        shortdesc=N_('MusicBrainz Disc Id'),
    ),
    TagVar(
        'musicbrainz_discids',
        shortdesc=N_('FIXME:musicbrainz_discids'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'musicbrainz_originalalbumid',
        shortdesc=N_('MusicBrainz Original Release Id'),
    ),
    TagVar(
        'musicbrainz_originalartistid',
        shortdesc=N_('MusicBrainz Original Artist Id'),
    ),
    TagVar(
        'musicbrainz_recordingid',
        shortdesc=N_('MusicBrainz Recording Id'),
    ),
    TagVar(
        'musicbrainz_releasegroupid',
        shortdesc=N_('MusicBrainz Release Group Id'),
    ),
    TagVar(
        'musicbrainz_trackid',
        shortdesc=N_('MusicBrainz Track Id'),
    ),
    TagVar(
        'musicbrainz_tracknumber',
        shortdesc=N_('FIXME:musicbrainz_tracknumber'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'musicbrainz_workid',
        shortdesc=N_('MusicBrainz Work Id'),
    ),
    TagVar(
        'musicip_fingerprint',
        shortdesc=N_('MusicIP Fingerprint'),
    ),
    TagVar(
        'musicip_puid',
        shortdesc=N_('MusicIP PUID'),
    ),
    TagVar(
        'originalalbum',
        shortdesc=N_('Original Album'),
    ),
    TagVar(
        'originalartist',
        shortdesc=N_('Original Artist'),
    ),
    TagVar(
        'originaldate',
        shortdesc=N_('Original Release Date'),
    ),
    TagVar(
        'originalfilename',
        shortdesc=N_('Original Filename'),
    ),
    TagVar(
        'originalyear',
        shortdesc=N_('Original Year'),
    ),
    TagVar(
        'performance_attributes',
        shortdesc=N_('FIXME:performance_attributes'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'performer',
        shortdesc=N_('Performer'),
    ),
    TagVar(
        'podcast',
        shortdesc=N_('Podcast'),
    ),
    TagVar(
        'podcasturl',
        shortdesc=N_('Podcast URL'),
    ),
    TagVar(
        'pregap',
        shortdesc=N_('FIXME:pregap'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'primaryreleasetype',
        shortdesc=N_('FIXME:primaryreleasetype'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'producer',
        shortdesc=N_('Producer'),
    ),
    TagVar(
        'r128_album_gain',
        shortdesc=N_('R128 Album Gain'),
        is_calculated=True,
    ),
    TagVar(
        'r128_track_gain',
        shortdesc=N_('R128 Track Gain'),
        is_calculated=True,
    ),
    TagVar(
        'rating',
        shortdesc=N_('Rating'),
        is_hidden=True,
    ),
    TagVar(
        'recording_firstreleasedate',
        shortdesc=N_('FIXME:recording_firstreleasedate'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'recordingcomment',
        shortdesc=N_('FIXME:recordingcomment'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'recordingtitle',
        shortdesc=N_('FIXME:recordingtitle'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasecomment',
        shortdesc=N_('FIXME:releasecomment'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasecountries',
        shortdesc=N_('FIXME:releasecountries'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasegroup',
        shortdesc=N_('FIXME:releasegroup'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasegroup_firstreleasedate',
        shortdesc=N_('FIXME:releasegroup_firstreleasedate'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasegroupcomment',
        shortdesc=N_('FIXME:releasegroupcomment'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releaselanguage',
        shortdesc=N_('FIXME:releaselanguage'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'releasecountry',
        shortdesc=N_('Release Country'),
    ),
    TagVar(
        'releasedate',
        shortdesc=N_('Release Date'),
    ),
    TagVar(
        'releasestatus',
        shortdesc=N_('Release Status'),
    ),
    TagVar(
        'releasetype',
        shortdesc=N_('Release Type'),
    ),
    TagVar(
        'remixer',
        shortdesc=N_('Remixer'),
    ),
    TagVar(
        'replaygain_album_gain',
        shortdesc=N_('ReplayGain Album Gain'),
        is_calculated=True,
    ),
    TagVar(
        'replaygain_album_peak',
        shortdesc=N_('ReplayGain Album Peak'),
        is_calculated=True,
    ),
    TagVar(
        'replaygain_album_range',
        shortdesc=N_('ReplayGain Album Range'),
        is_calculated=True,
    ),
    TagVar(
        'replaygain_reference_loudness',
        shortdesc=N_('ReplayGain Reference Loudness'),
        is_calculated=True,
    ),
    TagVar(
        'replaygain_track_gain',
        shortdesc=N_('ReplayGain Track Gain'),
        is_calculated=True,
    ),
    TagVar(
        'replaygain_track_peak',
        shortdesc=N_('ReplayGain Track Peak'),
        is_calculated=True,
    ),
    TagVar(
        'replaygain_track_range',
        shortdesc=N_('ReplayGain Track Range'),
        is_calculated=True,
    ),
    TagVar(
        'sample_rate',
        shortdesc=N_('File sample rate'),
        is_file_info=True,
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'secondaryreleasetype',
        shortdesc=N_('FIXME:secondaryreleasetype'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'script',
        shortdesc=N_('Script'),
    ),
    TagVar(
        'silence',
        shortdesc=N_('FIXME:silence'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'show',
        shortdesc=N_('Show Name'),
    ),
    TagVar(
        'showsort',
        shortdesc=N_('Show Name Sort Order'),
    ),
    TagVar(
        'showmovement',
        shortdesc=N_('Show Work & Movement'),
    ),
    TagVar(
        'subtitle',
        shortdesc=N_('Subtitle'),
    ),
    TagVar(
        'syncedlyrics',
        shortdesc=N_('Synced Lyrics'),
    ),
    TagVar(
        'title',
        shortdesc=N_('Title'),
    ),
    TagVar(
        'titlesort',
        shortdesc=N_('Title Sort Order'),
    ),
    TagVar(
        'totalalbumtracks',
        shortdesc=N_('FIXME:totalalbumtracks'),
        is_hidden=True,
        is_tag=False,
    ),
    TagVar(
        'totaldiscs',
        shortdesc=N_('Total Discs'),
    ),
    TagVar(
        'totaltracks',
        shortdesc=N_('Total Tracks'),
    ),
    TagVar(
        'tracknumber',
        shortdesc=N_('Track Number'),
    ),
    TagVar(
        'video',
        shortdesc=N_('File video flag'),
        is_hidden=True,
        is_preserved=True,
        is_tag=False,
    ),
    TagVar(
        'website',
        shortdesc=N_('Artist Website'),
    ),
    TagVar(
        'work',
        shortdesc=N_('Work'),
    ),
    TagVar(
        'writer',
        shortdesc=N_('Writer'),
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
        if tagvar.is_script_variable
    )


def display_tag_name(name):
    return ALL_TAGS.display_name(name)


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
