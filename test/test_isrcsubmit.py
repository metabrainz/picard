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

from picard.isrcsubmit import ISRCSubmitManager

from picard.ui.enums import MainAction


def mock_succeed_submission(recordings_isrcs, handler):
    handler({}, None, None)


def mock_fail_submission(recordings_isrcs, handler):
    handler({}, MagicMock(), True)


class ISRCSubmitManagerTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.isrcsubmit')
        self.mock_api = MagicMock()
        self.mock_api.submit_isrcs = Mock(wraps=mock_succeed_submission)
        self.manager = ISRCSubmitManager(self.mock_api)
        self.tagger.window = MagicMock()
        self.tagger.window.enable_action = MagicMock()

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

    def test_remove(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], [])
        self.assertEqual(1, self.manager.unsubmitted_count)
        self.manager.remove(file)
        self.assertEqual(0, self.manager.unsubmitted_count)
        self.assertTrue(self.manager.is_submitted(file))

    def test_remove_nonexistent(self):
        file = object()
        self.manager.remove(file)  # Should not raise
        self.assertEqual(0, self.manager.unsubmitted_count)

    def test_update_recording(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839', 'GBAYE0000351'], [])
        self.assertEqual(1, self.manager.unsubmitted_count)
        # Re-match to rec-2 which already has one of the ISRCs
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
        file = object()
        self.manager.update(file, 'rec-1', [])  # Should not raise

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
        # After success, all should be submitted
        self.assertTrue(self.manager.is_submitted(file1))
        self.assertTrue(self.manager.is_submitted(file2))
        self.assertEqual(0, self.manager.unsubmitted_count)

    def test_submit_failure(self):
        self.mock_api.submit_isrcs = Mock(wraps=mock_fail_submission)
        self.manager = ISRCSubmitManager(self.mock_api)
        self.tagger.window = MagicMock()
        self.tagger.window.enable_action = MagicMock()
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], [])
        self.manager.submit()
        # On failure, entries remain unsubmitted
        self.assertFalse(self.manager.is_submitted(file))
        self.assertEqual(1, self.manager.unsubmitted_count)

    def test_submit_empty(self):
        self.manager.submit()
        self.mock_api.submit_isrcs.assert_not_called()

    def test_check_unsubmitted_enables_action(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], [])
        self.tagger.window.enable_action.assert_called_with(MainAction.SUBMIT_ISRC, True)

    def test_check_unsubmitted_disables_action(self):
        file = object()
        self.manager.add(file, 'rec-1', ['USRC17607839'], [])
        self.manager.remove(file)
        self.tagger.window.enable_action.assert_called_with(MainAction.SUBMIT_ISRC, False)

    def test_multiple_files_same_recording(self):
        file1 = object()
        file2 = object()
        self.manager.add(file1, 'rec-1', ['USRC17607839'], [])
        self.manager.add(file2, 'rec-1', ['GBAYE0000351'], [])
        pending = self.manager._pending_isrcs()
        self.assertIn('rec-1', pending)
        # Both ISRCs should be included for the same recording
        self.assertIn('USRC17607839', pending['rec-1'])
        self.assertIn('GBAYE0000351', pending['rec-1'])


class FindDuplicateIsrcsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.isrcsubmit')
        self.mock_api = MagicMock()
        self.mock_api.submit_isrcs = Mock()
        self.manager = ISRCSubmitManager(self.mock_api)
        self.tagger.window = MagicMock()
        self.tagger.window.enable_action = MagicMock()

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
        # Same recording is fine — not a duplicate
        self.assertEqual(set(), self.manager.find_duplicate_isrcs())

    def test_ignores_submitted(self):
        file1 = object()
        file2 = object()
        self.manager.add(file1, 'rec-1', ['USRC17607839'], [])
        self.manager.add(file2, 'rec-2', ['USRC17607839'], [])
        # Simulate submission of file1's ISRC
        self.manager._entries[file1].new_isrcs = set()
        self.assertEqual(set(), self.manager.find_duplicate_isrcs())


class CheckTrackSubmittableTest(PicardTestCase):
    def test_new_isrcs_no_duplicates(self):
        submittable, reason = ISRCSubmitManager.check_track_submittable(None, {'USRC17607839'}, [], set())
        self.assertTrue(submittable)
        self.assertEqual('', reason)

    def test_new_isrcs_with_duplicates(self):
        submittable, reason = ISRCSubmitManager.check_track_submittable(None, {'USRC17607839'}, [], {'USRC17607839'})
        self.assertFalse(submittable)
        self.assertIn('different recordings', reason)

    def test_existing_isrcs_no_new(self):
        submittable, reason = ISRCSubmitManager.check_track_submittable(None, set(), ['USRC17607839'], set())
        self.assertFalse(submittable)
        self.assertIn('already submitted', reason)

    def test_no_isrcs_at_all(self):
        track = MagicMock()
        track.files = []
        submittable, reason = ISRCSubmitManager.check_track_submittable(track, set(), [], set())
        self.assertFalse(submittable)
        self.assertEqual('', reason)

    def test_file_has_multiple_isrcs(self):
        file_mock = MagicMock()
        file_mock.orig_metadata.getall.return_value = ['ISRC1', 'ISRC2']
        track = MagicMock()
        track.files = [file_mock]
        submittable, reason = ISRCSubmitManager.check_track_submittable(track, set(), [], set())
        self.assertFalse(submittable)
        self.assertIn('multiple ISRCs', reason)
