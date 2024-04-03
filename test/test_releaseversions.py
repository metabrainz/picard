# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013, 2018, 2020-2021 Laurent Monin
# Copyright (C) 2014 Michael Wiencek
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019-2020 Philipp Wolfer
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

from unittest.mock import patch

from test.picardtestcase import (
    PicardTestCase,
    load_test_json,
)

from picard.releasegroup import (
    ReleaseGroup,
    prepare_releases_for_versions,
)


settings = {
    "standardize_tracks": False,
    "standardize_artists": False,
    "standardize_releases": False,
    "translate_artist_names": False
}


class ReleaseTest(PicardTestCase):

    def test_1(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_2.json')
        releases = list(prepare_releases_for_versions(rlist['releases']))
        expected = [
            {'id': '123', 'year': '2009', 'country': 'GB', 'format': 'CD', 'label': 'label A', 'catnum': 'cat 123', 'tracks': '5', 'barcode': '0123456789', 'packaging': 'Jewel Case', 'disambiguation': 'special', '_disambiguate_name': [], 'totaltracks': 5, 'countries': [], 'formats': ['CD']},
            {'id': '456', 'year': '2009', 'country': 'GB', 'format': 'CD', 'label': 'label A', 'catnum': 'cat 123', 'tracks': '5', 'barcode': '0123456789', 'packaging': 'Digipak', 'disambiguation': 'special', '_disambiguate_name': [], 'totaltracks': 5, 'countries': [], 'formats': ['CD']},
            {'id': '789', 'year': '2009', 'country': 'GB', 'format': 'CD', 'label': 'label A', 'catnum': 'cat 123', 'tracks': '5', 'barcode': '0123456789', 'packaging': 'Digipak', 'disambiguation': 'specialx', '_disambiguate_name': [], 'totaltracks': 5, 'countries': [], 'formats': ['CD']},
        ]
        self.assertEqual(releases, expected)
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Jewel Case / special')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Digipak / special')
        self.assertEqual(r.versions[2]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Digipak / specialx')

    def test_2(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_3.json')
        releases = list(prepare_releases_for_versions(rlist['releases']))
        expected = [
            {'id': '789', 'year': '2011', 'country': 'FR', 'format': 'CD', 'label': 'label A', 'catnum': 'cat 123', 'tracks': '5', 'barcode': '0123456789', 'packaging': '??', 'disambiguation': 'special A', '_disambiguate_name': [], 'totaltracks': 5, 'countries': [], 'formats': ['CD']},
            {'id': '789', 'year': '2011', 'country': 'FR', 'format': 'CD', 'label': 'label A', 'catnum': 'cat 123', 'tracks': '5', 'barcode': '0123456789', 'packaging': '??', 'disambiguation': '', '_disambiguate_name': [], 'totaltracks': 5, 'countries': [], 'formats': ['CD']},
        ]
        self.assertEqual(releases, expected)
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2011 / FR / CD / label A / cat 123 / special A')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2011 / FR / CD / label A / cat 123')

    def test_3(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_4.json')
        releases = list(prepare_releases_for_versions(rlist['releases']))
        expected = [
            {'id': '789', 'year': '2009', 'country': 'FR', 'format': 'CD', 'label': 'label A', 'catnum': 'cat 123', 'tracks': '5', 'barcode': '0123456789', 'packaging': '??', 'disambiguation': '', '_disambiguate_name': [], 'totaltracks': 5, 'countries': [], 'formats': ['CD']},
            {'id': '789', 'year': '2009', 'country': 'FR', 'format': 'CD', 'label': 'label A', 'catnum': 'cat 123', 'tracks': '5', 'barcode': '[no barcode]', 'packaging': '??', 'disambiguation': '', '_disambiguate_name': [], 'totaltracks': 5, 'countries': [], 'formats': ['CD']},
        ]
        self.assertEqual(releases, expected)
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2009 / FR / CD / label A / cat 123 / 0123456789')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2009 / FR / CD / label A / cat 123 / [no barcode]')

    @patch('picard.releasegroup.VERSIONS_MAX_TRACKS', 2)
    def test_4(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_5.json')
        releases = list(prepare_releases_for_versions(rlist['releases']))
        expected = [
            {'id': '789', 'year': '2009', 'country': 'FR', 'format': '3×CD', 'label': 'label A', 'catnum': 'cat 123', 'tracks': '2+3+…', 'barcode': '0123456789', 'packaging': '??', 'disambiguation': '', '_disambiguate_name': [], 'totaltracks': 9, 'countries': [], 'formats': ['CD', 'CD', 'CD']},
        ]
        self.assertEqual(releases, expected)

    @patch('picard.releasegroup.VERSIONS_MAX_TRACKS', 3)
    def test_5(self):
        self.set_config_values(settings)
        rlist = load_test_json('release_group_5.json')
        releases = list(prepare_releases_for_versions(rlist['releases']))
        expected = [
            {'id': '789', 'year': '2009', 'country': 'FR', 'format': '3×CD', 'label': 'label A', 'catnum': 'cat 123', 'tracks': '2+3+4', 'barcode': '0123456789', 'packaging': '??', 'disambiguation': '', '_disambiguate_name': [], 'totaltracks': 9, 'countries': [], 'formats': ['CD', 'CD', 'CD']},
        ]
        self.assertEqual(releases, expected)
