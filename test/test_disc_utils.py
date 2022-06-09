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
    TocEntry,
    calculate_mb_toc_numbers,
)


test_entries = [
    TocEntry(1, 0, 24913),
    TocEntry(2, 24914, 43460),
    TocEntry(3, 43461, 60739),
]


class TestCalculateMbTocNumbers(PicardTestCase):

    def test_calculate_mb_toc_numbers(self):
        self.assertEqual((1, 3, 60890, 150, 25064, 43611), calculate_mb_toc_numbers(test_entries))

    def test_calculate_mb_toc_numbers_invalid_track_numbers(self):
        entries = [TocEntry(1, 0, 100), TocEntry(3, 101, 200), TocEntry(4, 201, 300)]
        with self.assertRaises(NotSupportedTOCError):
            calculate_mb_toc_numbers(entries)

    def test_calculate_mb_toc_numbers_empty_entries(self):
        with self.assertRaises(NotSupportedTOCError):
            calculate_mb_toc_numbers([])

    def test_calculate_mb_toc_numbers_ignore_datatrack(self):
        entries = [*test_entries, TocEntry(4, 72140, 80000)]
        self.assertEqual((1, 3, 60890, 150, 25064, 43611), calculate_mb_toc_numbers(entries))
