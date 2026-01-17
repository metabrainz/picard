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


from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard.disc.scsitoc import toc_from_file


class TestTocFromFile(PicardTestCase):
    def test_toc_from_file(self):
        test_log = get_test_data_path('scsi.toc')
        toc = toc_from_file(test_log)
        self.assertEqual(
            (1, 13, 186400, 150, 1577, 6626, 21547, 29728, 43379, 60379, 81350, 92793, 105047, 127885, 155090, 156793),
            toc,
        )
