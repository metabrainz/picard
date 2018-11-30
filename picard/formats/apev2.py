# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

from .mutagenext import tak


class APEv2File(File):

    """Generic APEv2-based file."""
    _File = None

    __translate = {
        "Album Artist": "albumartist",
        "MixArtist": "remixer",
        "Weblink": "website",
        "DiscSubtitle": "discsubtitle",
        "BPM": "bpm",
        "ISRC": "isrc",
        "CatalogNumber": "catalognumber",
        "Barcode": "barcode",
        "EncodedBy": "encodedby",
        "Language": "language",
        "MOVEMENT": "movementnumber",
        "MOVEMENTNAME": "movement",
        "MOVEMENTTOTAL": "movementtotal",
        "SHOWMOVEMENT": "showmovement",
        "MUSICBRAINZ_ALBUMSTATUS": "releasestatus",
        "MUSICBRAINZ_ALBUMTYPE": "releasetype",
        "musicbrainz_trackid": "musicbrainz_recordingid",
        "musicbrainz_releasetrackid": "musicbrainz_trackid",
        "Original Artist": "originalartist",
    }
    __rtranslate = dict([(v, k) for k, v in __translate.items()])

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        file = self._File(encode_filename(filename))
        metadata = Metadata()
        if file.tags:
            for origname, values in file.tags.items():
                if origname.lower().startswith("cover art") and values.kind == mutagen.apev2.BINARY:
                    if b'\0' in values.value:
                        descr, data = values.value.split(b'\0', 1)
                        try:
                            coverartimage = TagCoverArtImage(
                                file=filename,
                                tag=origname,
                                data=data,
                            )
                        except CoverArtImageError as e:
                            log.error('Cannot load image from %r: %s' %
                                      (filename, e))
                        else:
                            metadata.append_image(coverartimage)

                # skip EXTERNAL and BINARY values
                if values.kind != mutagen.apev2.TEXT:
                    continue
                for value in values:
                    name = origname
                    if name == "Year":
                        name = "date"
                        value = sanitize_date(value)
                    elif name == "Track":
                        name = "tracknumber"
                        track = value.split("/")
                        if len(track) > 1:
                            metadata["totaltracks"] = track[1]
                            value = track[0]
                    elif name == "Disc":
                        name = "discnumber"
                        disc = value.split("/")
                        if len(disc) > 1:
                            metadata["totaldiscs"] = disc[1]
                            value = disc[0]
                    elif name == 'Performer' or name == 'Comment':
                        name = name.lower() + ':'
                        if value.endswith(')'):
                            start = value.rfind(' (')
                            if start > 0:
                                name += value[start + 2:-1]
                                value = value[:start]
                    elif name in self.__translate:
                        name = self.__translate[name]
                    else:
                        name = name.lower()
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
        if config.setting["clear_existing_tags"]:
            tags.clear()
        elif metadata.images_to_be_saved_to_tags:
            for name, value in tags.items():
                if name.lower().startswith('cover art') and value.kind == mutagen.apev2.BINARY:
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
        for image in metadata.images_to_be_saved_to_tags:
            cover_filename = 'Cover Art (Front)'
            cover_filename += image.extension
            tags['Cover Art (Front)'] = mutagen.apev2.APEValue(cover_filename.encode('ascii') + b'\0' + image.data, mutagen.apev2.BINARY)
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
                tag_type = re.compile(r"\(%s\)" % tag.split(':', 1)[1])
                existing_tags = tags.get(real_name)
                if existing_tags:
                    for item in existing_tags:
                        if tag_type.search(item):
                            tags.get(real_name).remove(item)
            elif tag in ('totaltracks', 'totaldiscs'):
                tagstr = real_name.lower() + 'number'
                if tagstr in metadata:
                    tags[real_name] = metadata[tagstr]
            else:
                if real_name in tags:
                    del tags[real_name]

    def _get_tag_name(self, name):
        if name.startswith('lyrics:'):
            return 'Lyrics'
        elif name == 'date':
            return 'Year'
        elif name in ('tracknumber', 'totaltracks'):
            return 'Track'
        elif name in ('discnumber', 'totaldiscs'):
            return 'Disc'
        elif name.startswith('performer:') or name.startswith('comment:'):
            return name.split(':', 1)[0].title()
        elif name in self.__rtranslate:
            return self.__rtranslate[name]
        else:
            return name.title()

    @classmethod
    def supports_tag(cls, name):
        unsupported_tags = {
            'gapless',
            'musicip_fingerprint',
            'podcast',
            'podcasturl',
            'show',
            'showsort',
        }
        return bool(name) and name not in unsupported_tags


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
