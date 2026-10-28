# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021 Philipp Wolfer
# Copyright (C) 2021-2022, 2025 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

from picard.util.time import (
    get_timestamp,
    seconds_to_dhms,
)


class UtilTimeTest(PicardTestCase):
    @subtest_cases(
        "seconds,expected",
        [
            (0, (0, 0, 0, 0)),
            (1, (0, 0, 0, 1)),
            (60, (0, 0, 1, 0)),
            (61, (0, 0, 1, 1)),
            (120, (0, 0, 2, 0)),
            (3599, (0, 0, 59, 59)),
            (3600, (0, 1, 0, 0)),
            (3601, (0, 1, 0, 1)),
            (3660, (0, 1, 1, 0)),
            (3661, (0, 1, 1, 1)),
            (86399, (0, 23, 59, 59)),
            (86400, (1, 0, 0, 0)),
        ],
    )
    def test_seconds_to_dhms(self, seconds, expected):
        self.assertTupleEqual(expected, seconds_to_dhms(seconds))

    @subtest_cases(
        "seconds,expected",
        [
            (0, ""),
            (1, "01s"),
            (60, "01m 00s"),
            (61, "01m 01s"),
            (120, "02m 00s"),
            (3599, "59m 59s"),
            (3600, "01h 00m"),
            (3601, "01h 00m"),
            (3660, "01h 01m"),
            (3661, "01h 01m"),
            (86399, "23h 59m"),
            (86400, "01d 00h"),
        ],
    )
    def test_get_timestamp(self, seconds, expected):
        self.assertEqual(expected, get_timestamp(seconds))
