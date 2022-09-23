# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 Laurent Monin
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


from typing import Iterator

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard.disc.dbpoweramplog import (
    filter_toc_entries,
    toc_from_file,
)
from picard.disc.utils import (
    NotSupportedTOCError,
    TocEntry,
)


test_log = (
    'TEST LOG',
    'Track 1:  Ripped LBA 0 to 24914 (5:32) in 0:30. Filename: ',
    '',
    'Track 2:  Ripped LBA 24914 to 43461 (4:07) in 0:20. Filename: ',
    'Track 3:  Ripped LBA 43461 to 60740 (3:50) in 0:17. Filename: ',
    '',
    'foo',
)

test_entries = [
    TocEntry(1, 0, 24913),
    TocEntry(2, 24914, 43460),
    TocEntry(3, 43461, 60739),
]


class TestFilterTocEntries(PicardTestCase):

    def test_filter_toc_entries(self):
        result = filter_toc_entries(iter(test_log))
        self.assertTrue(isinstance(result, Iterator))
        entries = list(result)
        self.assertEqual(test_entries, entries)

    def test_no_gaps_in_track_numbers(self):
        log = test_log[:2] + test_log[4:]
        with self.assertRaisesRegex(NotSupportedTOCError, '^Non consecutive track numbers'):
            list(filter_toc_entries(log))


class TestTocFromFile(PicardTestCase):

    def _test_toc_from_file(self, logfile):
        test_log = get_test_data_path(logfile)
        toc = toc_from_file(test_log)
        self.assertEqual((1, 8, 149323, 150, 25064, 43611, 60890, 83090, 100000, 115057, 135558), toc)

    def test_toc_from_file_utf8(self):
        self._test_toc_from_file('dbpoweramp-utf8.txt')

    def test_toc_from_file_utf16le(self):
        self._test_toc_from_file('dbpoweramp-utf16le.txt')

    def test_toc_from_file_with_datatrack(self):
        test_log = get_test_data_path('dbpoweramp-datatrack.txt')
        toc = toc_from_file(test_log)
        self.assertEqual((1, 13, 239218, 150, 16988, 32954, 48647, 67535, 87269, 104221, 121441, 138572, 152608, 170362, 187838, 215400), toc)

    def test_toc_from_empty_file(self):
        test_log = get_test_data_path('eac-empty.log')
        with self.assertRaises(NotSupportedTOCError):
            toc_from_file(test_log)
