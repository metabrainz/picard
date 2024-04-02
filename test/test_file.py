# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018-2022 Philipp Wolfer
# Copyright (C) 2019-2022 Laurent Monin
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
from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase
from test.test_coverart_image import create_image

from picard import config
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.file import File
from picard.metadata import Metadata
from picard.util.tags import (
    CALCULATED_TAGS,
    FILE_INFO_TAGS,
)


class DataObjectTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.tagger.acoustidmanager = MagicMock()
        self.file = File('somepath/somefile.mp3')
        self.set_config_values({
            'save_acoustid_fingerprints': True,
        })

    def test_filename(self):
        self.assertEqual('somepath/somefile.mp3', self.file.filename)
        self.assertEqual('somefile.mp3', self.file.base_filename)

    def test_tracknumber(self):
        self.assertEqual(0, self.file.tracknumber)
        self.file.metadata['tracknumber'] = '42'
        self.assertEqual(42, self.file.tracknumber)
        self.file.metadata['tracknumber'] = 'FOURTYTWO'
        self.assertEqual(0, self.file.tracknumber)

    def test_discnumber(self):
        self.assertEqual(0, self.file.discnumber)
        self.file.metadata['discnumber'] = '42'
        self.assertEqual(42, self.file.discnumber)
        self.file.metadata['discnumber'] = 'FOURTYTWO'
        self.assertEqual(0, self.file.discnumber)

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
        self.set_config_values({
            'save_acoustid_fingerprints': False,
        })
        fingerprint = 'foo'
        length = 36
        self.file.set_acoustid_fingerprint(fingerprint, length)
        self.assertEqual(fingerprint, self.file.acoustid_fingerprint)
        self.assertEqual(length, self.file.acoustid_length)
        self.assertEqual('', self.file.metadata['acoustid_fingerprint'])


