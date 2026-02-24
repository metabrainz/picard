# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 metaisfacil
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

import unittest

from test.picardtestcase import PicardTestCase

from picard.util.toc import (
    parse_toc_itunes_cddb,
)


class ITunesCDDB1ParserTest(PicardTestCase):
    def test_parse_valid_itunes_cddb1_tag(self):
        tag = '5023F08C+100000+4+150+30000+50000+90000'
        num_tracks, leadout_lba, track_lbas = parse_toc_itunes_cddb(tag)

        self.assertEqual(num_tracks, 4)
        self.assertEqual(leadout_lba, 100000)
        self.assertEqual(track_lbas, [150, 30000, 50000, 90000])

    def test_parse_itunes_cddb1_single_track(self):
        tag = 'F001F000+4096+1+0'
        num_tracks, leadout_lba, track_lbas = parse_toc_itunes_cddb(tag)

        self.assertEqual(num_tracks, 1)
        self.assertEqual(leadout_lba, 4096)
        self.assertEqual(track_lbas, [0])

    def test_parse_itunes_cddb1_missing_cddb_id(self):
        tag = '+54950+7+150+44942+61305+72755'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("CDDB ID is absent", str(cm.exception))

    def test_parse_itunes_cddb1_too_few_parts(self):
        tag = '5023F08C+54950+7'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("unexpected format", str(cm.exception))

    def test_parse_itunes_cddb1_invalid_leadout(self):
        tag = '5023F08C+INVALID+7+150+44942+61305+72755'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("not a valid integer", str(cm.exception))

    def test_parse_itunes_cddb1_negative_leadout(self):
        tag = '5023F08C+-100+7+150+44942+61305+72755'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("must be positive", str(cm.exception))

    def test_parse_itunes_cddb1_invalid_track_count(self):
        tag = '5023F08C+54950+ABC+150+44942+61305+72755'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("not a valid integer", str(cm.exception))

    def test_parse_itunes_cddb1_zero_track_count(self):
        tag = '5023F08C+54950+0+150+44942+61305+72755'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("must be positive", str(cm.exception))

    def test_parse_itunes_cddb1_mismatched_offset_count(self):
        tag = '5023F08C+54950+7+150+44942'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("Expected 7 track offsets, got 2", str(cm.exception))

    def test_parse_itunes_cddb1_negative_offset(self):
        tag = '5023F08C+54950+2+-150+44942'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("must be non-negative", str(cm.exception))

    def test_parse_itunes_cddb1_non_monotonic_offsets(self):
        tag = '5023F08C+54950+3+150+44942+30000'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("strictly increasing", str(cm.exception))

    def test_parse_itunes_cddb1_duplicate_offsets(self):
        tag = '5023F08C+100+2+150+150'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("strictly increasing", str(cm.exception))

    def test_parse_itunes_cddb1_invalid_offset(self):
        tag = '5023F08C+54950+2+150+INVALID'
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn("not valid integers", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
