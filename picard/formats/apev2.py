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
import mutagenext.optimfrog
from picard.file import File
from picard.util import encode_filename, sanitize_date

class APEv2File(File):
    """Generic APEv2-based file."""
    _File = None

    __translate = {
        "Album Artist": "albumartist",
        "MixArtist": "remixer",
        "Weblink": "website",
        "MUSICBRAINZ_ALBUMSTATUS": "releasestatus"
        "MUSICBRAINZ_ALBUMTYPE": "releasetype"
    }

    def read(self):
        file = self._File(encode_filename(self.filename))
        if file.tags:
            for origname, values in file.tags.items():
                for value in values:
                    name = origname
                    if name == "Year":
                        name = "date"
                        value = sanitize_date(value)
                    elif name == "Track":
                        name = "tracknumber"
                        track = value.split("/")
                        if len(track) > 1:
                            self.metadata["totaltracks"] = track[1]
                            value = track[0]
                    elif name == 'Performer' and value.endswith(')'):
                        name = name.lower()
                        start = value.rfind(' (')
                        if start > 0:
                            name += ':' + value[start + 2:-1]
                            value = value[:start]
                    elif name in self.__translate:
                        name = self.__translate[name]
                    else:
                        name = name.lower()
                    self.metadata.add(name, value)
        self._info(file)
        self.orig_metadata.copy(self.metadata)

    def save(self):
        """Save metadata to the file."""
        try:
            tags = mutagen.apev2.APEv2(encode_filename(self.filename))
        except mutagen.apev2.APENoHeaderError:
            tags = mutagen.apev2.APEv2()
        if self.config.setting["clear_existing_tags"]:
            tags.clear()
        temp = {}
        for name, value in self.metadata.items():
            if name.startswith("~"):
                continue
            if name == "date":
                name = "Year"
            # tracknumber/totaltracks => Track
            elif name == 'tracknumber':
                name = 'Track'
                if 'totaltracks' in self.metadata:
                    value = '%s/%s' % (value, self.metadata['totaltracks'])
            # discnumber/totaldiscs => Disc
            elif name == 'discnumber':
                name = 'Disc'
                if 'totaldiscs' in self.metadata:
                    value = '%s/%s' % (value, self.metadata['totaldiscs'])
            elif name in ('totaltracks', 'totaldiscs'):
                continue
            elif name == "albumartist":
                name = "Album Artist"
            # "performer:Piano=Joe Barr" => "Performer=Joe Barr (Piano)"
            elif name.startswith('performer:') or name.startswith('comment:'):
                name, desc = name.split(':', 1)
                name = name.title()
                if desc:
                    value += ' (%s)' % desc
            else:
                name = name.title()
            temp.setdefault(name, []).append(value)
        for name, values in temp.items():
            tags[str(name)] = values
        tags.save(encode_filename(self.filename))

class MusepackFile(APEv2File):
    """Musepack file."""
    EXTENSIONS = [".mpc", ".mp+"]
    NAME = "Musepack"
    _File = mutagen.musepack.Musepack
    def _info(self, file):
        super(MusepackFile, self)._info(file)
        self.metadata['~format'] = "Musepack, SV%d" % file.info.version

class WavPackFile(APEv2File):
    """WavPack file."""
    EXTENSIONS = [".wv"]
    NAME = "WavPack"
    _File = mutagen.wavpack.WavPack
    def _info(self, file):
        super(WavPackFile, self)._info(file)
        self.metadata['~format'] = self.NAME

class OptimFROGFile(APEv2File):
    """OptimFROG file."""
    EXTENSIONS = [".ofr", ".ofs"]
    NAME = "OptimFROG"
    _File = mutagenext.optimfrog.OptimFROG
    def _info(self, file):
        super(OptimFROGFile, self)._info(file)
        if self.filename.lower().endswith(".ofs"):
            self.metadata['~format'] = "OptimFROG DualStream Audio"
        else:
            self.metadata['~format'] = "OptimFROG Lossless Audio"

class MonkeysAudioFile(APEv2File):
    """Monkey's Audio file."""
    EXTENSIONS = [".ape"]
    NAME = "Monkey's Audio"
    _File = mutagen.monkeysaudio.MonkeysAudio
    def _info(self, file):
        super(MonkeysAudioFile, self)._info(file)
        self.metadata['~format'] = self.NAME
