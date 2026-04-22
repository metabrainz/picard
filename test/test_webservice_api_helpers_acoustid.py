# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018, 2020-2023 Laurent Monin
# Copyright (C) 2019-2023 Philipp Wolfer
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

from picard.acoustid.manager import Submission
from picard.metadata import Metadata
from picard.webservice import WebService
from picard.webservice.api_helpers import AcoustIdAPIHelper


class AcoustdIdAPITest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.config = {'acoustid_apikey': "apikey"}
        self.set_config_values(self.config)
        self.ws = MagicMock(auto_spec=WebService)
        self.api = AcoustIdAPIHelper(self.ws)
        self.api.acoustid_host = 'acoustid_host'
        self.api.acoustid_port = 443
        self.api.client_key = "key"
        self.api.client_version = "ver"

    def test_encode_acoustid_args_static(self):
        args = {'a': '1', 'b': 'v a l'}
        result = self.api._encode_acoustid_args(args)
        expected = 'a=1&b=v%20a%20l&client=key&clientversion=ver&format=json'
        self.assertEqual(result, expected)

    def test_encode_acoustid_args_static_empty(self):
        args = dict()
        result = self.api._encode_acoustid_args(args)
        expected = 'client=key&clientversion=ver&format=json'
        self.assertEqual(result, expected)

    def test_submissions_to_args(self):
        submissions = [
            Submission('f1', 1, recordingid='or1', metadata=Metadata(musicip_puid='p1')),
            Submission('f2', 2, recordingid='or2', metadata=Metadata(musicip_puid='p2')),
        ]
        submissions[0].recordingid = 'r1'
        submissions[1].recordingid = 'r2'
        result = self.api._submissions_to_args(submissions)
        expected = {
            'user': 'apikey',
            'fingerprint.0': 'f1',
            'duration.0': '1',
            'mbid.0': 'r1',
            'puid.0': 'p1',
            'fingerprint.1': 'f2',
            'duration.1': '2',
            'mbid.1': 'r2',
            'puid.1': 'p2',
        }
        self.assertEqual(result, expected)

    def test_submissions_to_args_invalid_duration(self):
        metadata1 = Metadata(
            {
                'title': 'The Track',
                'artist': 'The Artist',
                'album': 'The Album',
                'albumartist': 'The Album Artist',
                'tracknumber': '4',
                'discnumber': '2',
            },
            length=100000,
        )
        metadata2 = Metadata(
            {'year': '2022'},
            length=100000,
        )
        metadata3 = Metadata(
            {'date': '1980-08-30'},
            length=100000,
        )
        metadata4 = Metadata(
            {'date': '08-30'},
            length=100000,
        )
        submissions = [
            Submission('f1', 500000, recordingid='or1', metadata=metadata1),
            Submission('f2', 500000, recordingid='or2', metadata=metadata2),
            Submission('f3', 500000, recordingid='or3', metadata=metadata3),
            Submission('f4', 500000, recordingid='or4', metadata=metadata4),
        ]
        submissions[0].recordingid = 'r1'
        submissions[1].recordingid = 'r2'
        submissions[1].recordingid = 'r3'
        submissions[1].recordingid = 'r4'
        result = self.api._submissions_to_args(submissions)
        expected = {
            'user': 'apikey',
            'fingerprint.0': 'f1',
            'duration.0': '500000',
            'track.0': metadata1['title'],
            'artist.0': metadata1['artist'],
            'album.0': metadata1['album'],
            'albumartist.0': metadata1['albumartist'],
            'trackno.0': metadata1['tracknumber'],
            'discno.0': metadata1['discnumber'],
            'fingerprint.1': 'f2',
            'duration.1': '500000',
            'year.1': '2022',
            'fingerprint.2': 'f3',
            'duration.2': '500000',
            'year.2': '1980',
            'fingerprint.3': 'f4',
            'duration.3': '500000',
        }
        self.assertEqual(result, expected)
