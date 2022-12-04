# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018-2020 Philipp Wolfer
# Copyright (C) 2019-2021 Laurent Monin
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


import unittest

from test.picardtestcase import PicardTestCase

from picard import config
from picard.const.sys import IS_WIN
from picard.file import File
from picard.metadata import Metadata
from picard.script import register_script_function
from picard.util.scripttofilename import (
    script_to_filename,
    script_to_filename_with_metadata,
)


settings = {
    'ascii_filenames': False,
    'enabled_plugins': [],
    'windows_compatibility': False,
    'win_compat_replacements': {},
    'replace_spaces_with_underscores': False,
}


def func_has_file(parser):
    return '1' if parser.file else ''


register_script_function(lambda p: '1' if p.file else '', 'has_file')


class ScriptToFilenameTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.set_config_values(settings)

    def test_plain_filename(self):
        metadata = Metadata()
        filename = script_to_filename('AlbumArt', metadata)
        self.assertEqual('AlbumArt', filename)

    def test_simple_script(self):
        metadata = Metadata()
        metadata['artist'] = 'AC/DC'
        metadata['album'] = 'The Album'
        filename = script_to_filename('%album%', metadata)
        self.assertEqual('The Album', filename)
        filename = script_to_filename('%artist%/%album%', metadata)
        self.assertEqual('AC_DC/The Album', filename)

    def test_preserve_backslash(self):
        metadata = Metadata()
        metadata['artist'] = 'AC\\/DC'
        filename = script_to_filename('%artist%', metadata)
        self.assertEqual('AC__DC' if IS_WIN else 'AC\\_DC', filename)

    def test_file_metadata(self):
        metadata = Metadata()
        file = File('somepath/somefile.mp3')
        self.assertEqual('', script_to_filename('$has_file()', metadata))
        self.assertEqual('1', script_to_filename('$has_file()', metadata, file=file))

    def test_script_to_filename_with_metadata(self):
        metadata = Metadata()
        metadata['artist'] = 'Foo'
        metadata['~extension'] = 'foo'
        (filename, new_metadata) = script_to_filename_with_metadata(
            '$set(_extension,bar)\n%artist%', metadata)
        self.assertEqual('Foo', filename)
        self.assertEqual('foo', metadata['~extension'])
        self.assertEqual('bar', new_metadata['~extension'])

    def test_ascii_filenames(self):
        metadata = Metadata()
        metadata['artist'] = 'Die Ärzte'
        settings = config.setting.copy()
        settings['ascii_filenames'] = False
        filename = script_to_filename('%artist% éöü½', metadata, settings=settings)
        self.assertEqual('Die Ärzte éöü½', filename)
        settings['ascii_filenames'] = True
        filename = script_to_filename('%artist% éöü½', metadata, settings=settings)
        self.assertEqual('Die Arzte eou 1_2', filename)

    def test_windows_compatibility(self):
        metadata = Metadata()
        metadata['artist'] = '\\*:'
        settings = config.setting.copy()
        settings['windows_compatibility'] = False
        expect_orig = '\\*:?'
        expect_compat = '____'
        filename = script_to_filename('%artist%?', metadata, settings=settings)
        self.assertEqual(expect_compat if IS_WIN else expect_orig, filename)
        settings['windows_compatibility'] = True
        filename = script_to_filename('%artist%?', metadata, settings=settings)
        self.assertEqual(expect_compat, filename)

    def test_windows_compatibility_custom_replacements(self):
        metadata = Metadata()
        metadata['artist'] = '\\*:'
        expect_compat = '_+_!'
        settings = config.setting.copy()
        settings['windows_compatibility'] = True
        settings['win_compat_replacements'] = {
            '*': '+',
            '?': '!',
        }
        filename = script_to_filename('%artist%?', metadata, settings=settings)
        self.assertEqual(expect_compat, filename)

    def test_replace_spaces_with_underscores(self):
        metadata = Metadata()
        metadata['artist'] = ' The \t  New* _ Artist  '
        settings = config.setting.copy()
        settings['windows_compatibility'] = True
        settings['replace_spaces_with_underscores'] = False
        filename = script_to_filename('%artist%', metadata, settings=settings)
        self.assertEqual(' The \t  New_ _ Artist  ', filename)
        settings['replace_spaces_with_underscores'] = True
        filename = script_to_filename('%artist%', metadata, settings=settings)
        self.assertEqual('The_New_Artist', filename)

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_ascii_win_save(self):
        self._test_ascii_windows_compatibility()

    def test_ascii_win_compat(self):
        config.setting['windows_compatibility'] = True
        self._test_ascii_windows_compatibility()

    def _test_ascii_windows_compatibility(self):
        metadata = Metadata()
        metadata['artist'] = '\u2216/\\\u2215'
        settings = config.setting.copy()
        settings['ascii_filenames'] = True
        filename = script_to_filename('%artist%/\u2216\\\\\u2215', metadata, settings=settings)
        self.assertEqual('____/_\\_', filename)

    def test_remove_null_chars(self):
        metadata = Metadata()
        filename = script_to_filename('a\x00b\x00', metadata)
        self.assertEqual('ab', filename)

    def test_remove_tabs_and_linebreaks_chars(self):
        metadata = Metadata()
        filename = script_to_filename('a\tb\nc', metadata)
        self.assertEqual('abc', filename)

    def test_remove_leading_and_trailing_whitespace(self):
        metadata = Metadata()
        metadata['artist'] = 'The Artist'
        filename = script_to_filename(' %artist% ', metadata)
        self.assertEqual(' The Artist ', filename)
