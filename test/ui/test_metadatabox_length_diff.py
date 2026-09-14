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


from test.picardtestcase import PicardTestCase

from picard.ui.metadatabox import (
    DiffColors,
    MetadataBox,
)
from picard.ui.metadatabox.tagdiff import TagDiff


_COLORS = DiffColors(text='#000000', placeholder='#888888', removed_bg='#f00', added_bg='#0f0')


class _FakeMetadataBox:
    """Minimal stand-in exposing what _compute_diff_html needs."""

    LOOKUP_TAGS = MetadataBox.LOOKUP_TAGS


def _compute(tag_diff):
    # Call the real method as an unbound function with a lightweight self.
    MetadataBox._compute_diff_html(_FakeMetadataBox(), tag_diff, _COLORS)


class TestLengthDiffTolerance(PicardTestCase):
    """Regression tests for PICARD-3442.

    The ~length diff in the metadata box must honour the
    ignore_track_duration_difference_under tolerance: differences under the
    tolerance must not be highlighted, while larger differences must be.
    """

    def _make_tag_diff(self, old_ms, new_ms, tolerance_s):
        tag_diff = TagDiff(max_length_diff=tolerance_s)
        tag_diff.add('~length', str(old_ms), str(new_ms), removable=False, readonly=True)
        tag_diff.update_tag_names()
        return tag_diff

    def test_length_diff_under_tolerance_not_highlighted(self):
        # 1 second difference, tolerance 2 seconds -> no diff HTML
        tag_diff = self._make_tag_diff(60000, 61000, tolerance_s=2)
        _compute(tag_diff)
        self.assertNotIn('~length', tag_diff.diff_html)

    def test_length_diff_above_tolerance_highlighted(self):
        # 5 second difference, tolerance 2 seconds -> diff HTML present
        tag_diff = self._make_tag_diff(60000, 65000, tolerance_s=2)
        _compute(tag_diff)
        self.assertIn('~length', tag_diff.diff_html)

    def test_length_diff_equal_values_not_highlighted(self):
        tag_diff = self._make_tag_diff(60000, 60000, tolerance_s=2)
        _compute(tag_diff)
        self.assertNotIn('~length', tag_diff.diff_html)

    def test_length_diff_zero_tolerance_highlights_any_difference(self):
        # Tolerance 0 -> any difference is highlighted (default "always" behavior)
        tag_diff = self._make_tag_diff(60000, 61000, tolerance_s=0)
        _compute(tag_diff)
        self.assertIn('~length', tag_diff.diff_html)
