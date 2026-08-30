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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


import unittest

from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

from picard.util.toc import (
    parse_toc_itunes_cddb,
)


class ITunesCDDB1ParserTest(PicardTestCase):
    @subtest_cases(
        "tag,expected",
        [
            ('5023F08C+100000+4+150+30000+50000+90000', (4, 100000, [150, 30000, 50000, 90000])),
            ('F001F000+4096+1+0', (1, 4096, [0])),
        ],
    )
    def test_parse_valid_itunes_cddb1_tags(self, tag, expected):
        num_tracks, leadout_lba, track_lbas = parse_toc_itunes_cddb(tag)
        self.assertEqual((num_tracks, leadout_lba, track_lbas), expected)

    @subtest_cases(
        "tag,expected_message",
        {
            'missing cddb id': ('+54950+7+150+44942+61305+72755', "CDDB ID is absent"),
            'too few parts': ('5023F08C+54950+7', "unexpected format"),
            'invalid leadout': ('5023F08C+INVALID+7+150+44942+61305+72755', "not a valid integer"),
            'negative leadout': ('5023F08C+-100+7+150+44942+61305+72755', "must be positive"),
            'invalid track count': ('5023F08C+54950+ABC+150+44942+61305+72755', "not a valid integer"),
            'zero track count': ('5023F08C+54950+0+150+44942+61305+72755', "must be positive"),
            'mismatched offset count': ('5023F08C+54950+7+150+44942', "Expected 7 track offsets, got 2"),
            'negative offset': ('5023F08C+54950+2+-150+44942', "must be non-negative"),
            'non monotonic offsets': ('5023F08C+54950+3+150+44942+30000', "strictly increasing"),
            'duplicate offsets': ('5023F08C+100+2+150+150', "strictly increasing"),
            'invalid offset': ('5023F08C+54950+2+150+INVALID', "not valid integers"),
        },
    )
    def test_parse_invalid_itunes_cddb1_tags(self, tag, expected_message):
        with self.assertRaises(ValueError) as cm:
            parse_toc_itunes_cddb(tag)
        self.assertIn(expected_message, str(cm.exception))


if __name__ == '__main__':
    unittest.main()
