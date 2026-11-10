# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013, 2018, 2020-2025 Laurent Monin
# Copyright (C) 2014 Michael Wiencek
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019-2020, 2026 Philipp Wolfer
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


from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import (
    PicardTestCase,
    load_test_json,
)

from picard.options import StandardizeArtistNames
from picard.releasegroup import (
    ReleaseGroup,
    alternative_versions,
    prepare_releases_for_versions,
)


settings = {
    "standardize_artist_names": StandardizeArtistNames.NONE,
    "translate_artist_names": False,
}


class ReleaseTest(PicardTestCase):
    def test_disambiguate_by_packaging(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_2.json')
        releases = list(prepare_releases_for_versions(rlist['releases']))
        expected = [
            {
                'id': '123',
                'year': '2009',
                'country': 'GB',
                'format': 'CD',
                'label': 'label A',
                'catnum': 'cat 123',
                'tracks': '5',
                'barcode': '0123456789',
                'packaging': 'Jewel Case',
                'disambiguation': 'special',
                '_disambiguate_name': [],
                'totaltracks': 5,
                'countries': [],
                'formats': ['CD'],
            },
            {
                'id': '456',
                'year': '2009',
                'country': 'GB',
                'format': 'CD',
                'label': 'label A',
                'catnum': 'cat 123',
                'tracks': '5',
                'barcode': '0123456789',
                'packaging': 'Digipak',
                'disambiguation': 'special',
                '_disambiguate_name': [],
                'totaltracks': 5,
                'countries': [],
                'formats': ['CD'],
            },
            {
                'id': '789',
                'year': '2009',
                'country': 'GB',
                'format': 'CD',
                'label': 'label A',
                'catnum': 'cat 123',
                'tracks': '5',
                'barcode': '0123456789',
                'packaging': 'Digipak',
                'disambiguation': 'specialx',
                '_disambiguate_name': [],
                'totaltracks': 5,
                'countries': [],
                'formats': ['CD'],
            },
        ]
        self.assertEqual(releases, expected)
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'], '5 / 2009 / GB / CD / label A / cat 123 / Jewel Case / special')
        self.assertEqual(r.versions[1]['name'], '5 / 2009 / GB / CD / label A / cat 123 / Digipak / special')
        self.assertEqual(r.versions[2]['name'], '5 / 2009 / GB / CD / label A / cat 123 / Digipak / specialx')

    def test_disambiguate_by_disambiguation_comment(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_3.json')
        releases = list(prepare_releases_for_versions(rlist['releases']))
        expected = [
            {
                'id': '789',
                'year': '2011',
                'country': 'FR',
                'format': 'CD',
                'label': 'label A',
                'catnum': 'cat 123',
                'tracks': '5',
                'barcode': '0123456789',
                'packaging': '??',
                'disambiguation': 'special A',
                '_disambiguate_name': [],
                'totaltracks': 5,
                'countries': [],
                'formats': ['CD'],
            },
            {
                'id': '789',
                'year': '2011',
                'country': 'FR',
                'format': 'CD',
                'label': 'label A',
                'catnum': 'cat 123',
                'tracks': '5',
                'barcode': '0123456789',
                'packaging': '??',
                'disambiguation': '',
                '_disambiguate_name': [],
                'totaltracks': 5,
                'countries': [],
                'formats': ['CD'],
            },
        ]
        self.assertEqual(releases, expected)
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'], '5 / 2011 / FR / CD / label A / cat 123 / special A')
        self.assertEqual(r.versions[1]['name'], '5 / 2011 / FR / CD / label A / cat 123')

    def test_disambiguate_by_barcode(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_4.json')
        releases = list(prepare_releases_for_versions(rlist['releases']))
        expected = [
            {
                'id': '789',
                'year': '2009',
                'country': 'FR',
                'format': 'CD',
                'label': 'label A',
                'catnum': 'cat 123',
                'tracks': '5',
                'barcode': '0123456789',
                'packaging': '??',
                'disambiguation': '',
                '_disambiguate_name': [],
                'totaltracks': 5,
                'countries': [],
                'formats': ['CD'],
            },
            {
                'id': '789',
                'year': '2009',
                'country': 'FR',
                'format': 'CD',
                'label': 'label A',
                'catnum': 'cat 123',
                'tracks': '5',
                'barcode': '[no barcode]',
                'packaging': '??',
                'disambiguation': '',
                '_disambiguate_name': [],
                'totaltracks': 5,
                'countries': [],
                'formats': ['CD'],
            },
        ]
        self.assertEqual(releases, expected)
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'], '5 / 2009 / FR / CD / label A / cat 123 / 0123456789')
        self.assertEqual(r.versions[1]['name'], '5 / 2009 / FR / CD / label A / cat 123 / [no barcode]')

    @patch('picard.releasegroup.VERSIONS_MAX_TRACKS', 2)
    def test_track_counts_truncated_at_max_tracks(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_5.json')
        releases = list(prepare_releases_for_versions(rlist['releases']))
        expected = [
            {
                'id': '789',
                'year': '2009',
                'country': 'FR',
                'format': '3×CD',
                'label': 'label A',
                'catnum': 'cat 123',
                'tracks': '2+3+…',
                'barcode': '0123456789',
                'packaging': '??',
                'disambiguation': '',
                '_disambiguate_name': [],
                'totaltracks': 9,
                'countries': [],
                'formats': ['CD', 'CD', 'CD'],
            },
        ]
        self.assertEqual(releases, expected)

    @patch('picard.releasegroup.VERSIONS_MAX_TRACKS', 3)
    def test_track_counts_shown_in_full_within_max_tracks(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_5.json')
        releases = list(prepare_releases_for_versions(rlist['releases']))
        expected = [
            {
                'id': '789',
                'year': '2009',
                'country': 'FR',
                'format': '3×CD',
                'label': 'label A',
                'catnum': 'cat 123',
                'tracks': '2+3+4',
                'barcode': '0123456789',
                'packaging': '??',
                'disambiguation': '',
                '_disambiguate_name': [],
                'totaltracks': 9,
                'countries': [],
                'formats': ['CD', 'CD', 'CD'],
            },
        ]
        self.assertEqual(releases, expected)


def _version(release_id, name, totaltracks=10, countries=(), formats=()):
    return {
        'id': release_id,
        'name': name,
        'totaltracks': totaltracks,
        'countries': list(countries),
        'formats': list(formats),
        'extra': '',
    }


def _album(versions, tracks_count):
    album = MagicMock()
    album.release_group.versions = versions
    album.get_num_total_files.return_value = tracks_count
    return album


class ReleaseVersionsFieldsTest(PicardTestCase):
    def test_a_version_keeps_the_fields_of_its_name(self):
        self.set_config_values(settings)
        r = ReleaseGroup(1)
        r._parse_versions(load_test_json('release_group_2.json'))
        version = r.versions[0]
        self.assertEqual(
            ('5', '2009', 'GB', 'CD', 'label A', 'cat 123'),
            tuple(version[key] for key in ('tracks', 'year', 'country', 'format', 'label', 'catnum')),
        )
        self.assertEqual(
            ('Jewel Case', '0123456789', 'special'),
            (version['packaging'], version['barcode'], version['disambiguation']),
        )

    def test_the_name_is_not_escaped_for_a_menu(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_2.json')
        rlist['releases'][0]['label-info'][0]['label']['name'] = 'A&B Records'
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertIn('A&B Records', r.versions[0]['name'])
        self.assertNotIn('&&', r.versions[0]['name'])


class ReleaseVersionsLoadTest(PicardTestCase):
    def test_a_failed_request_is_recorded_and_the_callback_still_called(self):
        r = ReleaseGroup('rg')
        callback = MagicMock()
        http = MagicMock()
        http.errorString.return_value = 'Service unavailable'
        r._request_finished(callback, None, http, 'error')
        callback.assert_called_once_with()
        self.assertTrue(r.loaded)
        self.assertEqual('Service unavailable', r.load_error)
        self.assertEqual([], r.versions)

    def test_a_request_that_succeeds_clears_the_previous_error(self):
        self.set_config_values(settings)
        r = ReleaseGroup('rg')
        r.load_error = 'Service unavailable'
        r._request_finished(MagicMock(), load_test_json('release_group_2.json'), MagicMock(), None)
        self.assertIsNone(r.load_error)
        self.assertEqual(3, len(r.versions))


class AlternativeVersionsTest(PicardTestCase):
    """The order of the other versions of an album, as the GUI menu shows them."""

    def setUp(self):
        super().setUp()
        self.set_config_values({'preferred_release_countries': [], 'preferred_release_formats': []})

    def _ids(self, album):
        return [version['id'] for _group, version in alternative_versions(album)]

    def test_the_versions_with_as_many_tracks_as_the_album_come_first(self):
        versions = [_version('a', 'A', totaltracks=12), _version('b', 'B', totaltracks=10)]
        self.assertEqual(['b', 'a'], self._ids(_album(versions, 10)))

    def test_then_the_preferred_countries_and_formats(self):
        self.set_config_values({'preferred_release_countries': ['GB'], 'preferred_release_formats': ['CD']})
        versions = [
            _version('us-vinyl', 'U', countries=['US'], formats=['Vinyl']),
            _version('gb-vinyl', 'G', countries=['GB'], formats=['Vinyl']),
            _version('us-cd', 'V', countries=['US'], formats=['CD']),
            _version('gb-cd', 'Z', countries=['GB'], formats=['CD']),
        ]
        self.assertEqual(['gb-cd', 'gb-vinyl', 'us-cd', 'us-vinyl'], self._ids(_album(versions, 10)))

    def test_versions_of_a_group_are_ordered_by_name_then_id(self):
        versions = [_version('2', 'B'), _version('3', 'A'), _version('1', 'B')]
        self.assertEqual(['3', '1', '2'], self._ids(_album(versions, 10)))

    def test_the_group_of_each_version_is_given(self):
        versions = [_version('a', 'A', totaltracks=12), _version('b', 'B', totaltracks=10)]
        groups = [group for group, _version in alternative_versions(_album(versions, 10))]
        self.assertEqual([(0, 0, 0), (1, 0, 0)], groups)

    def test_an_album_without_release_group_has_no_versions(self):
        album = _album([], 10)
        album.release_group = None
        self.assertEqual([], alternative_versions(album))

    def test_without_files_the_tracks_of_the_album_are_counted(self):
        album = _album([_version('a', 'A', totaltracks=2), _version('b', 'B', totaltracks=3)], 0)
        album.tracks = [object(), object(), object()]
        self.assertEqual(['b', 'a'], self._ids(album))
