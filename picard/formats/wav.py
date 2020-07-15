# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2012-2013, 2017 Wieland Hoffmann
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Laurent Monin
# Copyright (C) 2018-2020 Philipp Wolfer
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

from collections.abc import MutableMapping

import mutagen

from picard import (
    config,
    log,
)
from picard.file import File
from picard.formats.id3 import NonCompatID3File
from picard.metadata import Metadata


try:
    import mutagen.wave
    from mutagen._iff import assert_valid_chunk_id
    from mutagen._riff import RiffFile
    from mutagen._util import loadfile

    # See https://exiftool.org/TagNames/RIFF.html
    TRANSLATE_RIFF_INFO = {
        # Minimal, as e.g. supported by Windows Explorer,
        # Audacity and foobar2000
        'IART': 'artist',
        'ICMT': 'comment',
        'ICOP': 'copyright',
        'ICRD': 'date',
        'IGNR': 'genre',
        'INAM': 'title',
        'IPRD': 'album',
        'ITRK': 'tracknumber',

        # Extended, not well supported by other tools
        'ICNT': 'releasecountry',
        'IENC': 'encodedby',
        'IENG': 'engineer',
        'ILNG': 'language',
        'IMED': 'media',
        'IMUS': 'composer',
        'IPRO': 'producer',
        'IWRI': 'writer',
    }

    R_TRANSLATE_RIFF_INFO = dict([(v, k) for k, v in TRANSLATE_RIFF_INFO.items()])

    def translate_tag_to_riff_name(name):
        if name.startswith('comment:'):
            name = 'comment'
        return R_TRANSLATE_RIFF_INFO.get(name, None)

    class RiffListInfo(MutableMapping):
        """Allows loading / saving RIFF INFO tags from / to RIFF files.
        """

        def __init__(self, encoding='windows-1252'):
            self.encoding = encoding
            self.__tags = {}
            self.__deleted_tags = set()

        @loadfile()
        def load(self, filething):
            """Load the INFO tags from the file."""
            riff_file = RiffFile(filething.fileobj)
            info = self.__find_info_chunk(riff_file.root)
            if info:
                for tag in info.subchunks():
                    self.__tags[tag.id] = self.__decode_data(tag.read())

        @loadfile(writable=True)
        def save(self, filething):
            """Save the INFO tags to the file."""
            riff_file = RiffFile(filething.fileobj)
            info = self.__find_info_chunk(riff_file.root)
            if not info:
                info = riff_file.insert_chunk('LIST', b'INFO')
            for name, value in self.__tags.items():
                self.__save_tag_data(info, name, value)
            for name in self.__deleted_tags:
                self.__delete_tag(info, name)

        @loadfile(writable=True)
        def delete(self, filething):
            """Deletes the INFO chunk completely from the file."""
            riff_file = RiffFile(filething.fileobj)
            info = self.__find_info_chunk(riff_file.root)
            if info:
                info.delete()

        @staticmethod
        def __find_info_chunk(parent):
            for chunk in parent.subchunks():
                if chunk.id == 'LIST' and chunk.name == 'INFO':
                    return chunk
            return None

        @staticmethod
        def __find_subchunk(parent, name):
            for chunk in parent.subchunks():
                if chunk.id == name:
                    return chunk
            return None

        def __save_tag_data(self, info, name, value):
            data = self.__encode_data(value)
            chunk = self.__find_subchunk(info, name)
            if chunk:
                chunk.resize(len(data))
                chunk.write(data)
                return chunk
            else:
                return info.insert_chunk(name, data)

        def __delete_tag(self, info, name):
            chunk = self.__find_subchunk(info, name)
            if chunk:
                chunk.delete()

        @staticmethod
        def __decode_data(value):
            try:  # Always try first to decode as Unicode
                value = value.decode('utf-8')
            except UnicodeDecodeError:  # Fall back to Windows-1252 encoding
                value = value.decode('windows-1252', errors='replace')
            return value.rstrip('\0')

        def __encode_data(self, value):
            return value.encode(self.encoding, errors='replace') + b'\x00'

        def __contains__(self, name):
            return self.__tags.__contains__(name)

        def __getitem__(self, key):
            return self.__tags.get(key)

        def __setitem__(self, key, value):
            assert_valid_chunk_id(key)
            self.__tags[key] = value
            self.__deleted_tags.discard(key)

        def __delitem__(self, key):
            if key in self.__tags:
                del self.__tags[key]
            self.__deleted_tags.add(key)

        def __iter__(self):
            return iter(self.__tags)

        def __len__(self):
            return len(self.__tags)

        def __repr__(self):
            return repr(self.__tags)

        def __str__(self):
            return str(self.__tags)

    class WAVFile(NonCompatID3File):
        EXTENSIONS = [".wav"]
        NAME = "Microsoft WAVE"
        _File = mutagen.wave.WAVE

        def _info(self, metadata, file):
            super()._info(metadata, file)
            metadata['~format'] = self.NAME

            info = RiffListInfo(encoding=config.setting['wave_riff_info_encoding'])
            info.load(file.filename)
            for tag, value in info.items():
                if tag in TRANSLATE_RIFF_INFO:
                    name = TRANSLATE_RIFF_INFO[tag]
                    if name not in metadata:
                        metadata[name] = value

        def _save(self, filename, metadata):
            super()._save(filename, metadata)

            # Save RIFF LIST INFO
            if config.setting['write_wave_riff_info']:
                info = RiffListInfo(encoding=config.setting['wave_riff_info_encoding'])
                if config.setting['clear_existing_tags']:
                    info.delete(filename)
                for name, values in metadata.rawitems():
                    name = translate_tag_to_riff_name(name)
                    if name:
                        value = ", ".join(values)
                        info[name] = value
                for name in metadata.deleted_tags:
                    name = translate_tag_to_riff_name(name)
                    if name:
                        del info[name]
                info.save(filename)
            elif config.setting['remove_wave_riff_info']:
                info = RiffListInfo(encoding=config.setting['wave_riff_info_encoding'])
                info.delete(filename)

except ImportError:
    import wave

    class WAVFile(File):
        EXTENSIONS = [".wav"]
        NAME = "Microsoft WAVE"
        _File = None

        def _load(self, filename):
            log.debug("Loading file %r", filename)
            f = wave.open(filename, "rb")
            metadata = Metadata()
            metadata['~channels'] = f.getnchannels()
            metadata['~bits_per_sample'] = f.getsampwidth() * 8
            metadata['~sample_rate'] = f.getframerate()
            metadata.length = 1000 * f.getnframes() // f.getframerate()
            metadata['~format'] = self.NAME
            self._add_path_to_metadata(metadata)
            return metadata

        def _save(self, filename, metadata):
            log.debug("Saving file %r", filename)

        @classmethod
        def supports_tag(cls, name):
            return False
