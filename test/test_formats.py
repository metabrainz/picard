# -*- coding: utf-8 -*-
import logging
import os.path
import shutil
from tempfile import mkstemp
from test.picardtestcase import PicardTestCase
import unittest

import mutagen

from PyQt5 import QtCore

from picard import (
    config,
    log,
)
from picard.coverart.image import (
    CoverArtImage,
    TagCoverArtImage,
)
import picard.formats
from picard.formats import ext_to_format
from picard.metadata import Metadata

settings = {
    'clear_existing_tags': False,
    'embed_only_one_front_image': False,
    'enabled_plugins': '',
    'id3v23_join_with': '/',
    'id3v2_encoding': 'utf-8',
    'rating_steps': 6,
    'rating_user_email': 'users@musicbrainz.org',
    'remove_ape_from_mp3': False,
    'remove_id3_from_flac': False,
    'remove_images_from_tags': False,
    'save_images_to_tags': True,
    'write_id3v1': True,
    'write_id3v23': False,
    'itunes_compatible_grouping': False,
}


def save_metadata(filename, metadata):
    f = picard.formats.open_(filename)
    f._save(filename, metadata)


def load_metadata(filename):
    f = picard.formats.open_(filename)
    return f._load(filename)


def save_and_load_metadata(filename, metadata):
    """Save new metadata to a file and load it again."""
    f = picard.formats.open_(filename)
    loaded_metadata = f._load(filename)
    f._copy_loaded_metadata(loaded_metadata)
    f._save(filename, metadata)
    loaded_metadata = load_metadata(filename)
    return loaded_metadata


def load_raw(filename):
    return mutagen.File(filename)


TAGS = {
    'albumartist': 'Foo',
    'albumartistsort': 'Foo',
    'album': 'Foo Bar',
    'albumsort': 'Foo',
    'arranger': 'Foo',
    'artist': 'Foo',
    'artistsort': 'Foo',
    'asin': 'Foo',
    'barcode': 'Foo',
    'bpm': '80',
    'catalognumber': 'Foo',
    'comment:': 'Foo',
    'comment:foo': 'Foo',
    'compilation': '1',
    'composer': 'Foo',
    'composersort': 'Foo',
    'conductor': 'Foo',
    'copyright': 'Foo',
    'date': '2004',
    'discnumber': '1',
    'discsubtitle': 'Foo',
    'djmixer': 'Foo',
    'encodedby': 'Foo',
    'encodersettings': 'Foo',
    'engineer': 'Foo',
    'gapless': '1',
    'genre': 'Foo',
    'grouping': 'Foo',
    'isrc': 'Foo',
    'key': 'E#m',
    'label': 'Foo',
    'lyricist': 'Foo',
    'lyrics': 'Foo',
    'media': 'Foo',
    'mixer': 'Foo',
    'mood': 'Foo',
    'movement': 'Foo',
    'movementnumber': '2',
    'movementtotal': '8',
    'musicbrainz_albumartistid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_albumid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_artistid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_discid': 'HJRFvVfxx0MU_6v8v9swQUxDmZQ-',
    'musicbrainz_originalalbumid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_originalartistid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_releasegroupid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_trackid': '00000000-0000-0000-0000-000000000000',
    'musicbrainz_trmid': 'Foo',
    'musicbrainz_workid': '00000000-0000-0000-0000-000000000000',
    'musicip_fingerprint': 'Foo',
    'musicip_puid': '00000000-0000-0000-0000-000000000000',
    'originaldate': '1980-01-20',
    'originalyear': '1980',
    'performer:guest vocal': 'Foo',
    'podcast': '1',
    'podcasturl': 'Foo',
    'producer': 'Foo',
    'releasecountry': 'XW',
    'releasestatus': 'Foo',
    'releasetype': 'Foo',
    'remixer': 'Foo',
    'show': 'Foo',
    'showmovement': '1',
    'showsort': 'Foo',
    'subtitle': 'Foo',
    'title': 'Foo',
    'titlesort': 'Foo',
    'totaldiscs': '2',
    'totaltracks': '10',
    'tracknumber': '2',
    'website': 'http://example.com',
    'work': 'Foo'
}


