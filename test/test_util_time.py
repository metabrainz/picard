# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021 Laurent Monin
# Copyright (C) 2021 Philipp Wolfer
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

from picard.util.time import (
    get_timestamp,
    seconds_to_dhms,
)


class UtilTimeTest(PicardTestCase):

    def test_seconds_to_dhms(self):
        self.assertTupleEqual(seconds_to_dhms(0), (0, 0, 0, 0))
        self.assertTupleEqual(seconds_to_dhms(1), (0, 0, 0, 1))
        self.assertTupleEqual(seconds_to_dhms(60), (0, 0, 1, 0))
        self.assertTupleEqual(seconds_to_dhms(61), (0, 0, 1, 1))
        self.assertTupleEqual(seconds_to_dhms(120), (0, 0, 2, 0))
        self.assertTupleEqual(seconds_to_dhms(3599), (0, 0, 59, 59))
        self.assertTupleEqual(seconds_to_dhms(3600), (0, 1, 0, 0))
        self.assertTupleEqual(seconds_to_dhms(3601), (0, 1, 0, 1))
        self.assertTupleEqual(seconds_to_dhms(3660), (0, 1, 1, 0))
        self.assertTupleEqual(seconds_to_dhms(3661), (0, 1, 1, 1))
        self.assertTupleEqual(seconds_to_dhms(86399), (0, 23, 59, 59))
        self.assertTupleEqual(seconds_to_dhms(86400), (1, 0, 0, 0))

    def test_get_timestamp(self):
        self.assertEqual(get_timestamp(0), "")
        self.assertEqual(get_timestamp(1), "01s")
        self.assertEqual(get_timestamp(60), "01m 00s")
        self.assertEqual(get_timestamp(61), "01m 01s")
        self.assertEqual(get_timestamp(120), "02m 00s")
        self.assertEqual(get_timestamp(3599), "59m 59s")
        self.assertEqual(get_timestamp(3600), "01h 00m")
        self.assertEqual(get_timestamp(3601), "01h 00m")
        self.assertEqual(get_timestamp(3660), "01h 01m")
        self.assertEqual(get_timestamp(3661), "01h 01m")
        self.assertEqual(get_timestamp(86399), "23h 59m")
        self.assertEqual(get_timestamp(86400), "01d 00h")
