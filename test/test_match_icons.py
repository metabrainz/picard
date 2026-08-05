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

import pytest

from picard.ui.match_icons import (
    _THRESHOLDS,
    LOW_THRESHOLD,
    NUM_LEVELS,
    NUM_STEPS,
    similarity_to_level,
)


# ---------------------------------------------------------------------------
# similarity_to_level
# ---------------------------------------------------------------------------


class TestSimilarityToLevel:
    @pytest.mark.parametrize(
        "similarity,expected_level",
        [
            # Below low threshold → level 0
            (0.00, 0),
            (0.30, 0),
            (0.50, 0),
            (0.5624, 0),
            # At and above low threshold → level 1
            (0.5625, 1),
            (0.60, 1),
            (0.67, 1),
            # Level 2
            (0.68, 2),
            (0.75, 2),
            # Level 3
            (0.80, 3),
            (0.85, 3),
            # Level 4
            (0.90, 4),
            (0.95, 4),
            (0.99, 4),
            # Only exactly 1.0 → level 5 (top)
            (1.00, 5),
        ],
    )
    def test_level_mapping(self, similarity, expected_level):
        result = similarity_to_level(similarity)
        assert result == expected_level, f"similarity_to_level({similarity}) = {result}, expected {expected_level}"

    def test_below_one_never_returns_top_level(self):
        """Any value strictly below 1.0 must never map to the top level."""
        top = NUM_LEVELS - 1
        for pct in range(0, 100):
            sim = pct / 100.0
            result = similarity_to_level(sim)
            assert result < top, f"similarity_to_level({sim}) returned top level"

    def test_exactly_one_returns_top_level(self):
        assert similarity_to_level(1.0) == NUM_LEVELS - 1

    def test_above_one_returns_top_level(self):
        assert similarity_to_level(1.5) == NUM_LEVELS - 1

    def test_distinct_level_count(self):
        """Verify the number of distinct levels matches NUM_LEVELS."""
        all_levels = {similarity_to_level(p / 100.0) for p in range(101)}
        all_levels.add(similarity_to_level(1.0))
        assert len(all_levels) == NUM_LEVELS

    def test_num_levels(self):
        assert NUM_LEVELS == 6

    def test_thresholds_count(self):
        """_THRESHOLDS should have NUM_STEPS - 1 entries."""
        assert len(_THRESHOLDS) == NUM_STEPS - 1

    def test_monotonic_levels(self):
        """Higher similarity should never produce a lower level."""
        prev = 0
        for pct in range(0, 101):
            sim = pct / 100.0
            level = similarity_to_level(sim)
            assert level >= prev, f"Non-monotonic at {sim}: {level} < {prev}"
            prev = level

    def test_low_threshold_boundary(self):
        """Values just below and at LOW_THRESHOLD should differ."""
        below = similarity_to_level(LOW_THRESHOLD - 0.0001)
        at = similarity_to_level(LOW_THRESHOLD)
        assert below == 0
        assert at == 1
