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


from unittest.mock import (
    MagicMock,
    Mock,
)

from test.picardtestcase import PicardTestCase

from picard.file import File
from picard.isrcsubmit import ISRCSubmitManager

from picard.ui.enums import MainAction


def mock_succeed_submission(recordings_isrcs, handler):
    handler({}, None, None)


def mock_fail_submission(recordings_isrcs, handler):
    handler({}, MagicMock(), True)


def make_mock_track(track_number='1', title='', isrcs=None):
    """Create a mock track with metadata."""
    track = MagicMock()
    data = {'tracknumber': track_number, 'title': title}
    track.metadata.get = lambda key, default='': data.get(key, default)
    track.metadata.getall = lambda key: isrcs if key == 'isrc' and isrcs else []
    track.files = []
    return track


def make_mock_album(name, artist, tracks):
    """Create a mock album with tracks."""
    album = MagicMock()
    data = {'album': name, 'albumartist': artist}
    album.metadata.get = lambda key, default='': data.get(key, default)
    album.tracks = tracks
    return album


class ISRCSubmitTestCase(PicardTestCase):
    """Base test case for ISRCSubmitManager tests."""

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.isrcsubmit')
        self.mock_api = MagicMock()
        self.mock_api.submit_isrcs = Mock(wraps=mock_succeed_submission)
        self.manager = ISRCSubmitManager(self.mock_api)
        self.tagger.window = MagicMock()
        self.tagger.window.enable_action = MagicMock()


