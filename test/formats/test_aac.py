import os

from .common import (
    CommonTests,
    load_metadata,
    save_and_load_metadata,
)
from .test_apev2 import CommonApeTests

from picard import config
from picard.formats.apev2 import AACFile
from picard.metadata import Metadata


class AACTest(CommonTests.SimpleFormatsTestCase):
    testfile = 'test.aac'
    expected_info = {
        'length': 120,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '123.824',
    }
    unexpected_info = ['~video']


class AACWithAPETest(CommonApeTests.ApeTestCase):
    testfile = 'test-apev2.aac'
    supports_ratings = False
    expected_info = {
        'length': 119,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '123.824',
    }
    unexpected_info = ['~video']


class AACNoTagsTest(CommonTests.BaseFileTestCase):
    testfile = 'test-apev2.aac'

    def setUp(self):
        super().setUp()
        config.setting['aac_save_ape'] = False
        config.setting['remove_ape_from_aac'] = False

    def test_load_but_do_not_save_tags(self):
        metadata = load_metadata(self.filename)
        self.assertEqual('Test AAC with APEv2 tags', metadata['title'])
        self.assertEqual('The Artist', metadata['artist'])
        metadata['artist'] = 'Foo'
        metadata['title'] = 'Bar'
        metadata = save_and_load_metadata(self.filename, metadata)
        self.assertEqual('Test AAC with APEv2 tags', metadata['title'])
        self.assertEqual('The Artist', metadata['artist'])

    def test_remove_ape_tags(self):
        config.setting['remove_ape_from_aac'] = True
        metadata = Metadata({
            'artist': 'Foo'
        })
        metadata = save_and_load_metadata(self.filename, metadata)
        self.assertEqual('AAC', metadata['~format'])
        self.assertNotIn('title', metadata)
        self.assertNotIn('artist', metadata)

    def test_info_format(self):
        metadata = load_metadata(os.path.join('test', 'data', 'test.aac'))
        self.assertEqual('AAC', metadata['~format'])
        metadata = load_metadata(os.path.join('test', 'data', 'test-apev2.aac'))
        self.assertEqual('AAC (APEv2)', metadata['~format'])

    def test_supports_tag(self):
        config.setting['aac_save_ape'] = True
        self.assertTrue(AACFile.supports_tag('title'))
        config.setting['aac_save_ape'] = False
        self.assertFalse(AACFile.supports_tag('title'))
