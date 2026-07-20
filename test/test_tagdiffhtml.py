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

from test.picardtestcase import PicardTestCase

from picard.ui.metadatabox.tagdiffhtml import (
    compute_diff,
    tokenize,
)


REMOVED_BG = 'rgba(255, 0, 0, 60)'
ADDED_BG = 'rgba(0, 255, 0, 60)'
TEXT_COLOR = '#b8860b'


def _hl_removed(text: str) -> str:
    return f'<span style="background-color: {REMOVED_BG};">{text}</span>'


def _hl_added(text: str) -> str:
    return f'<span style="background-color: {ADDED_BG};">{text}</span>'


def _wrap(inner: str) -> str:
    return f'<span style="color: {TEXT_COLOR};">{inner}</span>'


class TestTokenize(PicardTestCase):
    def test_simple_words(self):
        self.assertEqual(tokenize("hello world"), ["hello", " ", "world"])

    def test_punctuation_separated(self):
        self.assertEqual(tokenize("Rock'n'Roll!"), ["Rock", "'", "n", "'", "Roll", "!"])

    def test_whitespace_preserved(self):
        self.assertEqual(tokenize("a  b"), ["a", "  ", "b"])

    def test_empty_string(self):
        self.assertEqual(tokenize(""), [])

    def test_unicode(self):
        self.assertEqual(tokenize("Björk"), ["Björk"])

    def test_mixed_punctuation_and_words(self):
        self.assertEqual(
            tokenize("Hello, world! (test)"),
            ["Hello", ",", " ", "world", "!", " ", "(", "test", ")"],
        )


class TestComputeDiff(PicardTestCase):
    def test_identical_strings_returns_none(self):
        result = compute_diff("same", "same", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        self.assertEqual(result, (None, None))

    def test_empty_strings_returns_none(self):
        result = compute_diff("", "", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        self.assertEqual(result, (None, None))

    def test_completely_different_words(self):
        old_html, new_html = compute_diff("Mitchell", "Johnson", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # Words are too dissimilar (ratio < 0.5), entire tokens highlighted
        self.assertEqual(old_html, _wrap(_hl_removed("Mitchell")))
        self.assertEqual(new_html, _wrap(_hl_added("Johnson")))

    def test_similar_word_char_diff(self):
        # "Mitchell" vs "Mitchel" - similar enough for char-level diff
        old_html, new_html = compute_diff("Mitchell", "Mitchel", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # Should show char-level diff: the extra 'l' at the end is removed
        self.assertIn("Mitche", old_html)
        self.assertIn("Mitche", new_html)
        # The removed 'll' vs 'l' should be highlighted
        self.assertIn(REMOVED_BG, old_html)

    def test_apostrophe_change(self):
        # Typographic apostrophe replacement: only the quote chars differ
        old_html, new_html = compute_diff("Rock'n'Roll", "Rock\u2019n\u2019Roll", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # "Rock" and "Roll" and "n" should not be highlighted
        self.assertIn("Rock", old_html)
        self.assertIn("Roll", old_html)
        # The apostrophes should be highlighted (escape() converts ' to &#x27;)
        self.assertIn(_hl_removed("&#x27;"), old_html)
        self.assertIn(_hl_added("\u2019"), new_html)

    def test_word_added(self):
        old_html, new_html = compute_diff("The Beatles", "The Fab Beatles", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # "Fab " is added in new
        self.assertIn(_hl_added("Fab"), new_html)
        # "The" and "Beatles" should appear unchanged in both
        self.assertIn("The", old_html)
        self.assertIn("Beatles", old_html)
        self.assertIn("The", new_html)
        self.assertIn("Beatles", new_html)

    def test_word_removed(self):
        old_html, new_html = compute_diff("The Fab Beatles", "The Beatles", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # "Fab " is removed from old
        self.assertIn(_hl_removed("Fab"), old_html)
        self.assertIn("The", new_html)
        self.assertIn("Beatles", new_html)

    def test_multi_value_joiner(self):
        # Simulating multi-valued tag joined with "; "
        old_html, new_html = compute_diff(
            "Artist A; Artist B",
            "Artist A; Artist C",
            REMOVED_BG,
            ADDED_BG,
            TEXT_COLOR,
        )
        # "Artist A; Artist " should be common
        self.assertIn("Artist", old_html)
        # "B" vs "C" should be highlighted
        self.assertIn(REMOVED_BG, old_html)
        self.assertIn(ADDED_BG, new_html)

    def test_custom_threshold(self):
        # With threshold=1.0, even similar words get full highlight
        old_html, new_html = compute_diff(
            "Mitchell",
            "Mitchel",
            REMOVED_BG,
            ADDED_BG,
            TEXT_COLOR,
            threshold=1.0,
        )
        # Entire word should be highlighted since ratio < 1.0
        self.assertEqual(old_html, _wrap(_hl_removed("Mitchell")))
        self.assertEqual(new_html, _wrap(_hl_added("Mitchel")))

    def test_html_escaping(self):
        # Ensure special characters are escaped
        old_html, new_html = compute_diff("<script>", "<style>", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # No raw < or > in output (they should be escaped)
        self.assertNotIn("<script>", old_html)
        self.assertNotIn("<style>", new_html)
        self.assertIn("&lt;", old_html)
        self.assertIn("&gt;", old_html)
