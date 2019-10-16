import os.path

import mutagen

from test.picardtestcase import PicardTestCase

from picard import config
from picard.formats import id3
from picard.metadata import Metadata

from .common import (
    CommonTests,
    load_metadata,
    load_raw,
    save_and_load_metadata,
    save_metadata,
    save_raw,
    skipUnlessTestfile,
)
from .coverart import CommonCoverArtTests


# prevent unittest to run tests in those classes
class CommonId3Tests:

    class Id3TestCase(CommonTests.TagFormatsTestCase):

        def setup_tags(self):
            # Note: in ID3v23, the original date can only be stored as a year.
            super().setup_tags()
            self.set_tags({
                'originaldate': '1980'
            })
            self.unsupported_tags['r128_album_gain'] = '-2857'
            self.unsupported_tags['r128_track_gain'] = '-2857'

        @skipUnlessTestfile
        def test_id3_freeform_delete(self):
            metadata = Metadata(self.tags)
            metadata['Foo'] = 'Foo'
            original_metadata = save_and_load_metadata(self.filename, metadata)
            del metadata['Foo']
            new_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertIn('Foo', original_metadata)
            self.assertNotIn('Foo', new_metadata)

        @skipUnlessTestfile
        def test_id3_ufid_delete(self):
            metadata = Metadata(self.tags)
            metadata['musicbrainz_recordingid'] = "Foo"
            original_metadata = save_and_load_metadata(self.filename, metadata)
            del metadata['musicbrainz_recordingid']
            new_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertIn('musicbrainz_recordingid', original_metadata)
            self.assertNotIn('musicbrainz_recordingid', new_metadata)

        @skipUnlessTestfile
        def test_id3_multiple_freeform_delete(self):
            metadata = Metadata(self.tags)
            metadata['Foo'] = 'Foo'
            metadata['Bar'] = 'Foo'
            metadata['FooBar'] = 'Foo'
            original_metadata = save_and_load_metadata(self.filename, metadata)
            del metadata['Foo']
            del metadata['Bar']
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
            metadata = Metadata({
                'album': 'Foo',
                'artist': 'Foo',
                'performer:piano': 'Foo',
                'title': 'Foo',
            })
            original_metadata = save_and_load_metadata(self.filename, metadata)
            new_metadata = save_and_load_metadata(self.filename, original_metadata)

            self.assertEqual(len(new_metadata['performer:piano']), len(original_metadata['performer:piano']))

        @skipUnlessTestfile
        def test_comment_delete(self):
            metadata = Metadata(self.tags)
            metadata['comment:bar'] = 'Foo'
            original_metadata = save_and_load_metadata(self.filename, metadata)
            del metadata['comment:bar']
            new_metadata = save_and_load_metadata(self.filename, metadata)

            self.assertIn('comment:foo', original_metadata)
            self.assertIn('comment:bar', original_metadata)
            self.assertIn('comment:foo', new_metadata)
            self.assertNotIn('comment:bar', new_metadata)

        @skipUnlessTestfile
        def test_id3v23_simple_tags(self):
            config.setting['write_id3v23'] = True
            metadata = Metadata(self.tags)
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
            self.assertIn('TXXX:Artists', raw_metadata)
            self.assertNotIn('TXXX:ARTISTS', raw_metadata)
            self.assertIn('TXXX:Work', raw_metadata)
            self.assertNotIn('TXXX:WORK', raw_metadata)
            metadata = load_metadata(filename)
            self.assertEqual(metadata['artists'], 'Artist1; Artist2')
            self.assertNotIn('Artists', metadata)
            self.assertEqual(metadata['work'], 'The Work')
            self.assertNotIn('Work', metadata)
            save_metadata(filename, metadata)
            raw_metadata = load_raw(filename)
            self.assertNotIn('TXXX:Artists', raw_metadata)
            self.assertIn('TXXX:ARTISTS', raw_metadata)
            self.assertNotIn('TXXX:Work', raw_metadata)
            self.assertIn('TXXX:WORK', raw_metadata)

        def test_preserve_unchanged_tags_v23(self):
            config.setting['write_id3v23'] = True
            self.test_preserve_unchanged_tags()

        @skipUnlessTestfile
        def test_replaygain_tags_case_insensitive(self):
            tags = mutagen.id3.ID3Tags()
            tags.add(mutagen.id3.TXXX(desc='replaygain_album_gain', text='-6.48 dB'))
            tags.add(mutagen.id3.TXXX(desc='Replaygain_Album_Peak', text='0.978475'))
            tags.add(mutagen.id3.TXXX(desc='replaygain_album_range', text='7.84 dB'))
            tags.add(mutagen.id3.TXXX(desc='replaygain_track_gain', text='-6.16 dB'))
            tags.add(mutagen.id3.TXXX(desc='REPLAYGAIN_track_peak', text='0.976991'))
            tags.add(mutagen.id3.TXXX(desc='REPLAYGAIN_TRACK_RANGE', text='8.22 dB'))
            tags.add(mutagen.id3.TXXX(desc='replaygain_reference_loudness', text='-18.00 LUFS'))
            save_raw(self.filename, tags)
            loaded_metadata = load_metadata(self.filename)
            for (key, value) in self.replaygain_tags.items():
                self.assertEqual(loaded_metadata[key], value, '%s: %r != %r' % (key, loaded_metadata[key], value))

        @skipUnlessTestfile
        def test_ci_tags_preserve_case(self):
            # Ensure values are not duplicated on repeated save and are saved
            # case preserving.
            tags = mutagen.id3.ID3Tags()
            tags.add(mutagen.id3.TXXX(desc='Replaygain_Album_Peak', text='0.978475'))
            save_raw(self.filename, tags)
            loaded_metadata = load_metadata(self.filename)
            loaded_metadata['replaygain_album_peak'] = '1.0'
            save_metadata(self.filename, loaded_metadata)
            raw_metadata = load_raw(self.filename)
            self.assertIn('TXXX:Replaygain_Album_Peak', raw_metadata)
            self.assertEqual(
                raw_metadata['TXXX:Replaygain_Album_Peak'].text[0],
                loaded_metadata['replaygain_album_peak'])
            self.assertEqual(1, len(raw_metadata['TXXX:Replaygain_Album_Peak'].text))
            self.assertNotIn('TXXX:REPLAYGAIN_ALBUM_PEAK', raw_metadata)

        def test_lyrics_with_description(self):
            metadata = Metadata({'lyrics:foo': 'bar'})
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(metadata['lyrics:foo'], loaded_metadata['lyrics:foo'])


