# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018-2026 Philipp Wolfer
# Copyright (C) 2019-2022, 2024 Laurent Monin
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Sophist-UK
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

import os
import re
from types import GeneratorType
import unittest
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase
from test.test_coverart_image import create_image

from picard import config
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.file import File
from picard.metadata import Metadata
from picard.tags import (
    calculated_tag_names,
    file_info_tag_names,
)


class FileTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.tagger.acoustidmanager = MagicMock()
        self.file = File('somepath/somefile.mp3')
        self.set_config_values(
            {
                'save_acoustid_fingerprints': True,
            }
        )

    def test_filename(self):
        self.assertEqual('somepath/somefile.mp3', self.file.filename)
        self.assertEqual('somefile.mp3', self.file.base_filename)

    def test_tracknumber(self):
        self.assertEqual(0, self.file.tracknumber)
        self.file.metadata['tracknumber'] = '42'
        self.assertEqual(42, self.file.tracknumber)
        self.file.metadata['tracknumber'] = 'FOURTYTWO'
        self.assertEqual(0, self.file.tracknumber)
        self.file.metadata['tracknumber'] = '3/12'
        self.assertEqual(3, self.file.tracknumber)
        self.file.metadata['tracknumber'] = '3 / 12'
        self.assertEqual(3, self.file.tracknumber)

    def test_discnumber(self):
        self.assertEqual(0, self.file.discnumber)
        self.file.metadata['discnumber'] = '42'
        self.assertEqual(42, self.file.discnumber)
        self.file.metadata['discnumber'] = 'FOURTYTWO'
        self.assertEqual(0, self.file.discnumber)
        self.file.metadata["discnumber"] = '3/12'
        self.assertEqual(3, self.file.discnumber)
        self.file.metadata["discnumber"] = '3 / 12'
        self.assertEqual(3, self.file.discnumber)

    def test_set_acoustid_fingerprint(self):
        fingerprint = 'foo'
        length = 36
        self.file.set_acoustid_fingerprint(fingerprint, length)
        self.assertEqual(fingerprint, self.file.acoustid_fingerprint)
        self.assertEqual(length, self.file.acoustid_length)
        self.tagger.acoustidmanager.add.assert_called_with(self.file, None)
        self.tagger.acoustidmanager.add.reset_mock()
        self.file.set_acoustid_fingerprint(fingerprint, length)
        self.tagger.acoustidmanager.add.assert_not_called()
        self.tagger.acoustidmanager.remove.assert_not_called()
        self.assertEqual(fingerprint, self.file.metadata['acoustid_fingerprint'])

    def test_set_acoustid_fingerprint_no_length(self):
        self.file.metadata.length = 42000
        fingerprint = 'foo'
        self.file.set_acoustid_fingerprint(fingerprint)
        self.assertEqual(fingerprint, self.file.acoustid_fingerprint)
        self.assertEqual(42, self.file.acoustid_length)
        self.assertEqual(fingerprint, self.file.metadata['acoustid_fingerprint'])

    def test_set_acoustid_fingerprint_unset(self):
        self.file.acoustid_fingerprint = 'foo'
        self.file.set_acoustid_fingerprint(None, 42)
        self.tagger.acoustidmanager.add.assert_not_called()
        self.tagger.acoustidmanager.remove.assert_called_with(self.file)
        self.assertEqual(None, self.file.acoustid_fingerprint)
        self.assertEqual(0, self.file.acoustid_length)
        self.assertEqual('', self.file.metadata['acoustid_fingerprint'])

    def format_specific_metadata(self):
        values = ['foo', 'bar']
        self.file.metadata['test'] = values
        self.assertEqual(values, self.file.format_specific_metadata(self.file.metadata, 'test'))

    def test_set_acoustid_fingerprint_no_save(self):
        self.set_config_values(
            {
                'save_acoustid_fingerprints': False,
            }
        )
        fingerprint = 'foo'
        length = 36
        self.file.set_acoustid_fingerprint(fingerprint, length)
        self.assertEqual(fingerprint, self.file.acoustid_fingerprint)
        self.assertEqual(length, self.file.acoustid_length)
        self.assertEqual('', self.file.metadata['acoustid_fingerprint'])

    def test_column(self):
        self.file.metadata['test'] = 'foo'
        self.assertEqual(self.file.column('test'), 'foo')
        self.assertEqual(self.file.column('unknown'), '')

    def test_column_orig_metadata_fallback(self):
        self.set_config_values({'clear_existing_tags': False})
        self.file.orig_metadata['test'] = 'foo'
        self.assertEqual(self.file.column('test'), 'foo')
        self.set_config_values({'clear_existing_tags': True})
        self.assertEqual(self.file.column('test'), '')
        self.file.metadata['test'] = 'bar'
        self.assertEqual(self.file.column('test'), 'bar')

    def test_column_title(self):
        self.assertEqual(self.file.column('title'), self.file.base_filename)
        self.file.metadata['title'] = 'foo'
        self.assertEqual(self.file.column('title'), 'foo')

    def test_column_filesize(self):
        self.assertEqual(self.file.column('~filesize'), '')
        self.file.orig_metadata['~filesize'] = 'notanumber'
        self.assertEqual(self.file.column('~filesize'), 'notanumber')
        self.file.orig_metadata['~filesize'] = '2048'
        self.assertEqual(self.file.column('~filesize'), '2 KiB')
        self.file.metadata['~filesize'] = '4096'
        self.assertEqual(self.file.column('~filesize'), '2 KiB')

    def test_column_bitrate(self):
        self.assertEqual(self.file.column('~bitrate'), '')
        self.file.orig_metadata['~bitrate'] = '320'
        self.assertEqual(self.file.column('~bitrate'), '320 kbps')
        self.file.orig_metadata['~bitrate'] = 'notanumber'
        self.assertEqual(self.file.column('~bitrate'), 'notanumber')

    def test_column_coverart(self):
        image = Mock()
        image.dimensions_as_string.return_value = '100x100'
        self.file.metadata.images.append(image)
        self.assertEqual(self.file.column('covercount'), '1')
        self.assertEqual(self.file.column('coverdimensions'), '100x100')

    def test_info(self):
        class MockInfo:
            length = 4.2
            bitrate = 2000
            sample_rate = 44100
            channels = 2
            bits_per_sample = 160

        metadata = Metadata(length=100)
        mock_file_type = Mock()
        mock_file_type.info = MockInfo()
        self.file._info(metadata, mock_file_type)
        self.assertEqual(4200, metadata.length)
        self.assertEqual('2.0', metadata['~bitrate'])
        self.assertEqual('44100', metadata['~sample_rate'])
        self.assertEqual('2', metadata['~channels'])
        self.assertEqual('160', metadata['~bits_per_sample'])
        self.assertEqual('', metadata['~format'])
        self.assertEqual('somepath/somefile.mp3', metadata['~filepath'])
        self.assertEqual('somepath', metadata['~dirname'])
        self.assertEqual('somefile', metadata['~filename'])
        self.assertEqual('mp3', metadata['~extension'])

    def test_info_name(self):
        class MockInfo:
            pass

        metadata = Metadata()
        mock_file_type = Mock()
        mock_file_type.info = MockInfo()
        self.file.NAME = 'Foo'
        self.file._info(metadata, mock_file_type)
        self.assertEqual('Foo', metadata['~format'])

    def test_info_name_from_class(self):
        class FooFile(File):
            pass

        class MockInfo:
            pass

        metadata = Metadata()
        mock_file_type = Mock()
        mock_file_type.info = MockInfo()
        file_ = FooFile('')
        file_._info(metadata, mock_file_type)
        self.assertEqual('Foo', metadata['~format'])

    def test_info_no_length(self):
        class MockInfo:
            pass

        metadata = Metadata(length=100)
        mock_file_type = Mock()
        mock_file_type.info = MockInfo()
        self.file._info(metadata, mock_file_type)
        self.assertEqual(100, metadata.length)
        mock_file_type.info.length = None
        self.file._info(metadata, mock_file_type)
        self.assertEqual(100, metadata.length)

    def test_info_zero_length(self):
        class MockInfo:
            length = 0

        metadata = Metadata(length=100)
        mock_file_type = Mock()
        mock_file_type.info = MockInfo()
        self.file._info(metadata, mock_file_type)
        self.assertEqual(0, metadata.length)