def skipUnlessTestfile(func):
    def _decorator(self, *args, **kwargs):
        if not self.testfile:
            raise unittest.SkipTest("No test file set")
        func(self, *args, **kwargs)
    return _decorator


# prevent unittest to run tests in those classes
class CommonTests:

    class FormatsTest(PicardTestCase):

        testfile = None
        testfile_ext = None
        testfile_path = None

        def setUp(self):
            super().setUp()
            self.tags = TAGS.copy()
            _name, self.testfile_ext = os.path.splitext(self.testfile)
            config.setting = settings.copy()
            if self.testfile:
                self.testfile_path = os.path.join('test', 'data', self.testfile)
                self.testfile_ext = os.path.splitext(self.testfile)[1]
                self.filename = self.copy_of_original_testfile()
            self.setup_tags()

        def copy_of_original_testfile(self):
            return self.copy_file_tmp(self.testfile_path, self.testfile_ext)

        def copy_file_tmp(self, filename, ext):
            fd, copy = mkstemp(suffix=ext)
            self.addCleanup(os.unlink, copy)
            os.close(fd)
            shutil.copy(filename, copy)
            return copy

        def setup_tags(self):
            supports_tag = ext_to_format(self.testfile_ext[1:]).supports_tag
            self.unsupported_tags = {tag : val for tag, val in self.tags.items() if not supports_tag(tag)}
            self.remove_tags(self.unsupported_tags.keys())

        def set_tags(self, dict_tag_value=None):
            if dict_tag_value:
                self.tags.update(dict_tag_value)

        def remove_tags(self, tag_list=None):
            for tag in tag_list:
                del self.tags[tag]

        @skipUnlessTestfile
        def test_simple_tags(self):
            metadata = Metadata()
            for (key, value) in self.tags.items():
                metadata[key] = value
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            for (key, value) in self.tags.items():
                self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))

        @skipUnlessTestfile
        def test_unsupported_tags(self):
            metadata = Metadata()
            for (key, value) in self.unsupported_tags.items():
                metadata[key] = value
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            for tag in self.unsupported_tags:
                self.assertTrue(tag not in loaded_metadata, '%s: %r != None' % (tag, loaded_metadata[tag]))

        @skipUnlessTestfile
        def test_preserve_unchanged_tags(self):
            metadata = Metadata()
            for (key, value) in self.tags.items():
                metadata[key] = value
            save_metadata(self.filename, metadata)
            loaded_metadata = save_and_load_metadata(self.filename, Metadata())
            for (key, value) in self.tags.items():
                self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))

        @skipUnlessTestfile
        def test_delete_simple_tags(self):
            metadata = Metadata()
            for (key, value) in self.tags.items():
                metadata[key] = value
            if self.supports_ratings:
                metadata['~rating'] = 1
            original_metadata = save_and_load_metadata(self.filename, metadata)
            metadata.delete('albumartist')
            if self.supports_ratings:
                metadata.delete('~rating')
            new_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertIn('albumartist', original_metadata.keys())
            self.assertNotIn('albumartist', new_metadata.keys())
            if self.supports_ratings:
                self.assertIn('~rating', original_metadata.keys())
                self.assertNotIn('~rating', new_metadata.keys())

        @skipUnlessTestfile
        def test_delete_non_existant_tags(self):
            metadata = Metadata()
            metadata.delete('albumartist')
            metadata.delete('performer:drums')
            metadata.delete('totaltracks')
            new_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertNotIn('albumartist', new_metadata.keys())
            self.assertNotIn('performer:drums', new_metadata.keys())
            self.assertNotIn('totaltracks', new_metadata.keys())

        @skipUnlessTestfile
        def test_delete_complex_tags(self):
            metadata = Metadata()

            for (key, value) in self.tags.items():
                metadata[key] = value

            original_metadata = save_and_load_metadata(self.filename, metadata)
            metadata.delete('totaldiscs')
            new_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertIn('totaldiscs', original_metadata)
            if self.testfile_ext == '.m4a':
                self.assertEqual(u'0', new_metadata['totaldiscs'])
            else:
                self.assertNotIn('totaldiscs', new_metadata)

        @skipUnlessTestfile
        def test_delete_performer(self):
            if 'performer:guest vocal' in self.tags:
                metadata = Metadata()
                for (key, value) in self.tags.items():
                    metadata[key] = value

                metadata['performer:piano'] = 'Foo'

                original_metadata = save_and_load_metadata(self.filename, metadata)
                metadata.delete('performer:piano')
                new_metadata = save_and_load_metadata(self.filename, metadata)

                self.assertIn('performer:guest vocal', original_metadata)
                self.assertIn('performer:guest vocal', new_metadata)
                self.assertIn('performer:piano', original_metadata)
                self.assertNotIn('performer:piano', new_metadata)

        @skipUnlessTestfile
        def test_ratings(self):
            if not self.supports_ratings:
                raise unittest.SkipTest("Ratings not supported")
            for rating in range(6):
                rating = 1
                metadata = Metadata()
                metadata['~rating'] = rating
                loaded_metadata = save_and_load_metadata(self.filename, metadata)
                self.assertEqual(int(loaded_metadata['~rating']), rating, '~rating: %r != %r' % (loaded_metadata['~rating'], rating))

        @skipUnlessTestfile
        def test_guess_format(self):
            temp_file = self.copy_of_original_testfile()
            audio = picard.formats.guess_format(temp_file)
            audio_original = picard.formats.open_(self.filename)
            self.assertEqual(type(audio), type(audio_original))

        @skipUnlessTestfile
        def test_split_ext(self):
            f = picard.formats.open_(self.filename)
            self.assertEqual(f._fixed_splitext(f.filename), os.path.splitext(f.filename))
            self.assertEqual(f._fixed_splitext(f.EXTENSIONS[0]), ('', f.EXTENSIONS[0]))
            self.assertEqual(f._fixed_splitext('.test'), os.path.splitext('.test'))
            self.assertNotEqual(f._fixed_splitext(f.EXTENSIONS[0]), os.path.splitext(f.EXTENSIONS[0]))

    class ID3Test(FormatsTest):

        def setup_tags(self):
            # Note: in ID3v23, the original date can only be stored as a year.
            super().setup_tags()
            self.set_tags({
                'originaldate': '1980'
            })

        @skipUnlessTestfile
        def test_id3_freeform_delete(self):
            metadata = Metadata()
            for (key, value) in self.tags.items():
                metadata[key] = value

            metadata['Foo'] = 'Foo'
            original_metadata = save_and_load_metadata(self.filename, metadata)
            metadata.delete('Foo')
            new_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertIn('Foo', original_metadata)
            self.assertNotIn('Foo', new_metadata)

        @skipUnlessTestfile
        def test_id3_ufid_delete(self):
            metadata = Metadata()
            for (key, value) in self.tags.items():
                metadata[key] = value
            metadata['musicbrainz_recordingid'] = "Foo"
            original_metadata = save_and_load_metadata(self.filename, metadata)
            metadata.delete('musicbrainz_recordingid')
            new_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertIn('musicbrainz_recordingid', original_metadata)
            self.assertNotIn('musicbrainz_recordingid', new_metadata)

        @skipUnlessTestfile
        def test_id3_multiple_freeform_delete(self):
            metadata = Metadata()
            for (key, value) in self.tags.items():
                metadata[key] = value

            metadata['Foo'] = 'Foo'
            metadata['Bar'] = 'Foo'
            metadata['FooBar'] = 'Foo'
            original_metadata = save_and_load_metadata(self.filename, metadata)
            metadata.delete('Foo')
            metadata.delete('Bar')
            new_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertIn('Foo', original_metadata)
            self.assertIn('Bar', original_metadata)
            self.assertIn('FooBar', original_metadata)
            self.assertNotIn('Foo', new_metadata)
            self.assertNotIn('Bar', new_metadata)
            self.assertIn('FooBar', new_metadata)

        @skipUnlessTestfile
        def test_performer_duplication(self):

            config.setting['write_id3v23'] = True
            metadata = Metadata()
            tags = {
                'album': 'Foo',
                'artist': 'Foo',
                'performer:piano': 'Foo',
                'title': 'Foo',
            }

            for (key, value) in tags.items():
                metadata[key] = value

            original_metadata = save_and_load_metadata(self.filename, metadata)
            new_metadata = save_and_load_metadata(self.filename, original_metadata)

            self.assertEqual(len(new_metadata['performer:piano']), len(original_metadata['performer:piano']))

        @skipUnlessTestfile
        def test_comment_delete(self):
            metadata = Metadata()
            for (key, value) in self.tags.items():
                metadata[key] = value
            metadata['comment:bar'] = 'Foo'
            original_metadata = save_and_load_metadata(self.filename, metadata)
            metadata.delete('comment:bar')
            new_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertIn('comment:foo', original_metadata)
            self.assertIn('comment:bar', original_metadata)
            self.assertIn('comment:foo', new_metadata)
            self.assertNotIn('comment:bar', new_metadata)

        @skipUnlessTestfile
        def test_id3v23_simple_tags(self):
            config.setting['write_id3v23'] = True
            metadata = Metadata()
            for (key, value) in self.tags.items():
                metadata[key] = value
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            for (key, value) in self.tags.items():
                self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))

        @property
        def itunes_grouping_metadata(self):
            metadata = Metadata()
            metadata['grouping'] = 'The Grouping'
            metadata['work'] = 'The Work'
            return metadata

        @skipUnlessTestfile
        def test_standard_grouping(self):
            metadata = self.itunes_grouping_metadata

            config.setting['itunes_compatible_grouping'] = False
            loaded_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertEqual(loaded_metadata['grouping'], metadata['grouping'])
            self.assertEqual(loaded_metadata['work'], metadata['work'])

        @skipUnlessTestfile
        def test_itunes_compatible_grouping(self):
            metadata = self.itunes_grouping_metadata

            config.setting['itunes_compatible_grouping'] = True
            loaded_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertEqual(loaded_metadata['grouping'], metadata['grouping'])
            self.assertEqual(loaded_metadata['work'], metadata['work'])

        @skipUnlessTestfile
        def test_always_read_grp1(self):
            metadata = self.itunes_grouping_metadata

            config.setting['itunes_compatible_grouping'] = True
            save_metadata(self.filename, metadata)
            config.setting['itunes_compatible_grouping'] = False
            loaded_metadata = load_metadata(self.filename)

            self.assertIn(metadata['grouping'], loaded_metadata['grouping'])
            self.assertIn(metadata['work'], loaded_metadata['grouping'])
            self.assertEqual(loaded_metadata['work'], '')

        @skipUnlessTestfile
        def test_always_read_txxx_work(self):
            metadata = self.itunes_grouping_metadata

            config.setting['itunes_compatible_grouping'] = False
            save_metadata(self.filename, metadata)
            config.setting['itunes_compatible_grouping'] = True
            loaded_metadata = load_metadata(self.filename)

            self.assertIn(metadata['grouping'], loaded_metadata['work'])
            self.assertIn(metadata['work'], loaded_metadata['work'])
            self.assertEqual(loaded_metadata['grouping'], '')

        @skipUnlessTestfile
        def test_save_itunnorm_tag(self):
            config.setting['clear_existing_tags'] = True
            iTunNORM = '00001E86 00001E86 0000A2A3 0000A2A3 000006A6 000006A6 000078FA 000078FA 00000211 00000211'
            metadata = Metadata()
            metadata['comment:iTunNORM'] = iTunNORM
            new_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(new_metadata['comment:iTunNORM'], iTunNORM)

        def test_rename_txxx_tags(self):
            file_path = os.path.join('test', 'data', 'test-id3-rename-tags.mp3')
            filename = self.copy_file_tmp(file_path, 'mp3')
            raw_metadata = load_raw(filename)
            self.assertTrue('TXXX:Artists' in raw_metadata)
            self.assertFalse('TXXX:ARTISTS' in raw_metadata)
            self.assertTrue('TXXX:Work' in raw_metadata)
            self.assertFalse('TXXX:WORK' in raw_metadata)
            metadata = load_metadata(filename)
            self.assertEqual(metadata['artists'], 'Artist1; Artist2')
            self.assertFalse('Artists' in metadata)
            self.assertEqual(metadata['work'], 'The Work')
            self.assertFalse('Work' in metadata)
            save_metadata(filename, metadata)
            raw_metadata = load_raw(filename)
            self.assertFalse('TXXX:Artists' in raw_metadata)
            self.assertTrue('TXXX:ARTISTS' in raw_metadata)
            self.assertFalse('TXXX:Work' in raw_metadata)
            self.assertTrue('TXXX:WORK' in raw_metadata)

        def test_preserve_unchanged_tags_v23(self):
            config.setting['write_id3v23'] = True
            self.test_preserve_unchanged_tags()


