# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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

import os.path

from test.picardtestcase import PicardTestCase

from picard.formats import util
from picard.formats.id3 import MP3File


class FormatsOpenTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values({'enabled_plugins': []})

    def test_open(self):
        file_path = os.path.join('test', 'data', 'test.mp3')
        filename = self.copy_file_tmp(file_path, '.mp3')
        filetype = util.open_(filename)
        self.assertIsInstance(filetype, MP3File)

    def test_open_no_extension(self):
        file_path = os.path.join('test', 'data', 'test.mp3')
        filename = self.copy_file_tmp(file_path, '')
        filetype = util.open_(filename)
        self.assertIsInstance(filetype, MP3File)

    def test_open_unknown_extension(self):
        file_path = os.path.join('test', 'data', 'test.mp3')
        filename = self.copy_file_tmp(file_path, '.fake')
        filetype = util.open_(filename)
        self.assertIsInstance(filetype, MP3File)

    def test_open_unknown_type(self):
        file_path = os.path.join('test', 'data', 'mb.png')
        filename = self.copy_file_tmp(file_path, '.ogg')
        filetype = util.open_(filename)
        self.assertIsNone(filetype)
