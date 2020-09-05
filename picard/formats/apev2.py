# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2009, 2011 Lukáš Lalinský
# Copyright (C) 2009-2011, 2018-2020 Philipp Wolfer
# Copyright (C) 2011-2014 Wieland Hoffmann
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013-2015, 2018-2019 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Ville Skyttä
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


from __future__ import absolute_import

from os.path import isfile
import re

import mutagen.apev2
import mutagen.monkeysaudio
import mutagen.musepack
import mutagen.optimfrog
import mutagen.wavpack

from picard import (
    config,
    log,
)
from picard.coverart.image import (
    CoverArtImageError,
    TagCoverArtImage,
)
from picard.file import File
from picard.metadata import Metadata
from picard.util import (
    encode_filename,
    sanitize_date,
)

from .mutagenext import (
    aac,
    tak,
)


INVALID_CHARS = re.compile('[^\x20-\x7e]')
DISALLOWED_KEYS = ['ID3', 'TAG', 'OggS', 'MP+']
UNSUPPORTED_TAGS = [
    'gapless',
    'musicip_fingerprint',
    'podcast',
    'podcasturl',
    'show',
    'showsort',
    'r128_album_gain',
    'r128_track_gain',
]


def is_valid_key(key):
    """
    Return true if a string is a valid APE tag key.
    APE tag item keys can have a length of 2 (including) up to 255 (including)
    characters in the range from 0x20 (Space) until 0x7E (Tilde).
    Not allowed are the following keys: ID3, TAG, OggS and MP+.

    See http://wiki.hydrogenaud.io/index.php?title=APE_key
    """
    return (key and 2 <= len(key) <= 255
            and key not in DISALLOWED_KEYS
            and INVALID_CHARS.search(key) is None)


