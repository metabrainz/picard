# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018 Antonio Larrosa
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018-2021 Laurent Monin
# Copyright (C) 2018-2021 Philipp Wolfer
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


def prepare_files(src_dir, dst_dir, src_files=None, dst_files=None, src_rel_path='', dst_rel_path=''):
    """Prepare src files and dst filenames for a test."""
    with suppress(FileExistsError):
        os.mkdir(os.path.join(src_dir, src_rel_path))

    # Prepare the source directory structure under src_dir
    # <src_dir>/<src_rel_path>/test.mp3
    # <src_dir>/<src_rel_path>/cover.jpg

    def src_file(name, sample_name=None):
        """Copy file from samples and returns path to temporary file to be
        used as source.
        If sample_name isn't provided, it will use name for it
        """
        if sample_name is None:
            sample_name = name
        sample = os.path.join('test', 'data', sample_name)
        copy_to = os.path.join(src_dir, src_rel_path, name)
        shutil.copy(sample, copy_to)
        return copy_to

    src = dict()
    if src_files:
        for filename, sample_name in src_files.items():
            src[filename] = src_file(filename, sample_name)

    with suppress(FileExistsError):
        os.mkdir(os.path.join(dst_dir, dst_rel_path))

    # Prepare the target filenames under dst_dir
    # <dst_dir>/<dst_rel_path>/test.mp3
    # <dst_dir>/<dst_rel_path>/cover.jpg

    def dst_file(name):
        """Returns path to temporary target file"""
        return os.path.join(dst_dir, dst_rel_path, name)

    dst = dict()
    if dst_files:
        for filename in dst_files:
            dst[filename] = dst_file(filename)

    return src, dst


class SampleFileSystem(PicardTestCase):
    settings = {
        'enabled_plugins': '',
        'move_files': True,
        'move_additional_files': True,
        'move_additional_files_pattern': 'cover.jpg',
    }

    src_files = {
        'test.mp3': None,
        'cover.jpg': 'mb.jpg',
        '.hidden.jpg': 'mb.jpg',
    }

    dst_files = {
        'test.mp3',
        'cover.jpg',
        '.hidden.jpg',
    }

    def setUp(self):
        super().setUp()
        self.src_directory = self.mktmpdir()
        self.dst_directory = self.mktmpdir()
        self.set_config_values(self.settings)

    def _prepare_files(self, src_rel_path='', dst_rel_path=''):
        """Prepare src files and dst filenames for a test."""

        return prepare_files(
            self.src_directory, self.dst_directory,
            self.src_files, self.dst_files,
            src_rel_path=src_rel_path,
            dst_rel_path=dst_rel_path
        )

    def _assertFile(self, path):
        self.assertTrue(os.path.isfile(path))

    def _assertNoFile(self, path):
        self.assertFalse(os.path.isfile(path))