class FLACTest(CommonTests.FormatsTest):
    testfile = 'test.flac'
    supports_ratings = True

    def test_preserve_waveformatextensible_channel_mask(self):
        config.setting['clear_existing_tags'] = True
        original_metadata = load_metadata(self.filename)
        self.assertEqual(original_metadata['~waveformatextensible_channel_mask'], '0x3')
        new_metadata = save_and_load_metadata(self.filename, original_metadata)
        self.assertEqual(new_metadata['~waveformatextensible_channel_mask'], '0x3')


class WMATest(CommonTests.FormatsTest):
    testfile = 'test.wma'
    supports_ratings = True


class ASFTest(CommonTests.FormatsTest):
    testfile = 'test.asf'
    supports_ratings = True


class MP3Test(CommonTests.ID3Test):
    testfile = 'test.mp3'
    supports_ratings = True


class TTATest(CommonTests.ID3Test):
    testfile = 'test.tta'
    supports_ratings = True


class DSFTest(CommonTests.ID3Test):
    testfile = 'test.dsf'
    supports_ratings = True


class AIFFTest(CommonTests.ID3Test):
    testfile = 'test.aiff'
    supports_ratings = False


class OggVorbisTest(CommonTests.FormatsTest):
    testfile = 'test.ogg'
    supports_ratings = True

    def test_invalid_rating(self):
        filename = os.path.join('test', 'data', 'test-invalid-rating.ogg')
        old_log_level = log.get_effective_level()
        log.set_level(logging.ERROR)
        metadata = load_metadata(filename)
        log.set_level(old_log_level)
        self.assertEqual(metadata["~rating"], "THERATING")


