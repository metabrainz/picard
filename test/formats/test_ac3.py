import os

from .common import (
    CommonTests,
    load_metadata,
    save_and_load_metadata,
)
from .test_apev2 import CommonApeTests

from picard import config
from picard.formats.ac3 import AC3File
from picard.metadata import Metadata


class AC3WithAPETest(CommonApeTests.ApeTestCase):
    testfile = 'test.ac3'
    supports_ratings = False
    expected_info = {}
    unexpected_info = ['~video']

    def setUp(self):
        super().setUp()
        config.setting['ac3_save_ape'] = True
        config.setting['remove_ape_from_ac3'] = True


class AC3NoTagsTest(CommonTests.BaseFileTestCase):
    testfile = 'test-apev2.ac3'

    def setUp(self):
        super().setUp()
        config.setting['ac3_save_ape'] = False
        config.setting['remove_ape_from_ac3'] = False

    def test_load_but_do_not_save_tags(self):
        metadata = load_metadata(self.filename)
        self.assertEqual('Test AC3 with APEv2 tags', metadata['title'])
        self.assertEqual('The Artist', metadata['artist'])
        metadata['artist'] = 'Foo'
        metadata['title'] = 'Bar'
        metadata = save_and_load_metadata(self.filename, metadata)
        self.assertEqual('Test AC3 with APEv2 tags', metadata['title'])
        self.assertEqual('The Artist', metadata['artist'])

    def test_remove_ape_tags(self):
        config.setting['remove_ape_from_ac3'] = True
        metadata = Metadata({
            'artist': 'Foo'
        })
        metadata = save_and_load_metadata(self.filename, metadata)
        self.assertEqual('AC3', metadata['~format'])
        self.assertNotIn('title', metadata)
        self.assertNotIn('artist', metadata)

    def test_info_format(self):
        metadata = load_metadata(os.path.join('test', 'data', 'test.ac3'))
        self.assertEqual('AC3', metadata['~format'])
        metadata = load_metadata(os.path.join('test', 'data', 'test-apev2.ac3'))
        self.assertEqual('AC3 (APEv2)', metadata['~format'])

    def test_supports_tag(self):
        config.setting['ac3_save_ape'] = True
        self.assertTrue(AC3File.supports_tag('title'))
        config.setting['ac3_save_ape'] = False
        self.assertFalse(AC3File.supports_tag('title'))