class TestPreserveTimes(PicardTestCase):

    def setUp(self):
        super().setUp()
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
            self.file._preserve_times(self.file.filename,
                                      self._modify_testfile)
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
        self.file = File('/somepath/somefile.mp3')
        self.set_config_values({
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
            'selected_file_naming_script_id': 'test_id',
        })
        self.metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
        })

    def test_make_filename_no_move_and_rename(self):
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.realpath(self.file.filename), filename)

    def test_make_filename_rename_only(self):
        config.setting['rename_files'] = True
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.realpath('/somepath/sometitle.mp3'), filename)

    def test_make_filename_move_only(self):
        config.setting['move_files'] = True
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(
            os.path.realpath('/media/music/somealbum/somefile.mp3'),
            filename)

    def test_make_filename_move_and_rename(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(
            os.path.realpath('/media/music/somealbum/sometitle.mp3'),
            filename)

    def test_make_filename_move_relative_path(self):
        config.setting['move_files'] = True
        config.setting['move_files_to'] = 'subdir'
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(
            os.path.realpath('/somepath/subdir/somealbum/somefile.mp3'),
            filename)

    def test_make_filename_empty_script(self):
        config.setting['rename_files'] = True
        config.setting['file_renaming_scripts'] = {'test_id': {'script': '$noop()'}}
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.realpath('/somepath/somefile.mp3'), filename)

    def test_make_filename_empty_basename(self):
        config.setting['move_files'] = True
        config.setting['rename_files'] = True
        config.setting['file_renaming_scripts'] = {'test_id': {'script': '/somedir/$noop()'}}
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.realpath('/media/music/somedir/somefile.mp3'), filename)

    def test_make_filename_no_extension(self):
        config.setting['rename_files'] = True
        file_ = FakeMp3File('/somepath/_')
        filename = file_.make_filename(file_.filename, self.metadata)
        self.assertEqual(os.path.realpath('/somepath/sometitle.mp3'), filename)

    def test_make_filename_lowercase_extension(self):
        config.setting['rename_files'] = True
        file_ = FakeMp3File('/somepath/somefile.MP3')
        filename = file_.make_filename(file_.filename, self.metadata)
        self.assertEqual(os.path.realpath('/somepath/sometitle.mp3'), filename)

    def test_make_filename_scripted_extension(self):
        config.setting['rename_files'] = True
        config.setting['file_renaming_scripts'] = {'test_id': {'script': '$set(_extension,.foo)%title%'}}
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.realpath('/somepath/sometitle.foo'), filename)

    def test_make_filename_replace_trailing_dots(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        config.setting['windows_compatibility'] = True
        metadata = Metadata({
            'album': 'somealbum.',
            'title': 'sometitle',
        })
        filename = self.file.make_filename(self.file.filename, metadata)
        self.assertEqual(
            os.path.realpath('/media/music/somealbum_/sometitle.mp3'),
            filename)

    @unittest.skipUnless(not IS_WIN, "non-windows test")
    def test_make_filename_keep_trailing_dots(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        config.setting['windows_compatibility'] = False
        metadata = Metadata({
            'album': 'somealbum.',
            'title': 'sometitle',
        })
        filename = self.file.make_filename(self.file.filename, metadata)
        self.assertEqual(
            os.path.realpath('/media/music/somealbum./sometitle.mp3'),
            filename)

    def test_make_filename_replace_leading_dots(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        config.setting['windows_compatibility'] = True
        metadata = Metadata({
            'album': '.somealbum',
            'title': '.sometitle',
        })
        filename = self.file.make_filename(self.file.filename, metadata)
        self.assertEqual(
            os.path.realpath('/media/music/_somealbum/_sometitle.mp3'),
            filename)


class FileGuessTracknumberAndTitleTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values({
            'guess_tracknumber_and_title': True,
        })

    def test_no_guess(self):
        f = File('/somepath/01 somefile.mp3')
        metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
            'tracknumber': '2',
        })
        f._guess_tracknumber_and_title(metadata)
        self.assertEqual(metadata['tracknumber'], '2')
        self.assertEqual(metadata['title'], 'sometitle')

    def test_guess_title(self):
        f = File('/somepath/01 somefile.mp3')
        metadata = Metadata({
            'album': 'somealbum',
            'tracknumber': '2',
        })
        f._guess_tracknumber_and_title(metadata)
        self.assertEqual(metadata['tracknumber'], '2')
        self.assertEqual(metadata['title'], 'somefile')

    def test_guess_tracknumber(self):
        f = File('/somepath/01 somefile.mp3')
        metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
        })
        f._guess_tracknumber_and_title(metadata)
        self.assertEqual(metadata['tracknumber'], '1')

    def test_guess_title_tracknumber(self):
        f = File('/somepath/01 somefile.mp3')
        metadata = Metadata({
            'album': 'somealbum',
        })
        f._guess_tracknumber_and_title(metadata)
        self.assertEqual(metadata['tracknumber'], '1')
        self.assertEqual(metadata['title'], 'somefile')


class FileAdditionalFilesPatternsTest(PicardTestCase):

    def test_empty_patterns(self):
        self.assertEqual(File._compile_move_additional_files_pattern('   '), set())

    def test_simple_patterns(self):
        pattern = 'cover.jpg'
        expected = {
            (re.compile('(?s:cover\\.jpg)\\Z', re.IGNORECASE), False)
        }
        self.assertEqual(File._compile_move_additional_files_pattern(pattern), expected)

    def test_whitespaces_patterns(self):
        pattern = "  a   \n b   "
        expected = {
            (re.compile('(?s:a)\\Z', re.IGNORECASE), False),
            (re.compile('(?s:b)\\Z', re.IGNORECASE), False),
        }
        self.assertEqual(File._compile_move_additional_files_pattern(pattern), expected)

    def test_duplicated_patterns(self):
        pattern = 'cover.jpg cover.jpg COVER.JPG'
        expected = {
            (re.compile('(?s:cover\\.jpg)\\Z', re.IGNORECASE), False)
        }
        self.assertEqual(File._compile_move_additional_files_pattern(pattern), expected)

    def test_simple_hidden_patterns(self):
        pattern = 'cover.jpg .hidden'
        expected = {
            (re.compile('(?s:cover\\.jpg)\\Z', re.IGNORECASE), False),
            (re.compile('(?s:\\.hidden)\\Z', re.IGNORECASE), True)
        }
        self.assertEqual(File._compile_move_additional_files_pattern(pattern), expected)

    def test_wildcard_patterns(self):
        pattern = 'c?ver.jpg .h?dden* *.jpg *.JPG'
        expected = {
            (re.compile('(?s:c.ver\\.jpg)\\Z', re.IGNORECASE), False),
            (re.compile('(?s:\\.h.dden.*)\\Z', re.IGNORECASE), True),
            (re.compile('(?s:.*\\.jpg)\\Z', re.IGNORECASE), False),
        }
        self.assertEqual(File._compile_move_additional_files_pattern(pattern), expected)


class FileUpdateTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.file = File('/somepath/somefile.mp3')
        self.INVALIDSIMVAL = 666
        self.file.similarity = self.INVALIDSIMVAL  # to check if changed or not
        self.file.supports_tag = lambda x: False if x.startswith('unsupported') else True
        self.set_config_values({
            'clear_existing_tags': False,
            'compare_ignore_tags': [],
            'enabled_plugins': [],
        })

    def test_same_image(self):
        image = create_image(b'a')
        self.file.metadata.images = [image]
        self.file.orig_metadata.images = [image]
        self.file.state = File.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)  # it should be modified
        self.assertEqual(self.file.state, File.NORMAL)

    def test_same_image_pending(self):
        image = create_image(b'a')
        self.file.metadata.images = [image]
        self.file.orig_metadata.images = [image]

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.PENDING)

    def test_same_image_changed_state(self):
        image = create_image(b'a')
        self.file.metadata.images = [image]
        self.file.orig_metadata.images = [image]
        self.file.state = File.CHANGED

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.NORMAL)

    def test_changed_image(self):
        old_image = create_image(b'a')
        new_image = create_image(b'b')
        self.file.metadata.images = [new_image]
        self.file.orig_metadata.images = [old_image]
        self.file.state = File.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.CHANGED)

    def test_signal(self):
        #  just for coverage
        self.file.update(signal=True)
        self.assertEqual(self.file.metadata, Metadata())
        self.assertEqual(self.file.orig_metadata, Metadata())

    def test_tags_to_update(self):
        self.file.orig_metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
            'ignoreme_old': 'a',
            '~ignoreme_old': 'b',
            'unsupported_old': 'c',
        })
        self.file.metadata = Metadata({
            'artist': 'someartist',
            'ignoreme_new': 'd',
            '~ignoreme_new': 'e',
            'unsupported_new': 'f',
        })

        ignore_tags = {'ignoreme_old', 'ignoreme_new'}

        expected = {'album', 'title', 'artist'}
        result = self.file._tags_to_update(ignore_tags)
        self.assertIsInstance(result, GeneratorType)
        self.assertEqual(set(result), expected)

    def test_unchanged_metadata(self):
        self.file.orig_metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
        })
        self.file.metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
        })
        self.file.state = File.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.NORMAL)

    def test_changed_metadata(self):
        self.file.orig_metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
        })
        self.file.metadata = Metadata({
            'album': 'somealbum2',
            'title': 'sometitle2',
        })
        self.file.state = File.NORMAL

        self.file.update(signal=False)
        self.assertLess(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.CHANGED)

    def test_changed_metadata_pending(self):
        self.file.orig_metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
        })
        self.file.metadata = Metadata({
            'album': 'somealbum2',
            'title': 'sometitle2',
        })

        self.file.update(signal=False)
        self.assertLess(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.PENDING)  # it shouldn't be modified

    def test_clear_existing(self):
        self.file.orig_metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
        })
        self.file.metadata = Metadata()
        self.file.state = File.NORMAL

        config.setting["clear_existing_tags"] = True

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 0.0)
        self.assertEqual(self.file.state, File.CHANGED)

    def test_no_new_metadata(self):
        self.file.orig_metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
        })
        self.file.metadata = Metadata()
        self.file.state = File.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.NORMAL)

    def test_tilde_tag(self):
        self.file.orig_metadata = Metadata()
        self.file.metadata = Metadata({
            '~tag': 'value'
        })
        self.file.state = File.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.NORMAL)

    def test_ignored_tag(self):
        self.file.orig_metadata = Metadata()
        self.file.metadata = Metadata({
            'tag': 'value'
        })
        self.file.state = File.NORMAL

        config.setting["compare_ignore_tags"] = ['tag']

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.NORMAL)

    def test_unsupported_tag(self):
        self.file.orig_metadata = Metadata()
        self.file.metadata = Metadata({
            'unsupported': 'value'
        })
        self.file.state = File.NORMAL

        self.file.update(signal=False)
        self.assertEqual(self.file.similarity, 1.0)
        self.assertEqual(self.file.state, File.NORMAL)

    def test_copy_file_info_tags(self):
        info_tags = {}
        for info in FILE_INFO_TAGS:
            info_tags[info] = 'val' + info

        orig_metadata = Metadata(info_tags)
        orig_metadata['a'] = 'vala'
        metadata = Metadata({
            '~bitrate': 'xxx',
            'b': 'valb',
        })
        self.file._copy_file_info_tags(metadata, orig_metadata)
        for info in FILE_INFO_TAGS:
            self.assertEqual('val' + info, metadata[info])
        self.assertEqual('valb', metadata['b'])
        self.assertNotIn('a', metadata)


class FileCopyMetadataTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        metadata = Metadata({
            'album': 'somealbum',
            'artist': 'someartist',
            'title': 'sometitle',
        })
        del metadata['deletedtag']
        metadata.images.append(create_image(b'a'))
        self.file = File('/somepath/somefile.mp3')
        self.file.metadata = metadata
        self.file.orig_metadata = Metadata({
            'album': 'origalbum',
            'artist': 'origartist',
            'title': 'origtitle',
        })
        self.INVALIDSIMVAL = 666
        self.set_config_values({
            'preserved_tags': [],
        })

    def test_copy_metadata_full(self):
        new_metadata = Metadata({
            'title': 'othertitle',
            '~foo': 'bar',
        })
        del new_metadata['foo']
        new_metadata.images.append(create_image(b'b'))
        self.file.copy_metadata(new_metadata, preserve_deleted=False)
        self.assertEqual(self.file.metadata, new_metadata)
        self.assertEqual(self.file.metadata.images, new_metadata.images)
        self.assertEqual(self.file.metadata.deleted_tags, new_metadata.deleted_tags)

    def test_copy_metadata_must_preserve_deleted_tags_by_default(self):
        new_metadata = Metadata({
            'title': 'othertitle',
            '~foo': 'bar',
        })
        del new_metadata['foo']
        self.file.copy_metadata(new_metadata)
        self.assertEqual(self.file.metadata, new_metadata)
        self.assertEqual(self.file.metadata.deleted_tags, {'deletedtag', 'foo'})

    def test_copy_metadata_do_not_preserve_deleted_tags(self):
        new_metadata = Metadata({
            'title': 'othertitle',
            '~foo': 'bar',
        })
        del new_metadata['foo']
        self.file.copy_metadata(new_metadata, preserve_deleted=False)
        self.assertEqual(self.file.metadata, new_metadata)
        self.assertEqual(self.file.metadata.deleted_tags, {'foo'})

    def test_copy_metadata_must_keep_file_content_specific_tags(self):
        for tag in CALCULATED_TAGS:
            self.file.metadata[tag] = 'foo'
        new_metadata = Metadata()
        self.file.copy_metadata(new_metadata)
        for tag in CALCULATED_TAGS:
            self.assertEqual(
                self.file.metadata[tag], 'foo',
                f'Tag {tag}: {self.file.metadata[tag]!r} != "foo"')

    def test_copy_metadata_must_remove_deleted_acoustid_id(self):
        self.file.metadata['acoustid_id'] = 'foo'
        new_metadata = Metadata()
        new_metadata.delete('acoustid_id')
        self.file.copy_metadata(new_metadata)
        self.assertEqual(self.file.metadata['acoustid_id'], '')
        self.assertIn('acoustid_id', self.file.metadata.deleted_tags)

    def test_copy_metadata_with_preserved_tags(self):
        self.set_config_values({
            'preserved_tags': ['artist', 'title'],
        })
        new_metadata = Metadata({
            'album': 'otheralbum',
            'artist': 'otherartist',
            'title': 'othertitle',
        })
        self.file.copy_metadata(new_metadata)
        self.assertEqual(self.file.metadata['album'], 'otheralbum')
        self.assertEqual(self.file.metadata['artist'], 'origartist')
        self.assertEqual(self.file.metadata['title'], 'origtitle')

    def test_copy_metadata_must_always_preserve_technical_variables(self):
        self.file.orig_metadata['~filename'] = 'orig.flac'
        new_metadata = Metadata({
            '~filename': 'new.flac',
        })
        self.file.copy_metadata(new_metadata)
        self.assertEqual(self.file.metadata['~filename'], 'orig.flac')
