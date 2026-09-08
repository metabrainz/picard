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


from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.ui.ratingwidget import RatingWidget


class RatingWidgetTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(
            setting={
                'rating_steps': 6,
                'submit_ratings': True,
            }
        )
        # RatingWidget is a QWidget and accesses the Tagger singleton via
        # tagger_instance(); patch it to the mock tagger.
        self.patch_tagger_instance('picard.ui.ratingwidget')
        self.tagger.mb_api = MagicMock()
        self.track = MagicMock()
        self.track.id = 'b9991644-7275-44db-bc43-fff6c6b4ce69'
        self.track.metadata = {'~rating': '0', 'title': 'Test Track'}
        self.track.files = []

    def test_update_track_submits_rating(self):
        # Regression test for PICARD-3425: RatingWidget referenced self.tagger,
        # which does not exist on a QWidget, so submitting a rating crashed with
        # AttributeError. It must use the Tagger singleton instead.
        widget = RatingWidget(self.track)
        widget._rating = 4
        widget._update_track()
        self.tagger.mb_api.submit_ratings.assert_called_once()
        ratings = self.tagger.mb_api.submit_ratings.call_args[0][0]
        self.assertEqual({('recording', self.track.id): 4}, ratings)

    def test_update_track_no_submit_when_disabled(self):
        self.set_config_values(setting={'rating_steps': 6, 'submit_ratings': False})
        widget = RatingWidget(self.track)
        widget._rating = 3
        widget._update_track()
        self.tagger.mb_api.submit_ratings.assert_not_called()

    def test_submitted_error_reports_via_tagger_window(self):
        widget = RatingWidget(self.track)
        widget._submitted(None, None, error=1)
        self.tagger.window.set_statusbar_message.assert_called_once()
