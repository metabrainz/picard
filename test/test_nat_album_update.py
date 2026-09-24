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


from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.album import NatAlbum
from picard.track import NonAlbumTrack


class NatAlbumUpdateCoalescingTest(PicardTestCase):
    """Regression tests for PICARD-2530 (standalone recording load freeze).

    Loading N standalone recordings finishes each one with a full
    NatAlbum.update(), whose per-track loop re-propagates the album title to
    every sibling track and refreshes every file's metadata. Done once per
    completed recording as N grows, that is O(N^2) main-thread work and a
    large part of the "GUI locked up while loading" symptom.

    The per-track propagation is only needed when the album title actually
    changes; on steady-state per-recording updates the title is unchanged, so
    the loop should be a no-op.
    """

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.track')
        self.set_config_values(setting={'nat_name': 'Standalone Recordings'})
        self.nats = NatAlbum()
        self.tagger.nats = self.nats
        self.tagger.albums = {'NATS': self.nats}
        # Make the tree-item refresh a cheap no-op; we only measure per-track work.
        self.nats.ui_item = MagicMock()

    def _add_nat_with_file(self, nat_id):
        nat = NonAlbumTrack(nat_id)
        # Title already matches the NAT album title (steady state after load).
        nat.metadata['album'] = self.nats.metadata['album']
        # A stand-in file; NatAlbum.update only iterates track.files and calls
        # track.update_file_metadata(file), which we mock out.
        nat.files.append(MagicMock())
        nat.update_file_metadata = MagicMock()
        self.nats.tracks.append(nat)
        return nat

    def test_update_without_title_change_does_not_touch_sibling_files(self):
        """A steady-state NatAlbum.update() must not re-refresh every track's
        file metadata (the O(N) per-call loop that makes loading O(N^2))."""
        nats_tracks = [self._add_nat_with_file(f'rec-{i}') for i in range(10)]

        # Simulate one recording completing: album title is unchanged.
        self.nats.update(update_tracks=False)

        for nat in nats_tracks:
            nat.update_file_metadata.assert_not_called()

    def test_update_with_title_change_propagates_to_all_tracks(self):
        """When the album title actually changes, propagation must still run
        for every track (behaviour preserved)."""
        nats_tracks = [self._add_nat_with_file(f'rec-{i}') for i in range(5)]

        # Change the configured NAT name so the title differs on next update.
        self.set_config_values(setting={'nat_name': 'New NAT Title'})
        self.nats.update()

        for nat in nats_tracks:
            nat.update_file_metadata.assert_called()
            self.assertEqual(nat.metadata['album'], 'New NAT Title')

    def test_total_file_refreshes_stay_linear_across_sequential_loads(self):
        """Simulate N recordings finishing one after another, each triggering a
        NatAlbum.update(). Total per-track file refreshes must be O(N), not
        O(N^2)."""
        total_calls = 0
        n = 20
        loaded = []
        for i in range(n):
            nat = self._add_nat_with_file(f'rec-{i}')
            loaded.append(nat)
            # Each completed recording triggers an album update (title unchanged).
            self.nats.update(update_tracks=False)
            total_calls += sum(t.update_file_metadata.call_count for t in loaded)
            for t in loaded:
                t.update_file_metadata.reset_mock()

        # With the fix, each update touches 0 files (title unchanged), so the
        # running total is 0. Without the fix it would be sum(1..N) == N*(N+1)/2.
        self.assertEqual(total_calls, 0)


class NonAlbumTrackUpdateCallsTest(PicardTestCase):
    """The per-recording finalization must not trigger a full update_tracks
    refresh of the whole NAT album (which re-updates every sibling track item,
    O(N^2) across a bulk load). It should refresh only this track's item and
    the album row (update_tracks=False)."""

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.track')
        self.set_config_values(setting={'nat_name': 'Standalone Recordings'})
        self.tagger.nats = MagicMock()
        self._album_refs = []

    def _make_nat_with_mock_album(self, nat_id='rec-1'):
        nat = NonAlbumTrack(nat_id)
        # Track.album is a weakref property, so keep a strong reference to the
        # mock album alive for the duration of the test (otherwise it may be
        # garbage-collected and nat.album would return None).
        album = MagicMock()
        album.metadata = {'album': 'Standalone Recordings'}
        self._album_refs.append(album)
        nat.album = album
        nat.update = MagicMock()
        return nat

    def test_set_error_does_not_full_refresh_album(self):
        nat = self._make_nat_with_mock_album()
        album = nat.album
        nat._set_error("boom")
        album.update.assert_called_once_with(update_tracks=False)
        nat.update.assert_called_once()

    def test_parse_recording_does_not_full_refresh_album(self):
        nat = self._make_nat_with_mock_album()
        album = nat.album
        # Isolate from track metadata processors and tagging scripts (global,
        # config-driven state that other tests may leave behind); this test only
        # concerns the UI-refresh coalescing at the end of _parse_recording.
        recording = {'id': 'rec-1', 'title': 'Song'}
        with (
            patch('picard.track.run_track_metadata_processors'),
            patch.object(NonAlbumTrack, 'run_scripts'),
        ):
            nat._parse_recording(recording)
        album.update.assert_called_with(update_tracks=False)
        # album.update must never be called with update_tracks=True here.
        for call in album.update.call_args_list:
            self.assertNotEqual(call.kwargs.get('update_tracks'), True)
        nat.update.assert_called()
