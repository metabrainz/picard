# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
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

from picard.util import get_base_title_with_suffix


class GetBaseTitle(PicardTestCase):
    def test_base_title_0(self):
        # Test with no matching suffix
        test_title = 'title'
        title = get_base_title_with_suffix(test_title, '(copy)')
        self.assertEqual(title, 'title')

    def test_base_title_1(self):
        # Test with matching suffix but no number section
        test_title = 'title (copy)'
        title = get_base_title_with_suffix(test_title, '(copy)')
        self.assertEqual(title, 'title')

    def test_base_title_2(self):
        # Test with matching suffix and number
        test_title = 'title (copy) (1)'
        title = get_base_title_with_suffix(test_title, '(copy)')
        self.assertEqual(title, 'title')

    def test_base_title_3(self):
        # Test with missing space between suffix and number section
        test_title = 'title (copy)(1)'
        title = get_base_title_with_suffix(test_title, '(copy)')
        self.assertEqual(title, test_title)

    def test_base_title_4(self):
        # Test with missing space between suffix and number section (and missing number)
        test_title = 'title (copy)()'
        title = get_base_title_with_suffix(test_title, '(copy)')
        self.assertEqual(title, test_title)

    def test_base_title_5(self):
        # Test with missing number
        test_title = 'title (copy) ()'
        title = get_base_title_with_suffix(test_title, '(copy)')
        self.assertEqual(title, 'title')

    def test_base_title_6(self):
        # Test with invalid number
        test_title = 'title (copy) (x)'
        title = get_base_title_with_suffix(test_title, '(copy)')
        self.assertEqual(title, test_title)

    def test_base_title_7(self):
        # Test with extra character after number section
        test_title = 'title (copy) (1)x'
        title = get_base_title_with_suffix(test_title, '(copy)')
        self.assertEqual(title, test_title)

    def test_base_title_8(self):
        # Test escaping of suffix
        test_title = 'title (copy) (1)'
        title = get_base_title_with_suffix(test_title, '(c?py)')
        self.assertEqual(title, test_title)
