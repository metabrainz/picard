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


from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QColor,
    QTextBlockFormat,
    QTextCursor,
)

import pytest

from picard.ui.playground import Playground


MATCH_COLOR = QColor(0, 255, 0)
SKIP_COLOR = QColor(255, 0, 0)


class MockPlayground(Playground):
    """Playground subclass with deterministic colors for testing."""

    def _get_fmt_match(self):
        fmt = QTextBlockFormat()
        fmt.setBackground(MATCH_COLOR)
        return fmt

    def _get_fmt_skip(self):
        fmt = QTextBlockFormat()
        fmt.setBackground(SKIP_COLOR)
        return fmt


@pytest.fixture()
def playground(qapp):
    p = MockPlayground("Test:")
    p._text_edit.setPlainText("foo\nbar\nbaz\n")
    return p


def _get_block_background(playground, lineno):
    """Get the background color of a specific block (line) in the playground."""
    block = playground._text_edit.document().findBlockByNumber(lineno)
    cursor = QTextCursor(block)
    return cursor.blockFormat().background().color()


def _has_background(playground, lineno):
    """Check if a specific block has a non-default background set."""
    block = playground._text_edit.document().findBlockByNumber(lineno)
    cursor = QTextCursor(block)
    return cursor.blockFormat().background().style() != Qt.BrushStyle.NoBrush


class TestPlayground:
    def test_update_with_none_clears_all_lines(self, playground):
        """When match_function is None, all lines should have no background."""
        # First apply some coloring
        playground.update(lambda line: line == "foo")
        assert _has_background(playground, 0)

        # Now clear with None
        playground.update(None)
        for lineno in range(3):
            assert not _has_background(playground, lineno)

    def test_update_matching_lines_get_match_color(self, playground):
        """Lines that match should get the match color."""
        playground.update(lambda line: line == "foo")
        assert _get_block_background(playground, 0) == MATCH_COLOR

    def test_update_non_matching_lines_get_skip_color(self, playground):
        """Lines that don't match should get the skip color."""
        playground.update(lambda line: line == "foo")
        assert _get_block_background(playground, 1) == SKIP_COLOR

    def test_update_empty_lines_get_cleared(self, qapp):
        """Empty lines should always get cleared regardless of match function."""
        playground = MockPlayground("Test:")
        playground._text_edit.setPlainText("foo\n\nbaz")
        playground.update(lambda line: True)
        assert not _has_background(playground, 1)
        assert _has_background(playground, 0)
        assert _has_background(playground, 2)

    def test_update_whitespace_only_lines_treated_as_empty(self, qapp):
        """Lines with only whitespace should be treated as empty."""
        playground = MockPlayground("Test:")
        playground._text_edit.setPlainText("foo\n   \nbaz")
        playground.update(lambda line: True)
        assert not _has_background(playground, 1)

    def test_update_all_match(self, playground):
        """When all lines match, they should all get the match color."""
        playground.update(lambda line: True)
        for lineno in range(3):
            assert _get_block_background(playground, lineno) == MATCH_COLOR

    def test_update_none_match(self, playground):
        """When no lines match, they should all get the skip color."""
        playground.update(lambda line: False)
        for lineno in range(3):
            assert _get_block_background(playground, lineno) == SKIP_COLOR

    def test_signals_not_emitted_during_update(self, playground):
        """The update should block signals to avoid recursive textChanged triggers."""
        signal_count = []

        def on_text_changed():
            signal_count.append(1)

        playground.textChanged.connect(on_text_changed)
        playground.update(lambda line: True)
        assert len(signal_count) == 0

    def test_set_error_shows_label(self, playground):
        """set_error should show the error label with the message."""
        playground.set_error("Test error")
        assert not playground._error_label.isHidden()
        assert playground._error_label.text() == "Test error"

    def test_clear_error_hides_label(self, playground):
        """clear_error should hide the error label."""
        playground.set_error("Test error")
        playground.clear_error()
        assert playground._error_label.isHidden()

    def test_error_label_hidden_by_default(self, playground):
        """Error label should be hidden initially."""
        assert playground._error_label.isHidden()

    def test_text_changed_signal(self, playground):
        """Typing in the text area should emit textChanged."""
        signal_count = []
        playground.textChanged.connect(lambda: signal_count.append(1))
        playground._text_edit.setPlainText("new text")
        assert len(signal_count) > 0
