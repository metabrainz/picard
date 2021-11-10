# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019-2020 Philipp Wolfer
# Copyright (C) 2020 Laurent Monin
# Copyright (C) 2020 Ray Bouchard
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Vladislav Karbovskii
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


import json
import os

from test.picardtestcase import PicardTestCase

from picard.acoustid.json_helpers import parse_recording
from picard.mbjson import recording_to_metadata
from picard.metadata import Metadata
from picard.track import Track


settings = {
    "standardize_tracks": False,
    "standardize_artists": False,
    "standardize_releases": False,
    "translate_artist_names": True,
    "artist_locales": ['en'],
    "translate_artist_names_script_exception": False,
}


class AcoustIDTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.init_test(self.filename)

    def init_test(self, filename):
        self.set_config_values(settings)
        self.json_doc = None
        with open(os.path.join('test', 'data', 'ws_data', filename), encoding='utf-8') as f:
            self.json_doc = json.load(f)


class RecordingTest(AcoustIDTest):
    filename = 'acoustid.json'

    def test_recording(self):
        parsed_recording = parse_recording(self.json_doc)
        release = parsed_recording['releases'][0]
        artist_credit = parsed_recording['artist-credit'][0]
        self.assertEqual(parsed_recording['id'], '017830c1-d1cf-46f3-8801-aaaa0a930223')
        self.assertEqual(parsed_recording['length'], 225000)
        self.assertEqual(parsed_recording['title'], 'Nina')
        self.assertEqual(release['media'], [{'format': 'CD', 'track-count': 12, 'position': 1, 'track': [{'position': 5, 'id': '16affcc3-9f34-48e5-88dc-68378c4cc208', 'number': 5}]}])
        self.assertEqual(release['title'], 'x')
        self.assertEqual(release['id'], 'a2b25883-306f-4a53-809a-a234737c209d')
        self.assertEqual(release['release-group'], {
            'id': 'c24e5416-cd2e-4cff-851b-5faa78db98a2',
            'primary-type': 'Album',
            'secondary-types': ['Compilation']
        })
        self.assertEqual(release['country'], 'XE')
        self.assertEqual(release['date'], {'month': 6, 'day': 23, 'year': 2014})
        self.assertEqual(release['medium-count'], 1)
        self.assertEqual(release['track-count'], 12)
        self.assertEqual(artist_credit['artist'], {'sort-name': 'Ed Sheeran',
                                                   'name': 'Ed Sheeran',
                                                   'id': 'b8a7c51f-362c-4dcb-a259-bc6e0095f0a6'})
        self.assertEqual(artist_credit['name'], 'Ed Sheeran')


class NullRecordingTest(AcoustIDTest):
    filename = 'acoustid_null.json'

    def test_recording(self):
        m = Metadata()
        t = Track("1")
        parsed_recording = parse_recording(self.json_doc)
        recording_to_metadata(parsed_recording, m, t)
        self.assertEqual(m, {})
