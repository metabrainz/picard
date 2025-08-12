# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
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

from picard.album import TracksCache


class TestTracksCache(PicardTestCase):
    def setUp(self):
        self.cache = TracksCache()
        self._init_cache(self.cache)

    @staticmethod
    def _init_cache(cache):
        # Mock Track object
        class MockTrack:
            def __init__(self, metadata):
                self.orig_metadata = metadata

        tracks = [
            MockTrack(
                {
                    'musicbrainz_recordingid': 'rec1',
                    'musicbrainz_trackid': 'track1',
                    'tracknumber': '1',
                    'discnumber': '1',
                }
            ),
            MockTrack(
                {
                    'musicbrainz_recordingid': 'rec2',
                    'musicbrainz_trackid': 'track2',
                    'tracknumber': '2',
                    'discnumber': '1',
                }
            ),
            MockTrack(
                {
                    'musicbrainz_recordingid': 'rec1',
                    'musicbrainz_trackid': 'track3',
                    'tracknumber': '2',
                    'discnumber': '2',
                }
            ),
            MockTrack(
                {
                    'musicbrainz_recordingid': 'rec4',
                    'musicbrainz_trackid': 'track4',
                    'tracknumber': '1',
                    'discnumber': '1',
                }
            ),
        ]
        cache.build(tracks)

    def test_build_cache(self):
        self.assertTrue(self.cache._initialized)
        self.assertIsNotNone(self.cache._cache[('rec1', '1', '1')])
        self.assertIsNotNone(self.cache._cache[('rec2', '2', '1')])
        self.assertIsNotNone(self.cache._cache[('rec1', '2', '2')])
        self.assertIsNotNone(self.cache._cache[('track1', '1', '1')])
        self.assertIsNotNone(self.cache._cache[('track2', '2', '1')])
        self.assertIsNotNone(self.cache._cache[('track3', '2', '2')])
        self.assertIsNotNone(self.cache._cache[('rec1', '1')])
        self.assertIsNotNone(self.cache._cache[('rec2', '2')])
        self.assertIsNotNone(self.cache._cache[('rec1',)])
        self.assertIsNotNone(self.cache._cache[('track1',)])

    def test_get_track_by_all(self):
        track = self.cache.get_track('rec1', '1', '1')
        self.assertEqual(track.orig_metadata['musicbrainz_trackid'], 'track1')

    def test_get_track_by_recording_and_tracknumber(self):
        track = self.cache.get_track('rec1', '2')
        self.assertEqual(track.orig_metadata['musicbrainz_trackid'], 'track3')

    def test_get_track_by_recording_id(self):
        track = self.cache.get_track('rec2')
        self.assertEqual(track.orig_metadata['musicbrainz_trackid'], 'track2')

    def test_get_track_by_track_and_tracknumber(self):
        track = self.cache.get_track('track1', '1')
        self.assertEqual(track.orig_metadata['musicbrainz_recordingid'], 'rec1')

    def test_get_track_by_track_id(self):
        track = self.cache.get_track('track2')
        self.assertEqual(track.orig_metadata['musicbrainz_recordingid'], 'rec2')

    def test_get_track_not_found(self):
        track = self.cache.get_track('nonexistent')
        self.assertIsNone(track)

    def test_bool(self):
        cache = TracksCache()
        self.assertFalse(cache)
        self._init_cache(cache)
        self.assertTrue(cache)