class MP3Test(CommonId3Tests.Id3TestCase):
    testfile = 'test.mp3'
    supports_ratings = True
    expected_info = {
        'length': 156,
        '~channels': '2',
        '~sample_rate': '44100',
    }
    unexpected_info = ['~video']


class TTATest(CommonId3Tests.Id3TestCase):
    testfile = 'test.tta'
    supports_ratings = True
    expected_info = {
        'length': 82,
        '~sample_rate': '44100',
    }
    unexpected_info = ['~video']


class DSFTest(CommonId3Tests.Id3TestCase):
    testfile = 'test.dsf'
    supports_ratings = True
    expected_info = {
        'length': 10,
        '~channels': '2',
        '~sample_rate': '5644800',
        '~bitrate': '11289.6',
        '~bits_per_sample': '1',
    }
    unexpected_info = ['~video']


class AIFFTest(CommonId3Tests.Id3TestCase):
    testfile = 'test.aiff'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '1411.2',
    }
    unexpected_info = ['~video']


class Id3UtilTest(PicardTestCase):
    def test_id3text(self):
        teststring = '日本語testÖäß'
        self.assertEqual(id3.id3text(teststring, 0), '???testÖäß')
        self.assertEqual(id3.id3text(teststring, 1), teststring)
        self.assertEqual(id3.id3text(teststring, 3), teststring)

    def test_image_type_from_id3_num(self):
        self.assertEqual(id3.image_type_from_id3_num(0), 'other')
        self.assertEqual(id3.image_type_from_id3_num(3), 'front')
        self.assertEqual(id3.image_type_from_id3_num(6), 'medium')
        self.assertEqual(id3.image_type_from_id3_num(9999), 'other')

    def test_image_type_as_id3_num(self):
        self.assertEqual(id3.image_type_as_id3_num('other'), 0)
        self.assertEqual(id3.image_type_as_id3_num('front'), 3)
        self.assertEqual(id3.image_type_as_id3_num('medium'), 6)
        self.assertEqual(id3.image_type_as_id3_num('track'), 6)
        self.assertEqual(id3.image_type_as_id3_num('unknowntype'), 0)

    def test_types_from_id3(self):
        self.assertEqual(id3.types_from_id3(0), ['other'])
        self.assertEqual(id3.types_from_id3(3), ['front'])
        self.assertEqual(id3.types_from_id3(6), ['medium'])
        self.assertEqual(id3.types_from_id3(9999), ['other'])


class Mp3CoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.mp3'