class ISRCSubmitManagerTest(ISRCSubmitTestCase):
    def test_add_new_isrcs(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], [])
        self.assertFalse(self.manager.is_submitted(file))
        self.assertEqual(1, self.manager.unsubmitted_count)

    def test_add_isrc_already_in_mb(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], ['USRC17607839'])
        self.assertTrue(self.manager.is_submitted(file))
        self.assertEqual(0, self.manager.unsubmitted_count)

    def test_add_mixed_new_and_existing(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839', 'GBAYE0000351'], ['USRC17607839'])
        self.assertFalse(self.manager.is_submitted(file))
        self.assertEqual(1, self.manager.unsubmitted_count)

    def test_add_invalid_isrc_skipped(self):
        file = object()
        self.manager.add(file, 'rec-1', ['INVALID', ''], [])
        self.assertTrue(self.manager.is_submitted(file))
        self.assertEqual(0, self.manager.unsubmitted_count)

    def test_add_normalizes_isrcs(self):
        file = object()
        self.manager.add(file, 'rec-1', ['us-rc1-76-07839'], [])
        entry = self.manager._entries[file]
        self.assertEqual({'USRC17607839'}, entry.new_isrcs)

    def test_add_case_insensitive_comparison(self):
        file = object()
        self.manager.add(file, 'rec-1', ['usrc17607839'], ['USRC17607839'])
        self.assertTrue(self.manager.is_submitted(file))

    def test_add_readd_with_all_in_mb_removes_entry(self):
        """Re-adding a file where all ISRCs are now in MB removes the entry."""
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], [])
        self.assertEqual(1, self.manager.unsubmitted_count)
        self.manager.add(file, 'rec-1', ['USRC17607839'], ['USRC17607839'])
        self.assertTrue(self.manager.is_submitted(file))
        self.assertEqual(0, self.manager.unsubmitted_count)

    def test_remove(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], [])
        self.assertEqual(1, self.manager.unsubmitted_count)
        self.manager.remove(file)
        self.assertEqual(0, self.manager.unsubmitted_count)
        self.assertTrue(self.manager.is_submitted(file))

    def test_remove_nonexistent(self):
        self.manager.remove(object())  # Should not raise
        self.assertEqual(0, self.manager.unsubmitted_count)

    def test_remove_album_clears_entries(self):
        album = MagicMock()
        file1 = MagicMock(album=album)
        file2 = MagicMock(album=album)
        self.manager.add(file1, 'rec-1', ['USRC17607839'], [])
        self.manager.add(file2, 'rec-2', ['GBAYE0000351'], [])
        self.assertEqual(2, self.manager.unsubmitted_count)
        self.manager.remove_album(album)
        self.assertEqual(0, self.manager.unsubmitted_count)

    def test_remove_album_only_affects_matching(self):
        album1 = MagicMock()
        album2 = MagicMock()
        file1 = MagicMock(album=album1)
        file2 = MagicMock(album=album2)
        self.manager.add(file1, 'rec-1', ['USRC17607839'], [])
        self.manager.add(file2, 'rec-2', ['GBAYE0000351'], [])
        self.manager.remove_album(album1)
        self.assertEqual(1, self.manager.unsubmitted_count)
        self.assertFalse(self.manager.is_submitted(file2))

    def test_remove_album_nonexistent(self):
        self.manager.remove_album(MagicMock())  # Should not raise
        self.assertEqual(0, self.manager.unsubmitted_count)

    def test_update_recording(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839', 'GBAYE0000351'], [])
        self.manager.update(file, 'rec-2', ['GBAYE0000351'])
        entry = self.manager._entries[file]
        self.assertEqual('rec-2', entry.recording_id)
        self.assertEqual({'USRC17607839'}, entry.new_isrcs)

    def test_update_all_known(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], [])
        self.manager.update(file, 'rec-2', ['USRC17607839'])
        self.assertTrue(self.manager.is_submitted(file))
        self.assertEqual(0, self.manager.unsubmitted_count)

    def test_update_nonexistent(self):
        self.manager.update(object(), 'rec-1', [])  # Should not raise

    def test_submit_success(self):
        file1 = object()
        file2 = object()
        self.manager.add(file1, 'rec-1', ['USRC17607839'], [])
        self.manager.add(file2, 'rec-2', ['GBAYE0000351'], [])
        self.manager.submit()
        self.mock_api.submit_isrcs.assert_called_once()
        payload = self.mock_api.submit_isrcs.call_args[0][0]
        self.assertIn('rec-1', payload)
        self.assertIn('rec-2', payload)
        self.assertTrue(self.manager.is_submitted(file1))
        self.assertTrue(self.manager.is_submitted(file2))
        self.assertEqual(0, self.manager.unsubmitted_count)

    def test_submit_failure(self):
        self.mock_api.submit_isrcs = Mock(wraps=mock_fail_submission)
        self.manager = ISRCSubmitManager(self.mock_api)
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], [])
        self.manager.submit()
        self.assertFalse(self.manager.is_submitted(file))
        self.assertEqual(1, self.manager.unsubmitted_count)

    def test_submit_empty(self):
        self.manager.submit()
        self.mock_api.submit_isrcs.assert_not_called()

    def test_check_unsubmitted_enables_action(self):
        self.manager.add(object(), 'rec-1', ['USRC17607839'], [])
        self.tagger.window.enable_action.assert_called_with(MainAction.SUBMIT_ISRC, True)

    def test_check_unsubmitted_disables_action(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], [])
        self.manager.remove(file)
        self.tagger.window.enable_action.assert_called_with(MainAction.SUBMIT_ISRC, False)

    def test_multiple_files_same_recording(self):
        self.manager.add(object(), 'rec-1', ['USRC17607839'], [])
        self.manager.add(object(), 'rec-1', ['GBAYE0000351'], [])
        pending = self.manager._pending_isrcs()
        self.assertIn('USRC17607839', pending['rec-1'])
        self.assertIn('GBAYE0000351', pending['rec-1'])

    def test_pending_isrcs_with_filter(self):
        self.manager.add(object(), 'rec-1', ['USRC17607839', 'GBAYE0000351'], [])
        result = self.manager._pending_isrcs(isrcs_to_submit={'USRC17607839'})
        self.assertEqual(['USRC17607839'], result['rec-1'])

    def test_pending_isrcs_filter_excludes_all(self):
        self.manager.add(object(), 'rec-1', ['USRC17607839'], [])
        result = self.manager._pending_isrcs(isrcs_to_submit={'GBAYE0000351'})
        self.assertNotIn('rec-1', result)