class APEv2File(File):

    """Generic APEv2-based file."""
    _File = None

    __translate = {
        "albumartist": "Album Artist",
        "remixer": "MixArtist",
        "website": "Weblink",
        "discsubtitle": "DiscSubtitle",
        "bpm": "BPM",
        "isrc": "ISRC",
        "catalognumber": "CatalogNumber",
        "barcode": "Barcode",
        "encodedby": "EncodedBy",
        "language": "Language",
        "movementnumber": "MOVEMENT",
        "movement": "MOVEMENTNAME",
        "movementtotal": "MOVEMENTTOTAL",
        "showmovement": "SHOWMOVEMENT",
        "releasestatus": "MUSICBRAINZ_ALBUMSTATUS",
        "releasetype": "MUSICBRAINZ_ALBUMTYPE",
        "musicbrainz_recordingid": "musicbrainz_trackid",
        "musicbrainz_trackid": "musicbrainz_releasetrackid",
        "originalartist": "Original Artist",
        "replaygain_album_gain": "REPLAYGAIN_ALBUM_GAIN",
        "replaygain_album_peak": "REPLAYGAIN_ALBUM_PEAK",
        "replaygain_album_range": "REPLAYGAIN_ALBUM_RANGE",
        "replaygain_track_gain": "REPLAYGAIN_TRACK_GAIN",
        "replaygain_track_peak": "REPLAYGAIN_TRACK_PEAK",
        "replaygain_track_range": "REPLAYGAIN_TRACK_RANGE",
        "replaygain_reference_loudness": "REPLAYGAIN_REFERENCE_LOUDNESS",
    }
    __rtranslate = dict([(v.lower(), k) for k, v in __translate.items()])

    def __init__(self, filename):
        super().__init__(filename)
        self.__casemap = {}

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        self.__casemap = {}
        file = self._File(encode_filename(filename))
        metadata = Metadata()
        if file.tags:
            for origname, values in file.tags.items():
                name_lower = origname.lower()
                if (values.kind == mutagen.apev2.BINARY
                    and name_lower.startswith("cover art")):
                    if b'\0' in values.value:
                        descr, data = values.value.split(b'\0', 1)
                        try:
                            coverartimage = TagCoverArtImage(
                                file=filename,
                                tag=name_lower,
                                data=data,
                            )
                        except CoverArtImageError as e:
                            log.error('Cannot load image from %r: %s' %
                                      (filename, e))
                        else:
                            metadata.images.append(coverartimage)

                # skip EXTERNAL and BINARY values
                if values.kind != mutagen.apev2.TEXT:
                    continue
                for value in values:
                    name = name_lower
                    if name == "year":
                        name = "date"
                        value = sanitize_date(value)
                    elif name == "track":
                        name = "tracknumber"
                        track = value.split("/")
                        if len(track) > 1:
                            metadata["totaltracks"] = track[1]
                            value = track[0]
                    elif name == "disc":
                        name = "discnumber"
                        disc = value.split("/")
                        if len(disc) > 1:
                            metadata["totaldiscs"] = disc[1]
                            value = disc[0]
                    elif name in ('performer', 'comment'):
                        if value.endswith(')'):
                            start = value.rfind(' (')
                            if start > 0:
                                name += ':' + value[start + 2:-1]
                                value = value[:start]
                    elif name in self.__rtranslate:
                        name = self.__rtranslate[name]
                    self.__casemap[name] = origname
                    metadata.add(name, value)
        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata):
        """Save metadata to the file."""
        log.debug("Saving file %r", filename)
        try:
            tags = mutagen.apev2.APEv2(encode_filename(filename))
        except mutagen.apev2.APENoHeaderError:
            tags = mutagen.apev2.APEv2()
        images_to_save = list(metadata.images.to_be_saved_to_tags())
        if config.setting["clear_existing_tags"]:
            tags.clear()
        elif images_to_save:
            for name, value in tags.items():
                if (value.kind == mutagen.apev2.BINARY
                    and name.lower().startswith('cover art')):
                    del tags[name]
        temp = {}
        for name, value in metadata.items():
            if name.startswith("~") or not self.supports_tag(name):
                continue
            real_name = self._get_tag_name(name)
            # tracknumber/totaltracks => Track
            if name == 'tracknumber':
                if 'totaltracks' in metadata:
                    value = '%s/%s' % (value, metadata['totaltracks'])
            # discnumber/totaldiscs => Disc
            elif name == 'discnumber':
                if 'totaldiscs' in metadata:
                    value = '%s/%s' % (value, metadata['totaldiscs'])
            elif name in ('totaltracks', 'totaldiscs'):
                continue
            # "performer:Piano=Joe Barr" => "Performer=Joe Barr (Piano)"
            elif name.startswith('performer:') or name.startswith('comment:'):
                name, desc = name.split(':', 1)
                if desc:
                    value += ' (%s)' % desc
            temp.setdefault(real_name, []).append(value)
        for name, values in temp.items():
            tags[name] = values
        for image in images_to_save:
            cover_filename = 'Cover Art (Front)'
            cover_filename += image.extension
            tags['Cover Art (Front)'] = mutagen.apev2.APEValue(
                cover_filename.encode('ascii') + b'\0' + image.data, mutagen.apev2.BINARY)
            break
            # can't save more than one item with the same name
            # (mp3tags does this, but it's against the specs)

        self._remove_deleted_tags(metadata, tags)
        tags.save(encode_filename(filename))

    def _remove_deleted_tags(self, metadata, tags):
        """Remove the tags from the file that were deleted in the UI"""
        for tag in metadata.deleted_tags:
            real_name = self._get_tag_name(tag)
            if real_name in ('Lyrics', 'Comment', 'Performer'):
                parts = tag.split(':', 1)
                if len(parts) == 2:
                    tag_type_regex = re.compile(r"\(%s\)$" % re.escape(parts[1]))
                else:
                    tag_type_regex = re.compile(r"[^)]$")
                existing_tags = tags.get(real_name, [])
                for item in existing_tags:
                    if re.search(tag_type_regex, item):
                        existing_tags.remove(item)
                tags[real_name] = existing_tags
            elif tag in ('totaltracks', 'totaldiscs'):
                tagstr = real_name.lower() + 'number'
                if tagstr in metadata:
                    tags[real_name] = metadata[tagstr]
            else:
                if real_name in tags:
                    del tags[real_name]

    def _get_tag_name(self, name):
        if name in self.__casemap:
            return self.__casemap[name]
        elif name.startswith('lyrics:'):
            return 'Lyrics'
        elif name == 'date':
            return 'Year'
        elif name in ('tracknumber', 'totaltracks'):
            return 'Track'
        elif name in ('discnumber', 'totaldiscs'):
            return 'Disc'
        elif name.startswith('performer:') or name.startswith('comment:'):
            return name.split(':', 1)[0].title()
        elif name in self.__translate:
            return self.__translate[name]
        else:
            return name.title()

    @classmethod
    def supports_tag(cls, name):
        return (bool(name) and name not in UNSUPPORTED_TAGS
                and (is_valid_key(name)
                    or name.startswith('comment:')
                    or name.startswith('lyrics:')
                    or name.startswith('performer:')))


