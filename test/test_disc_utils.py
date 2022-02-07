# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 Philipp Wolfer
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

from picard.disc.utils import (
    NotSupportedTOCError,
    calculate_mb_toc_numbers,
)


test_entries = [
    {
        'num': '1',
        'start_time': '0:00.00',
        'length_time': '5:32.14',
        'start_sector': '0',
        'end_sector': '24913'
    }, {
        'num': '2',
        'start_time': '5:32.14',
        'length_time': '4:07.22',
        'start_sector': '24914',
        'end_sector': '43460'
    }, {
        'num': '3',
        'start_time': '9:39.36',
        'length_time': '3:50.29',
        'start_sector': '43461',
        'end_sector': '60739'
    }
]


class TestCalculateMbTocNumbers(PicardTestCase):

    def test_calculate_mb_toc_numbers(self):
        self.assertEqual((1, 3, 60890, 150, 25064, 43611), calculate_mb_toc_numbers(test_entries))

    def test_calculate_mb_toc_numbers_invalid_track_numbers(self):
        entries = [{'num': '1'}, {'num': '3'}, {'num': '4'}]
        with self.assertRaises(NotSupportedTOCError):
            calculate_mb_toc_numbers(entries)

    def test_calculate_mb_toc_numbers_empty_entries(self):
        with self.assertRaises(NotSupportedTOCError):
            calculate_mb_toc_numbers([])