class OggSpxTest(CommonTests.FormatsTest):
    testfile = 'test.spx'
    supports_ratings = True


class OggOpusTest(CommonTests.FormatsTest):
    testfile = 'test.spx'
    supports_ratings = True


class MP4Test(CommonTests.FormatsTest):
    testfile = 'test.m4a'
    supports_ratings = False

    def test_supports_tag(self):
        fmt = ext_to_format(self.testfile_ext[1:])
        self.assertTrue(fmt.supports_tag('copyright'))
        self.assertTrue(fmt.supports_tag('compilation'))
        self.assertTrue(fmt.supports_tag('bpm'))
        self.assertTrue(fmt.supports_tag('djmixer'))
        self.assertTrue(fmt.supports_tag('discnumber'))
        self.assertTrue(fmt.supports_tag('lyrics:lead'))
        self.assertTrue(fmt.supports_tag('~length'))


class WavPackTest(CommonTests.FormatsTest):
    testfile = 'test.wv'
    supports_ratings = False


class MusepackSV7Test(CommonTests.FormatsTest):
    testfile = 'test-sv7.mpc'
    supports_ratings = False


class MusepackSV8Test(CommonTests.FormatsTest):
    testfile = 'test-sv8.mpc'
    supports_ratings = False


class MonkeysAudioTest(CommonTests.FormatsTest):
    testfile = 'test.ape'
    supports_ratings = False


