# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Laurent Monin
# Copyright (C) 2020 Philipp Wolfer
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

from picard import config
from picard.acoustid.manager import AcoustIDManager
from picard.file import File


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
    return file


class AcoustIDManagerTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        config.setting = {
            "clear_existing_tags": False,
            "compare_ignore_tags": []
        }
        self.mock_api_helper = MagicMock()
        self.mock_api_helper.submit_acoustid_fingerprints = Mock(wraps=mock_succeed_submission)
        self.acoustidmanager = AcoustIDManager(self.mock_api_helper)
        self.tagger.window = MagicMock()
        self.tagger.window.enable_submit = MagicMock()
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
        self.tagger.window.enable_submit.assert_not_called()

    def test_add_and_update(self):
        file = dummy_file(0)
        self.acoustidmanager.add(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.enable_submit.assert_called_with(False)
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000002')
        self.tagger.window.enable_submit.assert_called_with(True)
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.enable_submit.assert_called_with(False)

    def test_add_and_remove(self):
        file = dummy_file(0)
        self.acoustidmanager.add(file, '00000000-0000-0000-0000-000000000001')
        self.tagger.window.enable_submit.assert_called_with(False)
        self.acoustidmanager.update(file, '00000000-0000-0000-0000-000000000002')
        self.tagger.window.enable_submit.assert_called_with(True)
        self.acoustidmanager.remove(file)
        self.tagger.window.enable_submit.assert_called_with(False)

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
