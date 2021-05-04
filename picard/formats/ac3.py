# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020 Philipp Wolfer
# Copyright (C) 2020 Laurent Monin
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

from picard import log
from picard.config import get_config
from picard.formats.apev2 import APEv2File
from picard.util import encode_filename

from .mutagenext import ac3


class AC3File(APEv2File):
    EXTENSIONS = [".ac3", ".eac3"]
    NAME = "AC-3"
    _File = ac3.AC3APEv2

    def _info(self, metadata, file):
        super()._info(metadata, file)

        if hasattr(file.info, 'codec') and file.info.codec == 'ec-3':
            format = 'Enhanced AC-3'
        else:
            format = self.NAME
        if file.tags:
            metadata['~format'] = "%s (APEv2)" % format
        else:
            metadata['~format'] = format

    def _save(self, filename, metadata):
        config = get_config()
        if config.setting['ac3_save_ape']:
            super()._save(filename, metadata)
        elif config.setting['remove_ape_from_ac3']:
            try:
                mutagen.apev2.delete(encode_filename(filename))
            except BaseException:
                log.exception('Error removing APEv2 tags from %s', filename)

    @classmethod
    def supports_tag(cls, name):
        config = get_config()
        if config.setting['ac3_save_ape']:
            return APEv2File.supports_tag(name)
        else:
            return False
