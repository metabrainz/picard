# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Gabriel Ferreira
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

from picard.util.progresscheckpoints import ProgressCheckpoints


class ProgressCheckpointsTest(PicardTestCase):
    def setUp(self):
        super().setUp()

    def test_empty_jobs(self):
        checkpoints = ProgressCheckpoints(0, 1)
        self.assertEqual(list(sorted(checkpoints._checkpoints.keys())), [])
        self.assertEqual(list(sorted(checkpoints._checkpoints.values())), [])

        checkpoints = ProgressCheckpoints(0, 0)
        self.assertEqual(list(sorted(checkpoints._checkpoints.keys())), [])
        self.assertEqual(list(sorted(checkpoints._checkpoints.values())), [])

        checkpoints = ProgressCheckpoints(1, 0)
        self.assertEqual(list(sorted(checkpoints._checkpoints.keys())), [])
        self.assertEqual(list(sorted(checkpoints._checkpoints.values())), [])

    def test_uniformly_spaced_integer_distance(self):
        checkpoints = ProgressCheckpoints(100, 10)
        self.assertEqual(list(sorted(checkpoints._checkpoints.keys())), [10, 20, 30, 40, 50, 60, 70, 80, 90, 99])
        self.assertEqual(list(sorted(checkpoints._checkpoints.values())), [10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

    def test_uniformly_spaced_fractional_distance(self):
        checkpoints = ProgressCheckpoints(100, 7)
        self.assertEqual(list(sorted(checkpoints._checkpoints.keys())), [14, 28, 42, 57, 71, 85, 99])
        self.assertEqual(list(sorted(checkpoints._checkpoints.values())), [14, 28, 42, 57, 71, 85, 100])

        checkpoints = ProgressCheckpoints(10, 20)
        self.assertEqual(list(sorted(checkpoints._checkpoints.keys())), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(list(sorted(checkpoints._checkpoints.values())), [5, 15, 25, 35, 45, 55, 65, 75, 85, 100])

        checkpoints = ProgressCheckpoints(5, 10)
        self.assertEqual(list(sorted(checkpoints._checkpoints.keys())), [0, 1, 2, 3, 4])
        self.assertEqual(list(sorted(checkpoints._checkpoints.values())), [10, 30, 50, 70, 100])
