# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Laurent Monin
# Copyright (C) 2019 Wieland Hoffmann
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


from test.picardtestcase import PicardTestCase

from picard.track import TagGenreFilter


class TagGenreFilterTest(PicardTestCase):

    def test_no_filter(self):
        tag_filter = TagGenreFilter("# comment")
        self.assertFalse(tag_filter.skip('jazz'))

    def test_strict_filter(self):
        tag_filter = TagGenreFilter("-jazz")
        self.assertTrue(tag_filter.skip('jazz'))

    def test_strict_filter_allowlist(self):
        filters = """
            +jazz
            -jazz
        """
        tag_filter = TagGenreFilter(filters)
        self.assertFalse(tag_filter.skip('jazz'))

    def test_strict_filter_allowlist_reverseorder(self):
        filters = """
            -jazz
            +jazz
        """
        tag_filter = TagGenreFilter(filters)
        self.assertFalse(tag_filter.skip('jazz'))

    def test_wildcard_filter_all_but(self):
        filters = """
            -*
            +blues
        """
        tag_filter = TagGenreFilter(filters)
        self.assertTrue(tag_filter.skip('jazz'))
        self.assertTrue(tag_filter.skip('rock'))
        self.assertFalse(tag_filter.skip('blues'))

    def test_wildcard_filter(self):
        filters = """
            -jazz*
            -*rock
            -*disco*
            -a*b
        """
        tag_filter = TagGenreFilter(filters)

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
        filters = """
            -/^j.zz/
            -/r[io]ck$/
            -/disco+/
            +/discoooo/
        """
        tag_filter = TagGenreFilter(filters)

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

    def test_regex_filter_keep_all(self):
        filters = """
            -/^j.zz/
            -/r[io]ck$/
            -/disco+/
            +/discoooo/
            +/.*/
        """
        tag_filter = TagGenreFilter(filters)

        self.assertFalse(tag_filter.skip('jazz'))
        self.assertFalse(tag_filter.skip('jizz'))
        self.assertFalse(tag_filter.skip('jazz blues'))
        self.assertFalse(tag_filter.skip('blues jazz'))

        self.assertFalse(tag_filter.skip('rock'))
        self.assertFalse(tag_filter.skip('blues rock'))
        self.assertFalse(tag_filter.skip('blues rick'))
        self.assertFalse(tag_filter.skip('rock blues'))

        self.assertFalse(tag_filter.skip('disco'))
        self.assertFalse(tag_filter.skip('xdiscox'))
        self.assertFalse(tag_filter.skip('xdiscooox'))
        self.assertFalse(tag_filter.skip('xdiscoooox'))

    def test_uppercased_filter(self):
        filters = """
            -JAZZ*
            -ROCK
            -/^DISCO$/
        """
        tag_filter = TagGenreFilter(filters)

        self.assertTrue(tag_filter.skip('jazz blues'))
        self.assertTrue(tag_filter.skip('JAZZ BLUES'))
        self.assertTrue(tag_filter.skip('rock'))
        self.assertTrue(tag_filter.skip('ROCK'))
        self.assertTrue(tag_filter.skip('disco'))
        self.assertTrue(tag_filter.skip('DISCO'))

    def test_whitespaces_filter(self):
        filters = """
            - jazz b*
            - * ro ck
            - /^di sco$/
        """
        tag_filter = TagGenreFilter(filters)

        self.assertTrue(tag_filter.skip('jazz blues'))
        self.assertTrue(tag_filter.skip('blues ro ck'))
        self.assertTrue(tag_filter.skip('di sco'))

        self.assertFalse(tag_filter.skip('bluesro ck'))

    def test_filter_method(self):
        tag_filter = TagGenreFilter("-a*")
        self.assertEqual(['bx', 'by'], tag_filter.filter(["ax", "bx", "ay", "by"]))
