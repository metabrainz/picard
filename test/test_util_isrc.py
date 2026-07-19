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


from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.util.isrc import (
    _normalize_isrc,
    best_release_from_isrc_results,
    format_isrc,
    normalized_isrcs,
    valid_isrc,
)


class TestNormalizeIsrc(PicardTestCase):
    def test_plain(self):
        self.assertEqual('USRC17607839', _normalize_isrc('USRC17607839'))

    def test_with_hyphens(self):
        self.assertEqual('USRC17607839', _normalize_isrc('US-RC1-76-07839'))

    def test_lowercase(self):
        self.assertEqual('USRC17607839', _normalize_isrc('usrc17607839'))

    def test_with_spaces(self):
        self.assertEqual('USRC17607839', _normalize_isrc(' US RC1 76 07839 '))

    def test_mixed_hyphens_and_spaces(self):
        self.assertEqual('GBAYE0000351', _normalize_isrc('GB-AYE-00-00351'))

    def test_empty_string(self):
        self.assertEqual('', _normalize_isrc(''))


class TestValidIsrc(PicardTestCase):
    def test_valid_plain(self):
        self.assertEqual('USRC17607839', valid_isrc('USRC17607839'))

    def test_valid_with_hyphens(self):
        self.assertEqual('USRC17607839', valid_isrc('US-RC1-76-07839'))

    def test_valid_lowercase(self):
        self.assertEqual('USRC17607839', valid_isrc('usrc17607839'))

    def test_valid_alphanumeric_registrant(self):
        self.assertEqual('FRZ039100014', valid_isrc('FRZ039100014'))

    def test_idempotent(self):
        """Calling valid_isrc on an already-normalized value returns it unchanged."""
        normalized = valid_isrc('USRC17607839')
        self.assertEqual(normalized, valid_isrc(normalized))

    def test_valid_with_spaces(self):
        self.assertEqual('GBAYE0000351', valid_isrc('GB-AYE-00-00351'))

    def test_invalid_too_short(self):
        self.assertIsNone(valid_isrc('USRC1760783'))

    def test_invalid_too_long(self):
        self.assertIsNone(valid_isrc('USRC176078391'))

    def test_invalid_bad_country_code(self):
        self.assertIsNone(valid_isrc('12RC17607839'))

    def test_invalid_bad_year(self):
        self.assertIsNone(valid_isrc('USRC1AB07839'))

    def test_invalid_bad_designation(self):
        self.assertIsNone(valid_isrc('USRC176ABCDE'))

    def test_invalid_empty(self):
        self.assertIsNone(valid_isrc(''))

    def test_invalid_random_string(self):
        self.assertIsNone(valid_isrc('not-an-isrc'))


class TestFormatIsrc(PicardTestCase):
    def test_standard(self):
        self.assertEqual('US-RC1-76-07839', format_isrc('USRC17607839'))

    def test_finnish(self):
        self.assertEqual('FI-7S5-16-00001', format_isrc('FI7S51600001'))

    def test_short_value_unchanged(self):
        self.assertEqual('ABC', format_isrc('ABC'))

    def test_empty_unchanged(self):
        self.assertEqual('', format_isrc(''))

    def test_invalid_12char_unchanged(self):
        # 12 chars but doesn't match ISRC pattern (digits in country code)
        self.assertEqual('12RC17607839', format_isrc('12RC17607839'))

    def test_invalid_letters_in_designation(self):
        self.assertEqual('USRC176ABCDE', format_isrc('USRC176ABCDE'))


class TestNormalizedIsrcs(PicardTestCase):
    def test_valid_list(self):
        result = normalized_isrcs(['USRC17607839', 'GBAYE0000351'])
        self.assertEqual({'USRC17607839', 'GBAYE0000351'}, result)

    def test_filters_invalid(self):
        result = normalized_isrcs(['USRC17607839', 'INVALID', '', 'GBAYE0000351'])
        self.assertEqual({'USRC17607839', 'GBAYE0000351'}, result)

    def test_normalizes_values(self):
        result = normalized_isrcs(['us-rc1-76-07839', 'GB-AYE-00-00351'])
        self.assertEqual({'USRC17607839', 'GBAYE0000351'}, result)

    def test_empty_list(self):
        self.assertEqual(set(), normalized_isrcs([]))

    def test_all_invalid(self):
        self.assertEqual(set(), normalized_isrcs(['INVALID', 'NOPE', '']))

    def test_deduplicates(self):
        result = normalized_isrcs(['USRC17607839', 'usrc17607839', 'US-RC1-76-07839'])
        self.assertEqual({'USRC17607839'}, result)


class TestBestReleaseFromIsrcResults(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'standardize_artist_names': False})
        self.releases = [
            {
                'id': 'release-1',
                'title': 'Some Album',
                'artist-credit': [
                    {'name': 'Some Artist', 'artist': {'name': 'Some Artist', 'sort-name': 'Artist, Some'}}
                ],
            },
            {
                'id': 'release-2',
                'title': 'My Album',
                'artist-credit': [{'name': 'My Artist', 'artist': {'name': 'My Artist', 'sort-name': 'Artist, My'}}],
            },
            {
                'id': 'release-3',
                'title': 'Another Album',
                'artist-credit': [
                    {'name': 'Another Artist', 'artist': {'name': 'Another Artist', 'sort-name': 'Artist, Another'}}
                ],
            },
        ]

    def test_empty_releases(self):
        self.assertEqual('', best_release_from_isrc_results([]))

    def test_single_release(self):
        releases = [{'id': 'only-one', 'title': 'X'}]
        self.assertEqual('only-one', best_release_from_isrc_results(releases))

    def test_no_metadata_returns_first(self):
        self.assertEqual('release-1', best_release_from_isrc_results(self.releases))

    def test_picks_best_title_match(self):
        metadata = MagicMock()
        metadata.get = lambda key, default='': {'album': 'My Album', 'artist': ''}.get(key, default)
        result = best_release_from_isrc_results(self.releases, metadata)
        self.assertEqual('release-2', result)

    def test_picks_best_artist_match(self):
        metadata = MagicMock()
        metadata.get = lambda key, default='': {'album': '', 'artist': 'Another Artist'}.get(key, default)
        result = best_release_from_isrc_results(self.releases, metadata)
        self.assertEqual('release-3', result)

    def test_title_weighted_more_than_artist(self):
        # Title has 2x weight, so title match wins over artist match
        metadata = MagicMock()
        metadata.get = lambda key, default='': {'album': 'Some Album', 'artist': 'My Artist'}.get(key, default)
        result = best_release_from_isrc_results(self.releases, metadata)
        self.assertEqual('release-1', result)
