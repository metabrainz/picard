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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

from picard.util.isrc import (
    _normalize_isrc,
    format_isrc,
    normalized_isrcs,
    valid_isrc,
)


class TestNormalizeIsrc(PicardTestCase):
    @subtest_cases(
        "value,expected",
        {
            'plain': ('USRC17607839', 'USRC17607839'),
            'with hyphens': ('US-RC1-76-07839', 'USRC17607839'),
            'lowercase': ('usrc17607839', 'USRC17607839'),
            'with spaces': (' US RC1 76 07839 ', 'USRC17607839'),
            'mixed hyphens and spaces': ('GB-AYE-00-00351', 'GBAYE0000351'),
            'empty string': ('', ''),
        },
    )
    def test_normalize(self, value, expected):
        self.assertEqual(expected, _normalize_isrc(value))


class TestValidIsrc(PicardTestCase):
    @subtest_cases(
        "value,expected",
        {
            'plain': ('USRC17607839', 'USRC17607839'),
            'with hyphens': ('US-RC1-76-07839', 'USRC17607839'),
            'lowercase': ('usrc17607839', 'USRC17607839'),
            'alphanumeric registrant': ('FRZ039100014', 'FRZ039100014'),
            'with spaces': ('GB-AYE-00-00351', 'GBAYE0000351'),
            'invalid too short': ('USRC1760783', None),
            'invalid too long': ('USRC176078391', None),
            'invalid bad country code': ('12RC17607839', None),
            'invalid bad year': ('USRC1AB07839', None),
            'invalid bad designation': ('USRC176ABCDE', None),
            'invalid empty': ('', None),
            'invalid random string': ('not-an-isrc', None),
        },
    )
    def test_valid(self, value, expected):
        self.assertEqual(expected, valid_isrc(value))

    def test_idempotent(self):
        """Calling valid_isrc on an already-normalized value returns it unchanged."""
        normalized = valid_isrc('USRC17607839')
        self.assertIsNotNone(normalized)
        assert normalized is not None  # narrow type for the reuse below
        self.assertEqual(normalized, valid_isrc(normalized))


class TestFormatIsrc(PicardTestCase):
    @subtest_cases(
        "value,expected",
        {
            'standard': ('USRC17607839', 'US-RC1-76-07839'),
            'lowercase': ('usrc17607839', 'US-RC1-76-07839'),
            'with hyphens': ('us-rc1-76-07839', 'US-RC1-76-07839'),
            'with spaces': (' US RC1 76 07839 ', 'US-RC1-76-07839'),
            'finnish': ('FI7S51600001', 'FI-7S5-16-00001'),
            'short value unchanged': ('ABC', 'ABC'),
            'empty unchanged': ('', ''),
            # 12 chars but doesn't match ISRC pattern (digits in country code)
            'invalid 12char unchanged': ('12RC17607839', '12RC17607839'),
            'invalid letters in designation': ('USRC176ABCDE', 'USRC176ABCDE'),
        },
    )
    def test_format(self, value, expected):
        self.assertEqual(expected, format_isrc(value))


class TestNormalizedIsrcs(PicardTestCase):
    @subtest_cases(
        "values,expected",
        {
            'valid list': (['USRC17607839', 'GBAYE0000351'], {'USRC17607839', 'GBAYE0000351'}),
            'filters invalid': (['USRC17607839', 'INVALID', '', 'GBAYE0000351'], {'USRC17607839', 'GBAYE0000351'}),
            'normalizes values': (['us-rc1-76-07839', 'GB-AYE-00-00351'], {'USRC17607839', 'GBAYE0000351'}),
            'empty list': ([], set()),
            'all invalid': (['INVALID', 'NOPE', ''], set()),
            'deduplicates': (['USRC17607839', 'usrc17607839', 'US-RC1-76-07839'], {'USRC17607839'}),
        },
    )
    def test_normalized_isrcs(self, values, expected):
        self.assertEqual(expected, normalized_isrcs(values))