class FindDuplicateIsrcsTest(ISRCSubmitTestCase):
    def test_no_duplicates(self):
        self.manager.add(object(), 'rec-1', ['USRC17607839'], [])
        self.manager.add(object(), 'rec-2', ['GBAYE0000351'], [])
        self.assertEqual(set(), self.manager.find_duplicate_isrcs())

    def test_same_isrc_different_recordings(self):
        self.manager.add(object(), 'rec-1', ['USRC17607839'], [])
        self.manager.add(object(), 'rec-2', ['USRC17607839'], [])
        self.assertEqual({'USRC17607839'}, self.manager.find_duplicate_isrcs())

    def test_same_isrc_same_recording(self):
        self.manager.add(object(), 'rec-1', ['USRC17607839'], [])
        self.manager.add(object(), 'rec-1', ['USRC17607839'], [])
        self.assertEqual(set(), self.manager.find_duplicate_isrcs())

    def test_ignores_submitted(self):
        file1 = object()
        self.manager.add(file1, 'rec-1', ['USRC17607839'], [])
        self.manager.add(object(), 'rec-2', ['USRC17607839'], [])
        self.manager._entries[file1].new_isrcs = set()
        self.assertEqual(set(), self.manager.find_duplicate_isrcs())


class CheckTrackSubmittableTest(PicardTestCase):
    _check = staticmethod(ISRCSubmitManager.check_track_submittable)

    def test_new_isrcs_no_duplicates(self):
        submittable, reason = self._check(None, {'USRC17607839'}, [], set())
        self.assertTrue(submittable)
        self.assertEqual('', reason)

    def test_new_isrcs_with_duplicates(self):
        submittable, reason = self._check(None, {'USRC17607839'}, [], {'USRC17607839'})
        self.assertFalse(submittable)
        self.assertIn('different recordings', reason)

    def test_existing_isrcs_no_new(self):
        submittable, reason = self._check(None, set(), ['USRC17607839'], set())
        self.assertFalse(submittable)
        self.assertIn('already submitted', reason)

    def test_no_isrcs_at_all(self):
        track = MagicMock(files=[])
        submittable, reason = self._check(track, set(), [], set())
        self.assertFalse(submittable)
        self.assertEqual('', reason)

    def test_file_has_multiple_isrcs(self):
        file_mock = MagicMock()
        file_mock.orig_metadata.getall.return_value = ['ISRC1', 'ISRC2']
        track = MagicMock(files=[file_mock])
        submittable, reason = self._check(track, set(), [], set())
        self.assertFalse(submittable)
        self.assertIn('multiple ISRCs', reason)

    def test_isrc_already_on_another_track(self):
        album_isrcs = {'USRC17607839': 'Other Track'}
        submittable, reason = self._check(None, {'USRC17607839'}, [], set(), album_isrcs)
        self.assertFalse(submittable)
        self.assertIn('another track', reason)

    def test_isrc_on_same_track_is_ok(self):
        album_isrcs = {'USRC17607839': 'This Track'}
        submittable, reason = self._check(None, {'GBAYE0000351'}, ['USRC17607839'], set(), album_isrcs)
        self.assertTrue(submittable)
        self.assertEqual('', reason)


