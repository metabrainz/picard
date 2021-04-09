# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018 Antonio Larrosa
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018-2019 Philipp Wolfer
# Copyright (C) 2018-2020 Laurent Monin
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


from contextlib import suppress
import os.path
import shutil

from test.picardtestcase import PicardTestCase

from picard import config
import picard.formats


settings = {
    'enabled_plugins': '',
    'move_files': True,
    'move_additional_files': True,
    'move_additional_files_pattern': 'cover.jpg',
}


class TestFileSystem(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.src_directory = self.mktmpdir()
        self.tgt_directory = self.mktmpdir()
        self.set_config_values(settings)

    def _prepare_files(self, src_rel_path='', tgt_rel_path=''):
        """Prepare src files and tgt filenames for a test."""
        with suppress(FileExistsError):
            os.mkdir(os.path.join(self.src_directory, src_rel_path))

        # Prepare the source directory structure under self.src_directory
        # .../<src_rel_path>/test.mp3
        # .../<src_rel_path>/cover.jpg

        def src_file(name, sample_name=None):
            """Copy file from samples and returns path to temporary file to be
            used as source.
            If sample_name isn't provided, it will use name for it
            """
            if sample_name is None:
                sample_name = name
            sample = os.path.join('test', 'data', sample_name)
            copy_to = os.path.join(self.src_directory, src_rel_path, name)
            shutil.copy(sample, copy_to)
            return copy_to

        files = dict()
        files['old_mp3'] = src_file('test.mp3')
        files['old_img'] = src_file('cover.jpg', 'mb.jpg')
        files['old_hidden_img'] = src_file('.hidden.jpg', 'mb.jpg')

        with suppress(FileExistsError):
            os.mkdir(os.path.join(self.tgt_directory, tgt_rel_path))

        # Prepare the target filenames under self.tgt_directory
        # .../<tgt_rel_path>/test.mp3
        # .../<tgt_rel_path>/cover.jpg

        def tgt_file(name):
            """Returns path to temporary target file"""
            return os.path.join(self.tgt_directory, tgt_rel_path, name)

        files['new_mp3'] = tgt_file('test.mp3')
        files['new_img'] = tgt_file('cover.jpg')
        files['new_hidden_img'] = tgt_file('.hidden.jpg')

        return files

    def _assertFile(self, path):
        self.assertTrue(os.path.isfile(path))

    def _assertNoFile(self, path):
        self.assertFalse(os.path.isfile(path))

    def _move_additional_files(self, files):
        f = picard.formats.open_(files['old_mp3'])
        f._move_additional_files(files['old_mp3'], files['new_mp3'])

        self._assertFile(files['new_img'])
        self._assertNoFile(files['old_img'])

    def test_move_additional_files_source_unicode(self):
        files = self._prepare_files(src_rel_path='música')

        self._move_additional_files(files)

    def test_move_additional_files_target_unicode(self):
        files = self._prepare_files(tgt_rel_path='música')

        self._move_additional_files(files)

    def test_move_additional_files_duplicate_patterns(self):
        files = self._prepare_files()

        config.setting['move_additional_files_pattern'] = 'cover.jpg *.jpg'

        self._move_additional_files(files)

    def test_move_additional_files_hidden_nopattern(self):
        files = self._prepare_files()

        config.setting['move_additional_files_pattern'] = '*.jpg'

        self._move_additional_files(files)

        self._assertNoFile(files['new_hidden_img'])
        self._assertFile(files['old_hidden_img'])

    def test_move_additional_files_hidden_pattern(self):
        files = self._prepare_files()

        config.setting['move_additional_files_pattern'] = '*.jpg .*.jpg'

        self._move_additional_files(files)

        self._assertFile(files['new_hidden_img'])
        self._assertNoFile(files['old_hidden_img'])
