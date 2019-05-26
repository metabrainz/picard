# -*- coding: utf-8 -*-

from test.picardtestcase import PicardTestCase

from picard.track import TagGenreFilter


class TagGenreFilterTest(PicardTestCase):

    def __init__(self, *args, **kwargs):
        self.setting = {
            'ignore_genres': 'country,jazz, hip hop  ',
        }
        self.tag_filter = TagGenreFilter(setting=self.setting)

        super().__init__(*args, **kwargs)

    def test_simple_1(self):
        self.assertTrue(self.tag_filter.skip('jazz'))
        self.assertTrue(self.tag_filter.skip('COUNTRY'))
        self.assertTrue(self.tag_filter.skip('hip hop'))

        self.assertFalse(self.tag_filter.skip('rock'))
        self.assertFalse(self.tag_filter.skip('country music'))
        self.assertFalse(self.tag_filter.skip('hip-hop'))
