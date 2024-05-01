# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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

from collections import defaultdict

from test.picardtestcase import PicardTestCase

from picard.webservice import ratecontrol


class RateControlTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        ratecontrol.REQUEST_DELAY_MINIMUM = defaultdict(lambda: 1000)

    def test_set_minimum_delay(self):
        hostkey = ('example.com', 80)
        ratecontrol.set_minimum_delay(hostkey, 200)
        self.assertEqual(200, ratecontrol.REQUEST_DELAY_MINIMUM[hostkey])

    def test_set_minimum_delay_with_float(self):
        hostkey = ('example.com', 80)
        ratecontrol.set_minimum_delay(hostkey, 33.8)
        self.assertEqual(33, ratecontrol.REQUEST_DELAY_MINIMUM[hostkey])

    def test_set_minimum_delay_for_url(self):
        hostkey = ('example.com', 443)
        ratecontrol.set_minimum_delay_for_url('https://example.com', 300)
        self.assertEqual(300, ratecontrol.REQUEST_DELAY_MINIMUM[hostkey])