class MusepackFile(APEv2File):

    """Musepack file."""
    EXTENSIONS = [".mpc", ".mp+"]
    NAME = "Musepack"
    _File = mutagen.musepack.Musepack

    def _info(self, metadata, file):
        super()._info(metadata, file)
        metadata['~format'] = "Musepack, SV%d" % file.info.version


class WavPackFile(APEv2File):

    """WavPack file."""
    EXTENSIONS = [".wv"]
    NAME = "WavPack"
    _File = mutagen.wavpack.WavPack

    def _save_and_rename(self, old_filename, metadata):
        """Includes an additional check for WavPack correction files"""
        wvc_filename = old_filename.replace(".wv", ".wvc")
        if isfile(wvc_filename):
            if config.setting["rename_files"] or config.setting["move_files"]:
                self._rename(wvc_filename, metadata)
        return File._save_and_rename(self, old_filename, metadata)


class OptimFROGFile(APEv2File):

    """OptimFROG file."""
    EXTENSIONS = [".ofr", ".ofs"]
    NAME = "OptimFROG"
    _File = mutagen.optimfrog.OptimFROG

    def _info(self, metadata, file):
        super()._info(metadata, file)
        # mutagen.File.filename can be either a bytes or str object
        filename = file.filename
        if isinstance(filename, bytes):
            filename = filename.decode()
        if filename.lower().endswith(".ofs"):
            metadata['~format'] = "OptimFROG DualStream Audio"
        else:
            metadata['~format'] = "OptimFROG Lossless Audio"


class MonkeysAudioFile(APEv2File):

    """Monkey's Audio file."""
    EXTENSIONS = [".ape"]
    NAME = "Monkey's Audio"
    _File = mutagen.monkeysaudio.MonkeysAudio


class TAKFile(APEv2File):

    """TAK file."""
    EXTENSIONS = [".tak"]
    NAME = "Tom's lossless Audio Kompressor"
    _File = tak.TAK


class AACFile(APEv2File):
    EXTENSIONS = [".aac"]
    NAME = "AAC"
    _File = aac.AACAPEv2

    def _info(self, metadata, file):
        super()._info(metadata, file)
        if file.tags:
            metadata['~format'] = "%s (APEv2)" % self.NAME

    def _save(self, filename, metadata):
        if config.setting['aac_save_ape']:
            super()._save(filename, metadata)
        elif config.setting['remove_ape_from_aac']:
            try:
                mutagen.apev2.delete(encode_filename(filename))
            except BaseException:
                log.exception('Error removing APEv2 tags from %s', filename)

    @classmethod
    def supports_tag(cls, name):
        if config.setting['aac_save_ape']:
            return APEv2File.supports_tag(name)
        else:
            return False