class TestPreserveTimes(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.tmp_directory = self.mktmpdir()
        filepath = os.path.join(self.tmp_directory, 'a.mp3')
        self.file = File(filepath)

    def _create_testfile(self):
        # create a dummy file
        with open(self.file.filename, 'w') as f:
            f.write('xxx')
            f.flush()
            os.fsync(f.fileno())

    def _modify_testfile(self):
        # dummy file modification, append data to it
        with open(self.file.filename, 'a') as f:
            f.write('yyy')
            f.flush()
            os.fsync(f.fileno())

    def _read_testfile(self):
        with open(self.file.filename, 'r') as f:
            return f.read()

    def test_preserve_times(self):
        self._create_testfile()

        # test if times are preserved
        (before_atime_ns, before_mtime_ns) = self.file._preserve_times(self.file.filename, self._modify_testfile)

        # HERE an external access to the file is possible, modifying its access time

        # read times again and compare with original
        st = os.stat(self.file.filename)
        (after_atime_ns, after_mtime_ns) = (st.st_atime_ns, st.st_mtime_ns)

        # on macOS 10.14 and later os.utime only sets the times with second
        # precision see https://tickets.metabrainz.org/browse/PICARD-1516.
        # This also seems to depend on the Python build being used.
        if IS_MACOS:
            before_atime_ns //= 1000
            before_mtime_ns //= 1000
            after_atime_ns //= 1000
            after_mtime_ns //= 1000

        # modification times should be equal
        self.assertEqual(before_mtime_ns, after_mtime_ns)

        # access times may not be equal
        # time difference should be positive and reasonably low (if no access in between, it should be 0)
        delta = after_atime_ns - before_atime_ns
        tolerance = 10**7  # 0.01 seconds
        self.assertTrue(0 <= delta < tolerance, "0 <= %s < %s" % (delta, tolerance))

        # ensure written data can be read back
        # keep it at the end, we don't want to access file before time checks
        self.assertEqual(self._read_testfile(), 'xxxyyy')

    def test_preserve_times_nofile(self):
        with self.assertRaises(self.file.PreserveTimesStatError):
            self.file._preserve_times(self.file.filename, self._modify_testfile)
        with self.assertRaises(FileNotFoundError):
            self._read_testfile()

    def test_preserve_times_nofile_utime(self):
        self._create_testfile()

        def save():
            os.remove(self.file.filename)

        with self.assertRaises(self.file.PreserveTimesUtimeError):
            self.file._preserve_times(self.file.filename, save)


class FakeMp3File(File):
    EXTENSIONS = ['.mp3']


class FileNamingTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.file = File('/somepath/somefile.mp3')
        self.set_config_values(
            {
                'ascii_filenames': False,
                'clear_existing_tags': False,
                'enabled_plugins': [],
                'move_files_to': '/media/music',
                'move_files': False,
                'rename_files': False,
                'windows_compatibility': True,
                'win_compat_replacements': {},
                'windows_long_paths': False,
                'replace_spaces_with_underscores': False,
                'replace_dir_separator': '_',
                'file_renaming_scripts': {'test_id': {'script': '%album%/%title%'}},
                'active_file_naming_script_id': 'test_id',
            }
        )
        self.metadata = Metadata(
            {
                'album': 'somealbum',
                'title': 'sometitle',
            }
        )

    def test_make_filename_no_move_and_rename(self):
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.normpath(self.file.filename), filename)

    def test_make_filename_rename_only(self):
        config.setting['rename_files'] = True
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.normpath('/somepath/sometitle.mp3'), filename)

    def test_make_filename_move_only(self):
        config.setting['move_files'] = True
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.normpath('/media/music/somealbum/somefile.mp3'), filename)

    def test_make_filename_move_and_rename(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.normpath('/media/music/somealbum/sometitle.mp3'), filename)

    def test_make_filename_move_relative_path(self):
        config.setting['move_files'] = True
        config.setting['move_files_to'] = 'subdir'
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.normpath('/somepath/subdir/somealbum/somefile.mp3'), filename)

    def test_make_filename_empty_script(self):
        config.setting['rename_files'] = True
        config.setting['file_renaming_scripts'] = {'test_id': {'script': '$noop()'}}
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.normpath('/somepath/somefile.mp3'), filename)

    def test_make_filename_empty_basename(self):
        config.setting['move_files'] = True
        config.setting['rename_files'] = True
        config.setting['file_renaming_scripts'] = {'test_id': {'script': '/somedir/$noop()'}}
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.normpath('/media/music/somedir/somefile.mp3'), filename)

    def test_make_filename_no_extension(self):
        config.setting['rename_files'] = True
        file_ = FakeMp3File('/somepath/_')
        filename = file_.make_filename(file_.filename, self.metadata)
        self.assertEqual(os.path.normpath('/somepath/sometitle.mp3'), filename)

    def test_make_filename_lowercase_extension(self):
        config.setting['rename_files'] = True
        file_ = FakeMp3File('/somepath/somefile.MP3')
        filename = file_.make_filename(file_.filename, self.metadata)
        self.assertEqual(os.path.normpath('/somepath/sometitle.mp3'), filename)

    def test_make_filename_scripted_extension(self):
        config.setting['rename_files'] = True
        config.setting['file_renaming_scripts'] = {'test_id': {'script': '$set(_extension,.foo)%title%'}}
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.normpath('/somepath/sometitle.foo'), filename)

    def test_make_filename_replace_trailing_dots(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        config.setting['windows_compatibility'] = True
        metadata = Metadata(
            {
                'album': 'somealbum.',
                'title': 'sometitle',
            }
        )
        filename = self.file.make_filename(self.file.filename, metadata)
        self.assertEqual(os.path.normpath('/media/music/somealbum_/sometitle.mp3'), filename)

    @unittest.skipUnless(not IS_WIN, "non-windows test")
    def test_make_filename_keep_trailing_dots(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        config.setting['windows_compatibility'] = False
        metadata = Metadata(
            {
                'album': 'somealbum.',
                'title': 'sometitle',
            }
        )
        filename = self.file.make_filename(self.file.filename, metadata)
        self.assertEqual(os.path.normpath('/media/music/somealbum./sometitle.mp3'), filename)

    def test_make_filename_replace_leading_dots(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        config.setting['windows_compatibility'] = True
        metadata = Metadata(
            {
                'album': '.somealbum',
                'title': '.sometitle',
            }
        )
        filename = self.file.make_filename(self.file.filename, metadata)
        self.assertEqual(os.path.normpath('/media/music/_somealbum/_sometitle.mp3'), filename)


class FileGuessTracknumberAndTitleTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.set_config_values(
            {
                'guess_tracknumber_and_title': True,
            }
        )

    def test_no_guess(self):
        f = File('/somepath/01 somefile.mp3')
        metadata = Metadata(
            {
                'album': 'somealbum',
                'title': 'sometitle',
                'tracknumber': '2',
            }
        )
        f._guess_tracknumber_and_title(metadata)
        self.assertEqual(metadata['tracknumber'], '2')
        self.assertEqual(metadata['title'], 'sometitle')

    def test_guess_title(self):
        f = File('/somepath/01 somefile.mp3')
        metadata = Metadata(
            {
                'album': 'somealbum',
                'tracknumber': '2',
            }
        )
        f._guess_tracknumber_and_title(metadata)
        self.assertEqual(metadata['tracknumber'], '2')
        self.assertEqual(metadata['title'], 'somefile')

    def test_guess_tracknumber(self):
        f = File('/somepath/01 somefile.mp3')
        metadata = Metadata(
            {
                'album': 'somealbum',
                'title': 'sometitle',
            }
        )
        f._guess_tracknumber_and_title(metadata)
        self.assertEqual(metadata['tracknumber'], '1')

    def test_guess_title_tracknumber(self):
        f = File('/somepath/01 somefile.mp3')
        metadata = Metadata(
            {
                'album': 'somealbum',
            }
        )
        f._guess_tracknumber_and_title(metadata)
        self.assertEqual(metadata['tracknumber'], '1')
        self.assertEqual(metadata['title'], 'somefile')


class FileAdditionalFilesPatternsTest(PicardTestCase):
    def test_empty_patterns(self):
        self.assertEqual(File._compile_move_additional_files_pattern('   '), set())

    def test_simple_patterns(self):
        pattern = 'cover.jpg'
        expected = {(re.compile(r'(?s:cover\.jpg)\Z', re.IGNORECASE), False)}
        self._assert_patterns_match(pattern, expected)

    def test_whitespaces_patterns(self):
        pattern = "  a   \n b   "
        expected = {
            (re.compile(r'(?s:a)\Z', re.IGNORECASE), False),
            (re.compile(r'(?s:b)\Z', re.IGNORECASE), False),
        }
        self._assert_patterns_match(pattern, expected)

    def test_duplicated_patterns(self):
        pattern = 'cover.jpg cover.jpg COVER.JPG'
        expected = {(re.compile(r'(?s:cover\.jpg)\Z', re.IGNORECASE), False)}
        self._assert_patterns_match(pattern, expected)

    def test_simple_hidden_patterns(self):
        pattern = 'cover.jpg .hidden'
        expected = {
            (re.compile(r'(?s:cover\.jpg)\Z', re.IGNORECASE), False),
            (re.compile(r'(?s:\.hidden)\Z', re.IGNORECASE), True),
        }
        self._assert_patterns_match(pattern, expected)

    def test_wildcard_patterns(self):
        pattern = 'c?ver.jpg .h?dden* *.jpg *.JPG'
        expected = {
            (re.compile(r'(?s:c.ver\.jpg)\Z', re.IGNORECASE), False),
            (re.compile(r'(?s:\.h.dden.*)\Z', re.IGNORECASE), True),
            (re.compile(r'(?s:.*\.jpg)\Z', re.IGNORECASE), False),
        }
        self._assert_patterns_match(pattern, expected)

    def _assert_patterns_match(self, pattern, expected):
        compiled = File._compile_move_additional_files_pattern(pattern)
        # With Python 3.14 the \Z regex flag was renamed to \z. Convert the old
        # naming when comparing the patterns.
        expected = {(p.pattern, h) for p, h in expected}
        compiled = {(p.pattern.replace(r'\z', r'\Z'), h) for p, h in compiled}
        self.assertEqual(compiled, expected)


class FileUpdateTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.file = File('/somepath/somefile.mp3')
        self.INVALIDSIMVAL = 666
        self.file.similarity = self.INVALIDSIMVAL  # to check if changed or not
        self.file.supports_tag = lambda x: False if x.startswith('unsupported') else True
        self.set_config_values(
            {
                'clear_existing_tags': False,
                'compare_ignore_tags': [],
                'enabled_plugins': [],
            }
        )

    def test_same_image(self):
        image = create_image(b'a')
        self.file.metadata.images = [image]
        self.file.orig_metadata.images = [image]
        self.file.state = File.State.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)  # it should be modified
        self.assertEqual(self.file.state, File.State.NORMAL)

    def test_same_image_pending(self):
        image = create_image(b'a')
        self.file.metadata.images = [image]
        self.file.orig_metadata.images = [image]

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.State.PENDING)

    def test_same_image_changed_state(self):
        image = create_image(b'a')
        self.file.metadata.images = [image]
        self.file.orig_metadata.images = [image]
        self.file.state = File.State.CHANGED

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.State.NORMAL)

    def test_changed_image(self):
        old_image = create_image(b'a')
        new_image = create_image(b'b')
        self.file.metadata.images = [new_image]
        self.file.orig_metadata.images = [old_image]
        self.file.state = File.State.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.State.CHANGED)

    def test_signal(self):
        #  just for coverage
        self.file.update(signal=True)
        self.assertEqual(self.file.metadata, Metadata())
        self.assertEqual(self.file.orig_metadata, Metadata())

    def test_tags_to_update(self):
        self.file.orig_metadata = Metadata(
            {
                'album': 'somealbum',
                'title': 'sometitle',
                'ignoreme_old': 'a',
                '~ignoreme_old': 'b',
                'unsupported_old': 'c',
            }
        )
        self.file.metadata = Metadata(
            {
                'artist': 'someartist',
                'ignoreme_new': 'd',
                '~ignoreme_new': 'e',
                'unsupported_new': 'f',
            }
        )

        ignore_tags = {'ignoreme_old', 'ignoreme_new'}

        expected = {'album', 'title', 'artist'}
        result = self.file._tags_to_update(ignore_tags)
        self.assertIsInstance(result, GeneratorType)
        self.assertEqual(set(result), expected)

    def test_unchanged_metadata(self):
        self.file.orig_metadata = Metadata(
            {
                'album': 'somealbum',
                'title': 'sometitle',
            }
        )
        self.file.metadata = Metadata(
            {
                'album': 'somealbum',
                'title': 'sometitle',
            }
        )
        self.file.state = File.State.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.State.NORMAL)

    def test_changed_metadata(self):
        self.file.orig_metadata = Metadata(
            {
                'album': 'somealbum',
                'title': 'sometitle',
            }
        )
        self.file.metadata = Metadata(
            {
                'album': 'somealbum2',
                'title': 'sometitle2',
            }
        )
        self.file.state = File.State.NORMAL

        self.file.update(signal=False)
        self.assertLess(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.State.CHANGED)

    def test_changed_metadata_pending(self):
        self.file.orig_metadata = Metadata(
            {
                'album': 'somealbum',
                'title': 'sometitle',
            }
        )
        self.file.metadata = Metadata(
            {
                'album': 'somealbum2',
                'title': 'sometitle2',
            }
        )

        self.file.update(signal=False)
        self.assertLess(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.State.PENDING)  # it shouldn't be modified

    def test_clear_existing(self):
        self.file.orig_metadata = Metadata(
            {
                'album': 'somealbum',
                'title': 'sometitle',
            }
        )
        self.file.metadata = Metadata()
        self.file.state = File.State.NORMAL

        config.setting["clear_existing_tags"] = True

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 0.0)
        self.assertEqual(self.file.state, File.State.CHANGED)

    def test_no_new_metadata(self):
        self.file.orig_metadata = Metadata(
            {
                'album': 'somealbum',
                'title': 'sometitle',
            }
        )
        self.file.metadata = Metadata()
        self.file.state = File.State.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.State.NORMAL)

    def test_tilde_tag(self):
        self.file.orig_metadata = Metadata()
        self.file.metadata = Metadata({'~tag': 'value'})
        self.file.state = File.State.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.State.NORMAL)

    def test_ignored_tag(self):
        self.file.orig_metadata = Metadata()
        self.file.metadata = Metadata({'tag': 'value'})
        self.file.state = File.State.NORMAL

        config.setting["compare_ignore_tags"] = ['tag']

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.State.NORMAL)

    def test_unsupported_tag(self):
        self.file.orig_metadata = Metadata()
        self.file.metadata = Metadata({'unsupported': 'value'})
        self.file.state = File.State.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.State.NORMAL)

    def test_copy_file_info_tags(self):
        info_tags = {}
        for info in file_info_tag_names():
            info_tags[info] = 'val' + info

        orig_metadata = Metadata(info_tags)
        orig_metadata['a'] = 'vala'
        metadata = Metadata(
            {
                '~bitrate': 'xxx',
                'b': 'valb',
            }
        )
        self.file._copy_file_info_tags(metadata, orig_metadata)
        for info in file_info_tag_names():
            self.assertEqual('val' + info, metadata[info])
        self.assertEqual('valb', metadata['b'])
        self.assertNotIn('a', metadata)


class FileCopyMetadataTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        metadata = Metadata(
            {
                'album': 'somealbum',
                'artist': 'someartist',
                'title': 'sometitle',
            }
        )
        del metadata['deletedtag']
        metadata.images.append(create_image(b'a'))
        self.file = File('/somepath/somefile.mp3')
        self.file.metadata = metadata
        self.file.orig_metadata = Metadata(
            {
                'album': 'origalbum',
                'artist': 'origartist',
                'title': 'origtitle',
            }
        )
        self.INVALIDSIMVAL = 666
        self.set_config_values(
            {
                'preserved_tags': [],
            }
        )

    def test_copy_metadata_full(self):
        new_metadata = Metadata(
            {
                'title': 'othertitle',
                '~foo': 'bar',
            }
        )
        del new_metadata['foo']
        new_metadata.images.append(create_image(b'b'))
        self.file.copy_metadata(new_metadata, preserve_deleted=False)
        self.assertEqual(self.file.metadata, new_metadata)
        self.assertEqual(self.file.metadata.images, new_metadata.images)
        self.assertEqual(self.file.metadata.deleted_tags, new_metadata.deleted_tags)

    def test_copy_metadata_must_preserve_deleted_tags_by_default(self):
        new_metadata = Metadata(
            {
                'title': 'othertitle',
                '~foo': 'bar',
            }
        )
        del new_metadata['foo']
        self.file.copy_metadata(new_metadata)
        self.assertEqual(self.file.metadata, new_metadata)
        self.assertEqual(self.file.metadata.deleted_tags, {'deletedtag', 'foo'})

    def test_copy_metadata_do_not_preserve_deleted_tags(self):
        new_metadata = Metadata(
            {
                'title': 'othertitle',
                '~foo': 'bar',
            }
        )
        del new_metadata['foo']
        self.file.copy_metadata(new_metadata, preserve_deleted=False)
        self.assertEqual(self.file.metadata, new_metadata)
        self.assertEqual(self.file.metadata.deleted_tags, {'foo'})

    def test_copy_metadata_must_keep_file_content_specific_tags(self):
        for tag in calculated_tag_names():
            self.file.metadata[tag] = 'foo'
        new_metadata = Metadata()
        self.file.copy_metadata(new_metadata)
        for tag in calculated_tag_names():
            self.assertEqual(self.file.metadata[tag], 'foo', f'Tag {tag}: {self.file.metadata[tag]!r} != "foo"')

    def test_copy_metadata_must_remove_deleted_acoustid_id(self):
        self.file.metadata['acoustid_id'] = 'foo'
        new_metadata = Metadata()
        new_metadata.delete('acoustid_id')
        self.file.copy_metadata(new_metadata)
        self.assertEqual(self.file.metadata['acoustid_id'], '')
        self.assertIn('acoustid_id', self.file.metadata.deleted_tags)

    def test_copy_metadata_with_preserved_tags(self):
        self.set_config_values(
            {
                'preserved_tags': ['artist', 'title'],
            }
        )
        new_metadata = Metadata(
            {
                'album': 'otheralbum',
                'artist': 'otherartist',
                'title': 'othertitle',
            }
        )
        self.file.copy_metadata(new_metadata)
        self.assertEqual(self.file.metadata['album'], 'otheralbum')
        self.assertEqual(self.file.metadata['artist'], 'origartist')
        self.assertEqual(self.file.metadata['title'], 'origtitle')

    def test_copy_metadata_must_always_preserve_technical_variables(self):
        self.file.orig_metadata['~filename'] = 'orig.flac'
        new_metadata = Metadata(
            {
                '~filename': 'new.flac',
            }
        )
        self.file.copy_metadata(new_metadata)
        self.assertEqual(self.file.metadata['~filename'], 'orig.flac')

    def test_score_with_mutagen_file(self):
        mock_mutagen_file = Mock()
        mock_mutagen_file.score.return_value = 3

        class MyFormat(File):
            _File = mock_mutagen_file

        score = MyFormat.score('/somepath/somefile.mp3', Mock(), b"abc")
        self.assertEqual(score, 3)

    def test_score_match_extension(self):
        mock_mutagen_file = Mock()
        mock_mutagen_file.score.return_value = 3

        class MyFormat(File):
            EXTENSIONS = ['.mp3']

        score = MyFormat.score('/somepath/somefile.mp3', Mock(), b"abc")
        self.assertEqual(score, 1)

        score = MyFormat.score('/somepath/somefile.MP3', Mock(), b"abc")
        self.assertEqual(score, 1)

        score = MyFormat.score('/somepath/somefile.ogg', Mock(), b"abc")
        self.assertEqual(score, 0)


class RetryOnPermissionErrorTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.file = File('somepath/somefile.mp3')

    @patch('picard.file.IS_WIN', False)
    def test_no_retry_on_non_windows(self):
        """On non-Windows, PermissionError propagates immediately."""
        func = Mock(side_effect=PermissionError("locked"))
        with self.assertRaises(PermissionError):
            self.file._retry_on_permission_error(func)
        func.assert_called_once()

    @patch('picard.file.IS_WIN', True)
    @patch('picard.file.time.sleep')
    def test_succeeds_first_try(self, mock_sleep):
        func = Mock(return_value='result')
        result = self.file._retry_on_permission_error(func)
        self.assertEqual('result', result)
        func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('picard.file.IS_WIN', True)
    @patch('picard.file.time.sleep')
    def test_succeeds_after_retry(self, mock_sleep):
        """Succeeds on second attempt after one PermissionError."""
        func = Mock(side_effect=[PermissionError("locked"), 'result'])
        result = self.file._retry_on_permission_error(func)
        self.assertEqual('result', result)
        self.assertEqual(2, func.call_count)
        mock_sleep.assert_called_once_with(self.file._PERMISSION_ERROR_RETRY_DELAY)

    @patch('picard.file.IS_WIN', True)
    @patch('picard.file.time.sleep')
    def test_raises_after_max_retries(self, mock_sleep):
        """Raises PermissionError after exhausting all retries."""
        func = Mock(side_effect=PermissionError("locked"))
        with self.assertRaises(PermissionError):
            self.file._retry_on_permission_error(func)
        self.assertEqual(self.file._PERMISSION_ERROR_RETRIES, func.call_count)
        self.assertEqual(self.file._PERMISSION_ERROR_RETRIES - 1, mock_sleep.call_count)

    @patch('picard.file.IS_WIN', True)
    @patch('picard.file.time.sleep')
    def test_non_permission_error_not_retried(self, mock_sleep):
        """Other exceptions propagate immediately without retry."""
        func = Mock(side_effect=OSError("other error"))
        with self.assertRaises(OSError):
            self.file._retry_on_permission_error(func)
        func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('picard.file.IS_WIN', True)
    @patch('picard.file.time.sleep')
    @patch('picard.file.move_ensure_casing')
    def test_move_with_retry_cleans_partial_copy(self, mock_move, mock_sleep):
        """On failed cross-drive move, partial copy at destination is removed before retry."""
        # First call: simulate cross-drive failure (copy exists at dest, source still there)
        # Second call: succeeds
        mock_move.side_effect = [PermissionError("locked"), None]
        with (
            patch('os.path.exists', return_value=True),
            patch('picard.file.samefile', return_value=False),
            patch('os.remove') as mock_remove,
        ):
            self.file._move_with_retry('/src/file.mp3', '/dst/file.mp3')
        mock_remove.assert_called_once_with('/dst/file.mp3')
        self.assertEqual(2, mock_move.call_count)

    @patch('picard.file.IS_WIN', True)
    @patch('picard.file.time.sleep')
    @patch('picard.file.move_ensure_casing')
    def test_move_with_retry_no_cleanup_if_no_partial_copy(self, mock_move, mock_sleep):
        """No cleanup if destination doesn't exist (same-drive move failure)."""
        mock_move.side_effect = [PermissionError("locked"), None]
        with patch('os.path.exists', return_value=False), patch('os.remove') as mock_remove:
            self.file._move_with_retry('/src/file.mp3', '/dst/file.mp3')
        mock_remove.assert_not_called()

    @patch('picard.file.IS_WIN', True)
    @patch('picard.file.time.sleep')
    @patch('picard.file.move_ensure_casing')
    def test_move_with_retry_no_cleanup_if_samefile(self, mock_move, mock_sleep):
        """No cleanup if source and destination resolve to the same file."""
        mock_move.side_effect = [PermissionError("locked"), None]
        with (
            patch('os.path.exists', return_value=True),
            patch('picard.file.samefile', return_value=True),
            patch('os.remove') as mock_remove,
        ):
            self.file._move_with_retry('/src/file.mp3', '/dst/file.mp3')
        mock_remove.assert_not_called()