class PendingDetailsTest(ISRCSubmitTestCase):
    def _add_file_to_album(self, album, track, recording_id, isrcs):
        """Add a mock file linked to a track/album with pending ISRCs."""
        file = MagicMock(parent_item=track, album=album)
        self.manager.add(file, recording_id, isrcs, [])
        return file

    def test_basic(self):
        track1 = make_mock_track('1', 'Song One')
        track2 = make_mock_track('2', 'Song Two', ['USRC17607839'])
        album = make_mock_album('Test Album', 'Test Artist', [track1, track2])
        self._add_file_to_album(album, track1, 'rec-1', ['GBAYE0000351'])

        details = self.manager.pending_details()
        tracks = details[('Test Album', 'Test Artist')]
        self.assertEqual(2, len(tracks))
        self.assertEqual('1', tracks[0].track_number)
        self.assertTrue(tracks[0].submittable)
        self.assertEqual(['GBAYE0000351'], tracks[0].new_isrcs)
        self.assertEqual('2', tracks[1].track_number)
        self.assertFalse(tracks[1].submittable)

    def test_sorted_by_track_number(self):
        track3 = make_mock_track('3', 'Third')
        track1 = make_mock_track('1', 'First')
        track2 = make_mock_track('2', 'Second')
        album = make_mock_album('Album', 'Artist', [track3, track1, track2])
        self._add_file_to_album(album, track3, 'rec-3', ['USRC17607839'])

        details = self.manager.pending_details()
        tracks = details[('Album', 'Artist')]
        self.assertEqual(['1', '2', '3'], [t.track_number for t in tracks])

    def test_duplicate_isrc_not_submittable(self):
        track1 = make_mock_track('1', 'Song One')
        track2 = make_mock_track('2', 'Song Two')
        album = make_mock_album('Album', 'Artist', [track1, track2])
        self._add_file_to_album(album, track1, 'rec-1', ['USRC17607839'])
        self._add_file_to_album(album, track2, 'rec-2', ['USRC17607839'])

        details = self.manager.pending_details()
        tracks = details[('Album', 'Artist')]
        for t in tracks:
            if t.new_isrcs:
                self.assertFalse(t.submittable)
                self.assertIn('different recordings', t.disabled_reason)


class ISRCUpdateTest(PicardTestCase):
    """Tests for File.isrc_update() interaction with ISRCSubmitManager."""

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.isrcsubmit')
        self.patch_tagger_instance('picard.item')
        self.mock_api = MagicMock()
        self.manager = ISRCSubmitManager(self.mock_api)
        self.tagger.isrc_submit_manager = self.manager
        self.tagger.window = MagicMock()
        self.tagger.window.enable_action = MagicMock()
        self._tracks = []

    def _make_file_with_track(self, file_isrcs, mb_isrcs, recording_id='rec-1'):
        """Create a File with a mock parent track."""
        file = File('test.mp3')
        file.orig_metadata['isrc'] = file_isrcs
        track = MagicMock()
        track.can_link_fingerprint = True
        track.orig_metadata = MagicMock()
        track.orig_metadata.__getitem__ = lambda self, key: recording_id if key == 'musicbrainz_recordingid' else ''
        track.orig_metadata.getall = lambda key: mb_isrcs if key == 'isrc' else []
        file.parent_item = track
        self._tracks.append(track)
        return file

    def test_single_new_isrc_submitted(self):
        """File with a single new ISRC gets registered for submission."""
        file = self._make_file_with_track(['CARE19900179'], [])
        file.isrc_update()
        self.assertFalse(self.manager.is_submitted(file))
        self.assertEqual(1, self.manager.unsubmitted_count)

    def test_multiple_isrcs_with_new_one_submitted(self):
        """File with multiple ISRCs where one is new should still register.

        Regression test: previously, files with more than one ISRC in
        orig_metadata were silently skipped, preventing submission of new
        ISRCs from files that already had ISRCs from a previous tagging.
        """
        mb_isrcs = ['USRE10900199', 'USRE11100413']
        file_isrcs = ['USRE10900199', 'USRE11100413', 'CARE19900180']
        file = self._make_file_with_track(file_isrcs, mb_isrcs, 'rec-2')
        file.isrc_update()
        self.assertFalse(self.manager.is_submitted(file))
        self.assertEqual(1, self.manager.unsubmitted_count)
        entry = self.manager._entries[file]
        self.assertEqual({'CARE19900180'}, entry.new_isrcs)

    def test_multiple_isrcs_all_in_mb_not_submitted(self):
        """File with multiple ISRCs that are all already in MB is not submitted."""
        mb_isrcs = ['USRE10900199', 'USRE11100413']
        file_isrcs = ['USRE10900199', 'USRE11100413']
        file = self._make_file_with_track(file_isrcs, mb_isrcs)
        file.isrc_update()
        self.assertTrue(self.manager.is_submitted(file))
        self.assertEqual(0, self.manager.unsubmitted_count)
