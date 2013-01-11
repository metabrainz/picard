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

import mutagen.apev2
import mutagen.monkeysaudio
import mutagen.musepack
import mutagen.wavpack
import mutagen.optimfrog
import mutagenext.tak
from picard.file import File
from picard.metadata import Metadata
from picard.util import encode_filename, sanitize_date, mimetype
from os.path import isfile

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
        "MUSICBRAINZ_ALBUMSTATUS": "releasestatus",
        "MUSICBRAINZ_ALBUMTYPE": "releasetype",
    }
    __rtranslate = dict([(v, k) for k, v in __translate.iteritems()])

    def _load(self, filename):
        self.log.debug("Loading file %r", filename)
        file = self._File(encode_filename(filename))
        metadata = Metadata()
        if file.tags:
            for origname, values in file.tags.items():
                if origname.lower().startswith("cover art") and values.kind == mutagen.apev2.BINARY:
                    if '\0' in values.value:
                        descr, data = values.value.split('\0', 1)
                        mime = mimetype.get_from_data(data, descr, 'image/jpeg')
                        metadata.add_image(mime, data)
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

    def _save(self, filename, metadata, settings):
        """Save metadata to the file."""
        self.log.debug("Saving file %r", filename)
        try:
            tags = mutagen.apev2.APEv2(encode_filename(filename))
        except mutagen.apev2.APENoHeaderError:
            tags = mutagen.apev2.APEv2()
        if settings["clear_existing_tags"]:
            tags.clear()
        elif settings['save_images_to_tags'] and metadata.images:
            for name, value in tags.items():
                if name.lower().startswith('cover art') and value.kind == mutagen.apev2.BINARY:
                    del tags[name]
        temp = {}
        for name, value in metadata.items():
            if name.startswith("~"):
                continue
            if name.startswith('lyrics:'):
                name = 'Lyrics'
            elif name == "date":
                name = "Year"
            # tracknumber/totaltracks => Track
            elif name == 'tracknumber':
                name = 'Track'
                if 'totaltracks' in metadata:
                    value = '%s/%s' % (value, metadata['totaltracks'])
            # discnumber/totaldiscs => Disc
            elif name == 'discnumber':
                name = 'Disc'
                if 'totaldiscs' in metadata:
                    value = '%s/%s' % (value, metadata['totaldiscs'])
            elif name in ('totaltracks', 'totaldiscs'):
                continue
            # "performer:Piano=Joe Barr" => "Performer=Joe Barr (Piano)"
            elif name.startswith('performer:') or name.startswith('comment:'):
                name, desc = name.split(':', 1)
                name = name.title()
                if desc:
                    value += ' (%s)' % desc
            elif name in self.__rtranslate:
                name = self.__rtranslate[name]
            else:
                name = name.title()
            temp.setdefault(name, []).append(value)
        for name, values in temp.items():
            tags[str(name)] = values
        if settings['save_images_to_tags']:
            for image in metadata.images:
                if image.is_main_cover:
                    cover_filename = 'Cover Art (Front)'
                    cover_filename += mimetype.get_extension(image.mime, '.jpg')
                    tags['Cover Art (Front)'] = cover_filename + '\0' + image.data
                    break # can't save more than one item with the same name
                        # (mp3tags does this, but it's against the specs)
        tags.save(encode_filename(filename))

class MusepackFile(APEv2File):
    """Musepack file."""
    EXTENSIONS = [".mpc", ".mp+"]
    NAME = "Musepack"
    _File = mutagen.musepack.Musepack
    def _info(self, metadata, file):
        super(MusepackFile, self)._info(metadata, file)
        metadata['~format'] = "Musepack, SV%d" % file.info.version

class WavPackFile(APEv2File):
    """WavPack file."""
    EXTENSIONS = [".wv"]
    NAME = "WavPack"
    _File = mutagen.wavpack.WavPack
    def _info(self, metadata, file):
        super(WavPackFile, self)._info(metadata, file)
        metadata['~format'] = self.NAME

    def _save_and_rename(self, old_filename, metadata, settings):
        """Includes an additional check for WavPack correction files"""
        wvc_filename = old_filename.replace(".wv", ".wvc")
        if isfile(wvc_filename):
            if settings["rename_files"] or settings["move_files"]:
                self._rename(wvc_filename, metadata, settings)
        return File._save_and_rename(self, old_filename, metadata, settings)

class OptimFROGFile(APEv2File):
    """OptimFROG file."""
    EXTENSIONS = [".ofr", ".ofs"]
    NAME = "OptimFROG"
    _File = mutagen.optimfrog.OptimFROG
    def _info(self, metadata, file):
        super(OptimFROGFile, self)._info(metadata, file)
        if file.filename.lower().endswith(".ofs"):
            metadata['~format'] = "OptimFROG DualStream Audio"
        else:
            metadata['~format'] = "OptimFROG Lossless Audio"

class MonkeysAudioFile(APEv2File):
    """Monkey's Audio file."""
    EXTENSIONS = [".ape"]
    NAME = "Monkey's Audio"
    _File = mutagen.monkeysaudio.MonkeysAudio
    def _info(self, metadata, file):
        super(MonkeysAudioFile, self)._info(metadata, file)
        metadata['~format'] = self.NAME

class TAKFile(APEv2File):
    """TAK file."""
    EXTENSIONS = [".tak"]
    NAME = "Tom's lossless Audio Kompressor"
    _File = mutagenext.tak.TAK
    def _info(self, metadata, file):
        super(TAKFile, self)._info(metadata, file)
        metadata['~format'] = self.NAME
