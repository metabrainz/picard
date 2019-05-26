# -*- coding: utf-8 -*-

from test.picardtestcase import PicardTestCase

from picard.track import TagGenreFilter


class TagGenreFilterTest(PicardTestCase):

    def test_no_filter(self):
        setting = {
            'genres_filter': """
            # comment
            """
        }
        tag_filter = TagGenreFilter(setting=setting)

        self.assertFalse(tag_filter.skip('jazz'))

    def test_strict_filter(self):
        setting = {
            'genres_filter': """
            -jazz
            """
        }
        tag_filter = TagGenreFilter(setting=setting)

        self.assertTrue(tag_filter.skip('jazz'))

    def test_strict_filter_whitelist(self):
        setting = {
            'genres_filter': """
            +jazz
            -jazz
            """
        }
        tag_filter = TagGenreFilter(setting=setting)

        self.assertFalse(tag_filter.skip('jazz'))

    def test_strict_filter_whitelist_reverseorder(self):
        setting = {
            'genres_filter': """
            -jazz
            +jazz
            """
        }
        tag_filter = TagGenreFilter(setting=setting)

        self.assertFalse(tag_filter.skip('jazz'))

    def test_wildcard_filter_all_but(self):
        setting = {
            'genres_filter': """
            -*
            +blues
            """
        }
        tag_filter = TagGenreFilter(setting=setting)
        self.assertTrue(tag_filter.skip('jazz'))
        self.assertTrue(tag_filter.skip('rock'))
        self.assertFalse(tag_filter.skip('blues'))

    def test_wildcard_filter(self):
        setting = {
            'genres_filter': """
            -jazz*
            -*rock
            -*disco*
            -a*b
            """
        }
        tag_filter = TagGenreFilter(setting=setting)

        self.assertTrue(tag_filter.skip('jazz'))
        self.assertTrue(tag_filter.skip('jazz blues'))
        self.assertFalse(tag_filter.skip('blues jazz'))

        self.assertTrue(tag_filter.skip('rock'))
        self.assertTrue(tag_filter.skip('blues rock'))
        self.assertFalse(tag_filter.skip('rock blues'))

        self.assertTrue(tag_filter.skip('disco'))
        self.assertTrue(tag_filter.skip('xdisco'))
        self.assertTrue(tag_filter.skip('discox'))

        self.assertTrue(tag_filter.skip('ab'))
        self.assertTrue(tag_filter.skip('axb'))
        self.assertTrue(tag_filter.skip('axxb'))
        self.assertFalse(tag_filter.skip('xab'))

    def test_regex_filter(self):
        setting = {
            'genres_filter': """
            -/^j.zz/
            -/r[io]ck$/
            -/disco+/
            +/discoooo/
            +/*/
            """
        }
        tag_filter = TagGenreFilter(setting=setting)

        self.assertTrue(tag_filter.skip('jazz'))
        self.assertTrue(tag_filter.skip('jizz'))
        self.assertTrue(tag_filter.skip('jazz blues'))
        self.assertFalse(tag_filter.skip('blues jazz'))

        self.assertTrue(tag_filter.skip('rock'))
        self.assertTrue(tag_filter.skip('blues rock'))
        self.assertTrue(tag_filter.skip('blues rick'))
        self.assertFalse(tag_filter.skip('rock blues'))

        self.assertTrue(tag_filter.skip('disco'))
        self.assertTrue(tag_filter.skip('xdiscox'))
        self.assertTrue(tag_filter.skip('xdiscooox'))
        self.assertFalse(tag_filter.skip('xdiscoooox'))
