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

from picard.disc.eaclog import (
    filter_toc_entries,
    toc_from_file,
)
from picard.disc.utils import NotSupportedTOCError


test_log = (
    'TEST LOG',
    ' Track |   Start  |  Length  | Start sector | End sector',
    '---------------------------------------------------------',
    '    1  |  0:00.00 |  5:32.14 |         0    |    24913',
    '    2  |  5:32.14 |  4:07.22 |     24914    |    43460',
    '    3  |  9:39.36 |  3:50.29 |     43461    |    60739',
    '',
    'foo',
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


class TestFilterTocEntries(PicardTestCase):

    def test_filter_toc_entries(self):
        result = filter_toc_entries(iter(test_log))
        self.assertTrue(isinstance(result, Iterator))
        entries = list(result)
        self.assertEqual(test_entries, entries)


class TestTocFromFile(PicardTestCase):

    def _test_toc_from_file(self, logfile):
        test_log = get_test_data_path(logfile)
        toc = toc_from_file(test_log)
        self.assertEqual((1, 8, 149323, 150, 25064, 43611, 60890, 83090, 100000, 115057, 135558), toc)

    def test_toc_from_file_eac_utf8(self):
        self._test_toc_from_file('eac-utf8.log')

    def test_toc_from_file_eac_utf16le(self):
        self._test_toc_from_file('eac-utf16le.log')

    def test_toc_from_file_xld(self):
        self._test_toc_from_file('xld.log')

    def test_toc_from_empty_file(self):
        test_log = get_test_data_path('eac-empty.log')
        with self.assertRaises(NotSupportedTOCError):
            toc_from_file(test_log)
