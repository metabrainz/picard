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

from test.picardtestcase import PicardTestCase

from picard.metadata import Metadata

from picard.ui.player.listenbrainz import PreparedSubmission


class TestPreparedSubmissionService(PicardTestCase):
    def test_can_submit(self):
        metadata = Metadata()
        metadata.length = 20000  # milliseconds
        submission = PreparedSubmission(metadata, 0)
        self.assertFalse(submission.can_submit)

    def test_can_submit_after_half_playback(self):
        metadata = Metadata()
        metadata.length = 20000  # milliseconds
        submission = PreparedSubmission(metadata, 0)
        submission.elapsed_seconds = 9
        self.assertFalse(submission.can_submit)
        submission.elapsed_seconds = 10
        self.assertTrue(submission.can_submit)

    def test_can_submit_after_4_minutes(self):
        metadata = Metadata()
        metadata.length = 500000  # milliseconds
        submission = PreparedSubmission(metadata, 0)
        submission.elapsed_seconds = 239
        self.assertFalse(submission.can_submit)
        submission.elapsed_seconds = 240
        self.assertTrue(submission.can_submit)

    def test_can_submit_not_if_submitted(self):
        metadata = Metadata()
        metadata.length = 20000  # milliseconds
        submission = PreparedSubmission(metadata, 0)
        submission.elapsed_seconds = 12
        self.assertTrue(submission.can_submit)
        submission.submitted = True
        self.assertFalse(submission.can_submit)

    def test_can_submit_not_zero_seconds(self):
        metadata = Metadata()
        submission = PreparedSubmission(metadata, 0)
        self.assertFalse(submission.can_submit)
        metadata.length = 999
        self.assertFalse(submission.can_submit)
