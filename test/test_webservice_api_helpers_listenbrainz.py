# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Philipp Wolfer
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

from unittest.mock import Mock

from PyQt6.QtCore import QUrl

from test.picardtestcase import PicardTestCase

from picard import PICARD_VERSION_STR
from picard.metadata import Metadata
from picard.webservice.api_helpers.listenbrainz import (
    ListenBrainzAPIHelper,
    ListenPayload,
    ListenSubmission,
    ListenType,
    TrackMetadata,
)


class TestListenBrainzAPIHelper(PicardTestCase):
    def test_submit_listen(self):
        webservice = Mock()
        api_helper = ListenBrainzAPIHelper(webservice)
        user_token = '12345'
        submission = ListenSubmission(ListenType.SINGLE, [ListenPayload(TrackMetadata('Artist', 'Track'))])

        def reply_handler(data, reply, error):
            pass

        api_helper.submit_listen(user_token, submission, reply_handler)
        webservice.post_url.assert_called_once_with(
            url=QUrl('https://api.listenbrainz.org/1/submit-listens'),
            data=submission.as_json(),
            handler=reply_handler,
            mblogin=False,
            headers={'Authorization': f'Token {user_token}'},
        )

    def test_serialize_listen(self):
        listen = ListenSubmission(ListenType.SINGLE, [ListenPayload(TrackMetadata('Artist', 'Track'), 1771628400)])
        expected_json = '{"listen_type": "single", "payload": [{"listened_at": 1771628400, "track_metadata": {"artist_name": "Artist", "track_name": "Track"}}]}'
        self.assertEqual(listen.as_json(), expected_json)

    def test_track_from_metadata(self):
        metadata = Metadata(
            {
                'artist': 'Artist',
                'title': 'Track',
                'album': 'Release',
                'musicbrainz_recordingid': '00000000-0000-0000-0000-000000000001',
                'musicbrainz_artistid': [
                    '00000000-0000-0000-0000-000000000002',
                    '00000000-0000-0000-0000-000000000003',
                ],
            }
        )
        metadata.length = 300000
        track = TrackMetadata.from_metadata(metadata)
        self.assertEqual(track.artist_name, 'Artist')
        self.assertEqual(track.track_name, 'Track')
        self.assertEqual(track.release_name, 'Release')
        self.assertEqual(
            track.additional_info,
            {
                'media_player': 'MusicBrainz Picard',
                'media_player_version': PICARD_VERSION_STR,
                'duration_ms': 300000,
                'recording_mbid': '00000000-0000-0000-0000-000000000001',
                'artist_mbids': [
                    '00000000-0000-0000-0000-000000000002',
                    '00000000-0000-0000-0000-000000000003',
                ],
            },
        )

    def test_track_from_dict(self):
        track = TrackMetadata.from_dict(
            {
                'artist_name': 'Artist',
                'track_name': 'Track',
                'release_name': 'Release',
                'additional_info': {
                    'duration_ms': 300000,
                    'recording_mbid': '00000000-0000-0000-0000-000000000001',
                },
            }
        )
        self.assertEqual(track.artist_name, 'Artist')
        self.assertEqual(track.track_name, 'Track')
        self.assertEqual(track.release_name, 'Release')
        self.assertEqual(
            track.additional_info,
            {
                'duration_ms': 300000,
                'recording_mbid': '00000000-0000-0000-0000-000000000001',
            },
        )