class TAKTest(CommonTests.FormatsTest):
    testfile = 'test.tak'
    supports_ratings = False


class OptimFROGLosslessTest(CommonTests.FormatsTest):
    testfile = 'test.ofr'
    supports_ratings = False

    def test_format(self):
        metadata = load_metadata(self.filename)
        self.assertEqual(metadata['~format'], 'OptimFROG Lossless Audio')


class OptimFROGDUalStreamTest(CommonTests.FormatsTest):
    testfile = 'test.ofs'
    supports_ratings = False

    def test_format(self):
        metadata = load_metadata(self.filename)
        self.assertEqual(metadata['~format'], 'OptimFROG DualStream Audio')


cover_settings = {
    'embed_only_one_front_image': True,
}


class TestCoverArt(PicardTestCase):

    def setUp(self):
        super().setUp()
        with open(os.path.join('test', 'data', 'mb.jpg'), 'rb') as f:
            self.jpegdata = f.read()
        with open(os.path.join('test', 'data', 'mb.png'), 'rb') as f:
            self.pngdata = f.read()

    def _common_set_up(self, extra=None):
        config.setting = settings.copy()
        if extra is not None:
            config.setting.update(extra)

    def _set_up(self, original, extra=None):
        fd, self.filename = mkstemp(suffix=os.path.splitext(original)[1])
        os.close(fd)
        shutil.copy(original, self.filename)
        self._common_set_up(extra)

    def _common_tear_down(self):
        QtCore.QObject.tagger.run_cleanup()

    def _tear_down(self):
        os.unlink(self.filename)
        self._common_tear_down()

    def test_coverartimage(self):
        tests = {
            'jpg': {
                'mime': 'image/jpeg',
                'data': self.jpegdata
            },
            'png': {
                'mime': 'image/png',
                'data': self.pngdata
            },
        }
        tmp_files = []
        for t in tests:
            imgdata = tests[t]['data']
            imgdata2 = imgdata + b'xxx'
            # set data once
            coverartimage = CoverArtImage(
                data=imgdata2
            )
            tmp_file = coverartimage.tempfile_filename
            tmp_files.append(tmp_file)
            l = os.path.getsize(tmp_file)
            # ensure file was written, and check its length
            self.assertEqual(l, len(imgdata2))
            self.assertEqual(coverartimage.data, imgdata2)

            # set data again, with another payload
            coverartimage.set_data(imgdata)

            tmp_file = coverartimage.tempfile_filename
            tmp_files.append(tmp_file)
            l = os.path.getsize(tmp_file)
            # check file length again
            self.assertEqual(l, len(imgdata))
            self.assertEqual(coverartimage.data, imgdata)

        QtCore.QObject.tagger.run_cleanup()

    def test_asf(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.wma'))

    def test_ape(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.wv'))

    def test_mp3(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.mp3'))

    def test_mp4(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.m4a'))

    def test_ogg(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.ogg'))

    def test_flac(self):
        self._test_cover_art(os.path.join('test', 'data', 'test.flac'))

    # test for multiple images added to files, some types don't accept more than
    # one, and there is no guarantee that order is preserved
    def test_asf_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.wma'),
                                   set('abcdefg'[:]))

    def test_ape_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.wv'),
                                   set('a'))

    def test_mp3_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.mp3'),
                                   set('abcdefg'[:]))

    def test_mp4_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.m4a'),
                                   set('abcdefg'[:]))

    def test_ogg_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.ogg'),
                                   set('abcdefg'[:]))

    def test_flac_types(self):
        self._test_cover_art_types(os.path.join('test', 'data', 'test.flac'),
                                   set('abcdefg'[:]))

    def test_asf_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.wma'),
            set('a'))

    def test_ape_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.wv'),
            set('a'))

    def test_mp3_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.mp3'),
            set('a'))

    def test_mp4_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.m4a'),
            set('a'))

    def test_ogg_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.ogg'),
            set('a'))

    def test_flac_types_only_front(self):
        self._test_cover_art_types_only_front(
            os.path.join('test', 'data', 'test.flac'),
            set('a'))

    def test_flac_set_picture_dimensions(self):
        self._set_up(os.path.join('test', 'data', 'test.flac'))
        try:
            tests = [
                CoverArtImage(data=self.jpegdata),
                CoverArtImage(data=self.pngdata),
            ]
            for test in tests:
                self._file_save_image(self.filename, test)
                raw_metadata = load_raw(self.filename)
                pic = raw_metadata.pictures[0]
                self.assertNotEqual(pic.width, 0)
                self.assertEqual(pic.width, test.width)
                self.assertNotEqual(pic.height, 0)
                self.assertEqual(pic.height, test.height)
        finally:
            self._tear_down()

    def _test_cover_art(self, filename):
        self._set_up(filename)
        try:
            source_types = ["front", "booklet"]
            # Use reasonable large data > 64kb.
            # This checks a mutagen error with ASF files.
            tests = [
                CoverArtImage(data=self.jpegdata + b"a" * 1024 * 128, types=source_types),
                CoverArtImage(data=self.pngdata + b"a" * 1024 * 128, types=source_types),
            ]
            for test in tests:
                self._file_save_image(self.filename, test)
                f = picard.formats.open_(self.filename)
                loaded_metadata = f._load(self.filename)
                image = loaded_metadata.images[0]
                self.assertEqual(test.mimetype, image.mimetype)
                self.assertEqual(test, image)
        finally:
            self._tear_down()

    @staticmethod
    def _file_save_image(filename, image):
        f = picard.formats.open_(filename)
        metadata = Metadata()
        metadata.images.append(image)
        f._save(filename, metadata)

    def _cover_metadata(self):
        imgdata = self.jpegdata
        metadata = Metadata()
        metadata.images.append(
            TagCoverArtImage(
                file='a',
                tag='a',
                data=imgdata + b'a',
                support_types=True,
                types=[u'booklet', u'front'],
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='b',
                tag='b',
                data=imgdata + b'b',
                support_types=True,
                types=[u'back'],
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='c',
                tag='c',
                data=imgdata + b'c',
                support_types=True,
                types=[u'front'],
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='d',
                tag='d',
                data=imgdata + b'd',
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='e',
                tag='e',
                data=imgdata + b'e',
                is_front=False
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='f',
                tag='f',
                data=imgdata + b'f',
                types=[u'front']
            )
        )
        metadata.images.append(
            TagCoverArtImage(
                file='g',
                tag='g',
                data=imgdata + b'g',
                types=[u'back'],
                is_front=True
            )
        )
        return metadata

    def test_is_front_image(self):
        self._common_set_up()
        try:
            m = self._cover_metadata()
            front_images = set('acdfg'[:])
            found = set()
            for img in m.images:
                if img.is_front_image():
                    found.add(img.tag)
            self.assertEqual(front_images, found)
        finally:
            self._common_tear_down()

    def _test_cover_art_types(self, filename, expect):
        self._set_up(filename)
        expect = {ord(char) for char in expect}
        try:
            f = picard.formats.open_(self.filename)
            f._save(self.filename, self._cover_metadata())

            f = picard.formats.open_(self.filename)
            loaded_metadata = f._load(self.filename)
            found = set()
            for n, image in enumerate(loaded_metadata.images):
                found.add(image.data[-1])
            self.assertEqual(expect, found)
        finally:
            self._tear_down()

    def _test_cover_art_types_only_front(self, filename, expect):
        self._set_up(filename, {'embed_only_one_front_image': True})
        expect = {ord(char) for char in expect}
        try:
            f = picard.formats.open_(self.filename)
            f._save(self.filename, self._cover_metadata())

            f = picard.formats.open_(self.filename)
            loaded_metadata = f._load(self.filename)
            found = set()
            for n, image in enumerate(loaded_metadata.images):
                found.add(image.data[-1])
            self.assertEqual(expect, found)
        finally:
            self._tear_down()


class AACTest(PicardTestCase):
    filename = os.path.join('test', 'data', 'test.aac')

    def setUp(self):
        super().setUp()
        config.setting = settings.copy()

    def test_can_open_and_save(self):
        metadata = Metadata()
        save_and_load_metadata(self.filename, metadata)


class AACWithAPETest(CommonTests.FormatsTest):
    testfile = 'test-apev2.aac'
    supports_ratings = False


class WAVTest(PicardTestCase):
    filename = os.path.join('test', 'data', 'test.wav')

    def setUp(self):
        super().setUp()
        config.setting = settings.copy()

    def test_can_open_and_save(self):
        metadata = Metadata()
        save_and_load_metadata(self.filename, metadata)


class MIDITest(PicardTestCase):
    filename = os.path.join('test', 'data', 'test.mid')

    def setUp(self):
        super().setUp()
        config.setting = settings.copy()

    def test_can_open_and_save(self):
        metadata = Metadata()
        save_and_load_metadata(self.filename, metadata)
