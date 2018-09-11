# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2012-2013, 2017 Wieland Hoffmann
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Laurent Monin
# Copyright (C) 2018-2019 Philipp Wolfer
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

import mutagen

from picard import (
    config,
    log,
)
from picard.file import File
from picard.formats.id3 import ID3File
from picard.formats.mutagenext import compatid3
from picard.metadata import Metadata


try:
    import mutagen.wave

    class WAVFile(ID3File):
        EXTENSIONS = [".wav"]
        NAME = "Microsoft WAVE"
        _File = mutagen.wave.WAVE

        def _get_file(self, filename):
            return self._File(filename, known_frames=compatid3.known_frames)

        def _info(self, metadata, file):
            super()._info(metadata, file)
            metadata['~format'] = self.NAME

        def _get_tags(self, filename):
            file = self._get_file(filename)
            if file.tags is None:
                file.add_tags()
            return file.tags

        def _save_tags(self, tags, filename):
            if config.setting['write_id3v23']:
                tags.update_to_v23()
                separator = config.setting['id3v23_join_with']
                tags.save(filename, v2_version=3, v23_sep=separator)
            else:
                tags.update_to_v24()
                tags.save(filename, v2_version=4)

        @classmethod
        def supports_tag(cls, name):
            return (super().supports_tag(name)
                    and name not in {'albumsort',
                                     'artistsort',
                                     'discsubtitle',
                                     'titlesort'})

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
