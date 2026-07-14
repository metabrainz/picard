# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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


from collections.abc import Iterator

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard.disc.cyanriplog import (
    filter_toc_entries,
    toc_from_file,
)
from picard.disc.utils import (
    NotSupportedTOCError,
    TocEntry,
)


test_log = [
    "cyanrip 0.9.3 (c23f1c4)",
    "System device: /dev/cdrom",
    "Disc tracks: 3",
    "DiscID: testid123",
    "Tracks:",
    "",
    "Track 1 ripped and encoded successfully!",
    "",
    "  Properties:",
    "    Duration: 00:05:32.000",
    "    Start LSN: 0",
    "    End LSN: 24913",
    "",
    "Track 2 ripped and encoded successfully!",
    "",
    "  Properties:",
    "    Duration: 00:04:07.000",
    "    Start LSN: 24914",
    "    End LSN: 43460",
    "",
    "Track 3 ripped and encoded successfully!",
    "",
    "  Properties:",
    "    Duration: 00:03:50.000",
    "    Start LSN: 43461",
    "    End LSN: 60739",
    "",
    "Ripping errors: 0",
]

test_entries = [
    TocEntry(1, 0, 24913),
    TocEntry(2, 24914, 43460),
    TocEntry(3, 43461, 60739),
]


class TestFilterTocEntries(PicardTestCase):
    def test_filter_toc_entries(self):
        result = filter_toc_entries(test_log)
        self.assertIsInstance(result, Iterator)
        entries = list(result)
        self.assertEqual(test_entries, entries)

    def test_empty_log(self):
        result = list(filter_toc_entries([]))
        self.assertEqual([], result)

    def test_no_tracks(self):
        log = [
            "cyanrip 0.9.3 (c23f1c4)",
            "System device: /dev/cdrom",
            "Ripping errors: 0",
        ]
        result = list(filter_toc_entries(log))
        self.assertEqual([], result)


class TestTocFromFile(PicardTestCase):
    def test_toc_from_file(self):
        test_log = get_test_data_path('cyanrip.log')
        toc = toc_from_file(test_log)
        # Track 1: Start LSN 0, End LSN 136919
        # Track 2: Start LSN 136920, End LSN 233754
        # Expected: (first_track, last_track, leadout_offset, offset_1, offset_2)
        # leadout = 233754 + 150 + 1 = 233905
        # offset_1 = 0 + 150 = 150
        # offset_2 = 136920 + 150 = 137070
        self.assertEqual((1, 2, 233905, 150, 137070), toc)

    def test_toc_from_empty_file(self):
        test_log = get_test_data_path('eac-empty.log')
        with self.assertRaises(NotSupportedTOCError):
            toc_from_file(test_log)

    def test_not_a_cyanrip_log(self):
        # An EAC log should be rejected by the cyanrip header check
        test_log = get_test_data_path('eac-utf8.log')
        with self.assertRaises(NotSupportedTOCError):
            toc_from_file(test_log)