class TestAdditionalFilesMoves(SampleFileSystem):
    src_files = {
        'test.mp3': None,
        'cover1.jpg': 'mb.jpg',
        'cover2.JPG': 'mb.jpg',
        '.hidden1.jpg': 'mb.jpg',
        '.hidden2.JPG': 'mb.jpg',
    }

    dst_files = list(src_files)

    def test_no_pattern(self):
        src, dst = self._prepare_files()
        f = picard.formats.open_(src['test.mp3'])

        moves = set(f._get_additional_files_moves(self.src_directory, self.dst_directory, ()))
        expected = set()
        self.assertEqual(moves, expected)

    def test_no_src_dir(self):
        src, dst = self._prepare_files()
        f = picard.formats.open_(src['test.mp3'])
        patterns = f._compile_move_additional_files_pattern('*.jpg')

        with self.assertRaises(FileNotFoundError):
            moves = set(f._get_additional_files_moves(self.src_directory + 'donotexist', self.dst_directory, patterns))
            del moves

    def test_no_dst_dir(self):
        src, dst = self._prepare_files()
        f = picard.formats.open_(src['test.mp3'])
        patterns = f._compile_move_additional_files_pattern('*.jpg')

        suffix = 'donotexist'
        moves = set(f._get_additional_files_moves(self.src_directory, self.dst_directory + suffix, patterns))
        expected = {
            (src['cover1.jpg'], os.path.join(self.dst_directory + suffix, 'cover1.jpg')),
            (src['cover2.JPG'], os.path.join(self.dst_directory + suffix, 'cover2.JPG')),
        }
        self.assertEqual(moves, expected)

    def test_all_jpg_no_hidden(self):
        src, dst = self._prepare_files()
        f = picard.formats.open_(src['test.mp3'])
        patterns = f._compile_move_additional_files_pattern('*.j?g *.jpg')

        moves = set(f._get_additional_files_moves(self.src_directory, self.dst_directory, patterns))
        expected = {
            (src['cover1.jpg'], dst['cover1.jpg']),
            (src['cover2.JPG'], dst['cover2.JPG']),
        }
        self.assertEqual(moves, expected)

    def test_all_hidden_jpg(self):
        src, dst = self._prepare_files()
        f = picard.formats.open_(src['test.mp3'])
        patterns = f._compile_move_additional_files_pattern('.*.j?g .*.jpg')

        moves = set(f._get_additional_files_moves(self.src_directory, self.dst_directory, patterns))
        expected = {
            (src['.hidden1.jpg'], dst['.hidden1.jpg']),
            (src['.hidden2.JPG'], dst['.hidden2.JPG']),
        }
        self.assertEqual(moves, expected)

    def test_one_only_jpg(self):
        src, dst = self._prepare_files()
        f = picard.formats.open_(src['test.mp3'])
        patterns = f._compile_move_additional_files_pattern('.*1.j?g *1.jpg')

        moves = set(f._get_additional_files_moves(self.src_directory, self.dst_directory, patterns))
        expected = {
            (src['.hidden1.jpg'], dst['.hidden1.jpg']),
            (src['cover1.jpg'], dst['cover1.jpg']),
        }
        self.assertEqual(moves, expected)


class TestFileSystem(SampleFileSystem):

    def _move_additional_files(self, src, dst):
        f = picard.formats.open_(src['test.mp3'])
        f._move_additional_files(src['test.mp3'], dst['test.mp3'], config)

    def _assert_files_moved(self, src, dst):
        self._move_additional_files(src, dst)
        self._assertFile(dst['cover.jpg'])
        self._assertNoFile(src['cover.jpg'])

    def _assert_files_not_moved(self, src, dst):
        self._move_additional_files(src, dst)
        self._assertNoFile(dst['cover.jpg'])
        self._assertFile(src['cover.jpg'])

    def test_move_additional_files_source_unicode(self):
        src, dst = self._prepare_files(src_rel_path='música')
        self._assert_files_moved(src, dst)

    def test_move_additional_files_target_unicode(self):
        src, dst = self._prepare_files(dst_rel_path='música')
        self._assert_files_moved(src, dst)

    def test_move_additional_files_duplicate_patterns(self):
        src, dst = self._prepare_files()
        config.setting['move_additional_files_pattern'] = 'cover.jpg *.jpg'
        self._assert_files_moved(src, dst)

    def test_move_additional_files_hidden_nopattern(self):
        src, dst = self._prepare_files()
        config.setting['move_additional_files_pattern'] = '*.jpg'
        self._assert_files_moved(src, dst)
        self._assertNoFile(dst['.hidden.jpg'])
        self._assertFile(src['.hidden.jpg'])

    def test_move_additional_files_hidden_pattern(self):
        src, dst = self._prepare_files()
        config.setting['move_additional_files_pattern'] = '*.jpg .*.jpg'
        self._assert_files_moved(src, dst)
        self._assertFile(dst['.hidden.jpg'])
        self._assertNoFile(src['.hidden.jpg'])

    def test_move_additional_files_disabled(self):
        config.setting['move_additional_files'] = False
        src, dst = self._prepare_files(src_rel_path='música')
        self._assert_files_not_moved(src, dst)

    def test_move_files_disabled(self):
        config.setting['move_files'] = False
        src, dst = self._prepare_files(src_rel_path='música')
        self._assert_files_not_moved(src, dst)
