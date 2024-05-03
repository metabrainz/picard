# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Laurent Monin
# Copyright (C) 2020, 2022 Philipp Wolfer
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

from picard.acoustid.manager import (
    FINGERPRINT_MAX_ALLOWED_LENGTH_DIFF_MS,
    AcoustIDManager,
    Submission,
)
from picard.file import File
from picard.metadata import Metadata


def mock_succeed_submission(*args, **kwargs):
    # Run the callback
    args[1]({}, None, None)


def mock_fail_submission(*args, **kwargs):
    # Run the callback with error arguments
    args[1]({}, MagicMock(), True)


FINGERPRINT_SIZE = 4000


def dummy_file(i):
    file = File('foo%d.flac' % i)
    file.acoustid_fingerprint = 'Z' * FINGERPRINT_SIZE
    file.acoustid_length = 120
    file.metadata = Metadata(length=file.acoustid_length * 1000)
    return file


class AcoustIDManagerTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values({
            "clear_existing_tags": False,
            "compare_ignore_tags": []
        })
        self.mock_api_helper = MagicMock()
        self.mock_api_helper.submit_acoustid_fingerprints = Mock(wraps=mock_succeed_submission)
        self.acoustidmanager = AcoustIDManager(self.mock_api_helper)
        self.tagger.window = MagicMock()
        self.tagger.window.action_enabled = MagicMock()
        AcoustIDManager.MAX_PAYLOAD = FINGERPRINT_SIZE * 5
        AcoustIDManager.MAX_ATTEMPTS = 3

    def _add_unsubmitted_files(self, count):
        files = []
        for i in range(0, count):
            file = dummy_file(i)
            files.append(file)
            self.acoustidmanager.add(file, None)
            self.acoustidmanager.update(file, '00000000-0000-0000-0000-%012d' % i)
            self.assertFalse(self.acoustidmanager.is_submitted(file))
        return files

    def test_add_invalid(self):
        file = File('foo.flac')
        self.acoustidmanager.add(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.action_enabled.assert_not_called()

    def test_add_and_update(self):
        file = dummy_file(0)
        self.acoustidmanager.add(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.action_enabled.assert_called_with('submit_acoustid_action', False)
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000002')
        self.tagger.window.action_enabled.assert_called_with('submit_acoustid_action', True)
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.action_enabled.assert_called_with('submit_acoustid_action', False)

    def test_add_and_remove(self):
        file = dummy_file(0)
        self.acoustidmanager.add(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.action_enabled.assert_called_with('submit_acoustid_action', False)
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000002')
        self.tagger.window.action_enabled.assert_called_with('submit_acoustid_action', True)
        self.acoustidmanager.remove(file)
        self.tagger.window.action_enabled.assert_called_with('submit_acoustid_action', False)

    def test_is_submitted(self):
        file = dummy_file(0)
        self.assertTrue(self.acoustidmanager.is_submitted(file))
        self.acoustidmanager.add(file, '00000000-0000-0000-0000-000000000001')
        self.assertTrue(self.acoustidmanager.is_submitted(file))
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000002')
        self.assertFalse(self.acoustidmanager.is_submitted(file))
        self.acoustidmanager.update(file, '')
        self.assertTrue(self.acoustidmanager.is_submitted(file))

    def test_submit_single_batch(self):
        f = self._add_unsubmitted_files(1)[0]
        self.acoustidmanager.submit()
        self.assertEqual(self.mock_api_helper.submit_acoustid_fingerprints.call_count, 1)
        self.assertEqual(
            f.acoustid_fingerprint,
            self.mock_api_helper.submit_acoustid_fingerprints.call_args[0][0][0].fingerprint
        )

    def test_submit_multi_batch(self):
        files = self._add_unsubmitted_files(int(AcoustIDManager.MAX_PAYLOAD / FINGERPRINT_SIZE) * 2)
        self.acoustidmanager.submit()
        self.assertEqual(self.mock_api_helper.submit_acoustid_fingerprints.call_count, 3)
        for f in files:
            self.assertTrue(self.acoustidmanager.is_submitted(f))

    def test_submit_multi_batch_failure(self):
        self.mock_api_helper.submit_acoustid_fingerprints = Mock(wraps=mock_fail_submission)
        files = self._add_unsubmitted_files(int(AcoustIDManager.MAX_PAYLOAD / FINGERPRINT_SIZE) * 2)
        self.acoustidmanager.submit()
        self.assertEqual(self.mock_api_helper.submit_acoustid_fingerprints.call_count, 8)
        for f in files:
            self.assertFalse(self.acoustidmanager.is_submitted(f))


class SubmissionTest(PicardTestCase):

    def test_init(self):
        fingerprint = 'abc'
        duration = 42
        recordingid = 'rec1'
        metadata = Metadata({
            'musicip_puid': 'puid1'
        })
        submission = Submission(fingerprint, duration, recordingid, metadata)
        self.assertEqual(fingerprint, submission.fingerprint)
        self.assertEqual(duration, submission.duration)
        self.assertEqual(recordingid, submission.recordingid)
        self.assertEqual(recordingid, submission.orig_recordingid)
        self.assertEqual(metadata, submission.metadata)
        self.assertEqual(metadata['musicip_puid'], submission.puid)
        self.assertEqual(0, submission.attempts)

    def test_bool(self):
        self.assertTrue(bool(Submission('foo', 1)))
        self.assertTrue(bool(Submission('foo', 0)))
        self.assertFalse(bool(Submission('foo', None)))
        self.assertFalse(bool(Submission(None, 1)))
        self.assertFalse(bool(Submission('', 1)))

    def test_valid_duration(self):
        duration_s = 342
        duration_ms = duration_s * 1000
        metadata = Metadata()
        submission = Submission('abc', duration_s, metadata=metadata)
        self.assertFalse(submission.valid_duration)
        metadata.length = duration_ms
        self.assertTrue(submission.valid_duration)
        metadata.length = duration_ms + FINGERPRINT_MAX_ALLOWED_LENGTH_DIFF_MS
        self.assertTrue(submission.valid_duration)
        metadata.length = duration_ms - FINGERPRINT_MAX_ALLOWED_LENGTH_DIFF_MS
        self.assertTrue(submission.valid_duration)
        metadata.length = duration_ms + 1 + FINGERPRINT_MAX_ALLOWED_LENGTH_DIFF_MS
        self.assertFalse(submission.valid_duration)
        metadata.length = duration_ms - 1 - FINGERPRINT_MAX_ALLOWED_LENGTH_DIFF_MS
        self.assertFalse(submission.valid_duration)

    def test_valid_duration_no_metadata(self):
        submission = Submission('abc', 342)
        self.assertTrue(submission.valid_duration)

    def test_init_no_metadata(self):
        submission = Submission('abc', 42)
        self.assertIsNone(submission.metadata)
        self.assertEqual('', submission.puid)

    def test_is_submitted_no_recording_id(self):
        submission = Submission('abc', 42)
        self.assertTrue(submission.is_submitted)
        submission.recordingid = 'rec1'
        self.assertFalse(submission.is_submitted)

    def test_is_submitted_move_recording_id(self):
        submission = Submission('abc', 42, recordingid='rec1')
        self.assertTrue(submission.is_submitted)
        submission.recordingid = 'rec2'
        self.assertFalse(submission.is_submitted)

    def test_args_with_mbid(self):
        submission = Submission('abc', 42, recordingid='rec1')
        expected = {
            'fingerprint': 'abc',
            'duration': '42',
            'mbid': 'rec1',
        }
        self.assertEqual(expected, submission.args)

    def test_args_with_mbid_with_puid(self):
        metadata = Metadata(
            musicip_puid='p1'
        )
        metadata.length = 42000
        submission = Submission('abc', 42, recordingid='rec1', metadata=metadata)
        expected = {
            'fingerprint': 'abc',
            'duration': '42',
            'mbid': 'rec1',
            'puid': 'p1'
        }
        self.assertEqual(expected, submission.args)

    def test_args_with_invalid_duration(self):
        metadata = Metadata({
            'title': 'The Track',
            'artist': 'The Artist',
            'album': 'The Album',
            'albumartist': 'The Album Artist',
            'tracknumber': '4',
            'discnumber': '2',
            'date': '2022-01-22',
        })
        metadata.length = 500000
        submission = Submission('abc', 42, recordingid='rec1', metadata=metadata)
        expected = {
            'fingerprint': 'abc',
            'duration': '42',
            'track': metadata['title'],
            'artist': metadata['artist'],
            'album': metadata['album'],
            'albumartist': metadata['albumartist'],
            'trackno': metadata['tracknumber'],
            'discno': metadata['discnumber'],
            'year': '2022',
        }
        self.assertEqual(expected, submission.args)

    def test_args_without_mbid(self):
        metadata = Metadata({
            'title': 'The Track',
            'artist': 'The Artist',
            'album': 'The Album',
            'albumartist': 'The Album Artist',
            'tracknumber': '4',
            'discnumber': '2',
            'date': '2022-01-22',
        })
        metadata.length = 42000
        submission = Submission('abc', 42, recordingid=None, metadata=metadata)
        expected = {
            'fingerprint': 'abc',
            'duration': '42',
            'track': metadata['title'],
            'artist': metadata['artist'],
            'album': metadata['album'],
            'albumartist': metadata['albumartist'],
            'trackno': metadata['tracknumber'],
            'discno': metadata['discnumber'],
            'year': '2022',
        }
        self.assertEqual(expected, submission.args)

    def test_args_year(self):
        metadata = Metadata({
            'year': '2022',
        })
        metadata.length = 500000
        submission = Submission('abc', 42, recordingid='rec1', metadata=metadata)
        args = submission.args
        self.assertEqual('2022', args['year'])

    def test_args_invalid_year(self):
        metadata = Metadata({
            'year': 'NaN',
        })
        metadata.length = 500000
        submission = Submission('abc', 42, recordingid='rec1', metadata=metadata)
        self.assertNotIn('year', submission.args)

    def test_len_mbid_puid(self):
        fingerprint = 'abc' * 30
        puid = 'p1'
        recordingid = 'rec1'
        duration = 42
        metadata = Metadata(
            musicip_puid=puid
        )
        metadata.length = 42000
        submission = Submission(fingerprint, 42, recordingid=recordingid, metadata=metadata)
        expected_min_length = len('&fingerprint=%s&duration=%s&mbid=%s&puid=%s' % (fingerprint, duration, recordingid, puid))
        self.assertGreater(len(submission), expected_min_length)

    def test_len_no_mbid(self):
        metadata = Metadata({
            'title': 'The Track',
            'artist': 'The Artist',
            'album': 'The Album',
            'albumartist': 'The Album Artist',
            'tracknumber': '4',
            'discnumber': '2',
            'date': '2022-01-22',
        })
        metadata.length = 500000
        submission = Submission('abc', 42, recordingid='rec1', metadata=metadata)
        expected_args = {
            'fingerprint': 'abc',
            'duration': '42',
            'track': metadata['title'],
            'artist': metadata['artist'],
            'album': metadata['album'],
            'albumartist': metadata['albumartist'],
            'trackno': metadata['tracknumber'],
            'discno': metadata['discnumber'],
            'year': '2022',
        }
        expected_min_length = len('&'.join(('='.join([k, v]) for k, v in expected_args.items())))
        self.assertGreater(len(submission), expected_min_length)
