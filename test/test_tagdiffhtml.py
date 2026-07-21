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
    highlight_full,
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
    return f'<span style="color: {TEXT_COLOR}; white-space: pre;">{inner}</span>'


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

    def test_cjk_characters_split_individually(self):
        self.assertEqual(tokenize("周杰倫"), ["周", "杰", "倫"])

    def test_cjk_mixed_with_latin(self):
        self.assertEqual(
            tokenize("周杰倫 Jay Chou"),
            ["周", "杰", "倫", " ", "Jay", " ", "Chou"],
        )

    def test_cjk_with_punctuation(self):
        self.assertEqual(
            tokenize("周杰倫feat.蔡依林"),
            ["周", "杰", "倫", "feat", ".", "蔡", "依", "林"],
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


class TestHighlightFull(PicardTestCase):
    def test_identical_strings_returns_none(self):
        result = highlight_full("same", "same", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        self.assertEqual(result, (None, None))

    def test_empty_strings_returns_none(self):
        result = highlight_full("", "", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        self.assertEqual(result, (None, None))

    def test_full_highlight_both(self):
        old_html, new_html = highlight_full("abc-123-def", "xyz-789-ghi", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # Old value entirely highlighted with removed color
        self.assertEqual(old_html, _wrap(_hl_removed("abc-123-def")))
        # New value entirely highlighted with added color
        self.assertEqual(new_html, _wrap(_hl_added("xyz-789-ghi")))

    def test_old_empty_new_highlighted(self):
        # Simulates an added tag (no old value)
        old_html, new_html = highlight_full("", "new value", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # Old is an empty highlight span
        self.assertEqual(old_html, _wrap(_hl_removed("")))
        # New value fully highlighted
        self.assertEqual(new_html, _wrap(_hl_added("new value")))

    def test_new_empty_old_highlighted(self):
        # Simulates a removed tag (no new value)
        old_html, new_html = highlight_full("old value", "", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # Old value fully highlighted
        self.assertEqual(old_html, _wrap(_hl_removed("old value")))
        # New is an empty highlight span
        self.assertEqual(new_html, _wrap(_hl_added("")))

    def test_html_escaping(self):
        old_html, new_html = highlight_full("<b>old</b>", "<i>new</i>", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        self.assertNotIn("<b>", old_html)
        self.assertNotIn("<i>", new_html)
        self.assertIn("&lt;b&gt;", old_html)
        self.assertIn("&lt;i&gt;", new_html)


class TestComputeDiffEdgeCases(PicardTestCase):
    def test_old_empty_new_has_value(self):
        old_html, new_html = compute_diff("", "added text", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # Everything in new should be highlighted as added
        self.assertIn(_hl_added("added"), new_html)
        self.assertIn(_hl_added("text"), new_html)

    def test_old_has_value_new_empty(self):
        old_html, new_html = compute_diff("removed text", "", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # Everything in old should be highlighted as removed
        self.assertIn(_hl_removed("removed"), old_html)
        self.assertIn(_hl_removed("text"), old_html)

    def test_whitespace_only_change(self):
        old_html, new_html = compute_diff("a  b", "a b", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # The extra space in old should be highlighted as removed
        self.assertIn(REMOVED_BG, old_html)
        # The words should not be highlighted
        self.assertNotIn(_hl_removed("a"), old_html)
        self.assertNotIn(_hl_removed("b"), old_html)

    def test_single_char_change(self):
        old_html, new_html = compute_diff("a", "b", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        self.assertEqual(old_html, _wrap(_hl_removed("a")))
        self.assertEqual(new_html, _wrap(_hl_added("b")))

    def test_formatted_time_diff(self):
        # Simulates ~length handling: formatted time strings like "4:05" vs "4:06"
        old_html, new_html = compute_diff("4:05", "4:06", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # The "4:" prefix is common, only "05" vs "06" differs
        self.assertIn("4", old_html)
        self.assertIn("4", new_html)
        self.assertIn(REMOVED_BG, old_html)
        self.assertIn(ADDED_BG, new_html)

    def test_formatted_time_full_diff(self):
        # Very different times get full highlight
        old_html, new_html = highlight_full("3:30", "4:06", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        self.assertEqual(old_html, _wrap(_hl_removed("3:30")))
        self.assertEqual(new_html, _wrap(_hl_added("4:06")))

    def test_cjk_single_character_change(self):
        # "周杰倫" vs "周杰伦" - last character differs (traditional vs simplified)
        old_html, new_html = compute_diff("周杰倫", "周杰伦", REMOVED_BG, ADDED_BG, TEXT_COLOR)
        # "周" and "杰" should be common (not highlighted)
        self.assertIn("周", old_html)
        self.assertIn("杰", old_html)
        # "倫" vs "伦" should be highlighted
        self.assertIn(_hl_removed("倫"), old_html)
        self.assertIn(_hl_added("伦"), new_html)
