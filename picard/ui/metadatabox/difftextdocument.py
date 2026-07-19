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

"""Character/word-level diff highlighting for the metadata box.

Provides hybrid diff computation: first diffs at the word/token level,
then refines with character-level diffs within similar replaced tokens.
"""

from difflib import SequenceMatcher
from html import escape
import re

from PyQt6 import QtGui

from picard.ui.colors import interface_colors


# If two replaced tokens have a similarity ratio at or above this threshold,
# show character-level diff within the token. Below this, highlight the
# entire token as changed.
_CHAR_DIFF_RATIO_THRESHOLD = 0.5

# Split text into tokens: runs of word characters, or individual non-word
# characters (punctuation, symbols), or whitespace runs.
# This ensures punctuation is a separate token from the word it's attached to,
# e.g. "Rock'n'Roll!" -> ["Rock", "'", "n", "'", "Roll", "!"]
_TOKEN_RE = re.compile(r"(\w+|[^\w\s]|\s+)")


def _get_diff_colors():
    """Return (removed_bg, added_bg) as CSS rgba strings with transparency."""
    removed = interface_colors.get_qcolor('tagstatus_removed')
    added = interface_colors.get_qcolor('tagstatus_added')
    removed_bg = f'rgba({removed.red()}, {removed.green()}, {removed.blue()}, 60)'
    added_bg = f'rgba({added.red()}, {added.green()}, {added.blue()}, 60)'
    return removed_bg, added_bg


def _tokenize(text):
    """Split text into tokens: words, punctuation, and whitespace separately."""
    return _TOKEN_RE.findall(text)


def _highlight(text, bg_color):
    """Wrap escaped text in a colored background span."""
    return f'<span style="background-color: {bg_color};">{escape(text)}</span>'


def _char_diff_within_token(old_token, new_token, removed_bg, added_bg):
    """Compute character-level diff within a pair of similar tokens.

    Args:
        old_token: The original token string.
        new_token: The new token string.
        removed_bg: CSS color for removed character background.
        added_bg: CSS color for added character background.

    Returns:
        Tuple (old_html, new_html) with per-character highlights.
    """
    matcher = SequenceMatcher(None, old_token, new_token)
    old_parts = []
    new_parts = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == 'equal':
            chunk = escape(old_token[i1:i2])
            old_parts.append(chunk)
            new_parts.append(chunk)
        elif op == 'replace':
            old_parts.append(_highlight(old_token[i1:i2], removed_bg))
            new_parts.append(_highlight(new_token[j1:j2], added_bg))
        elif op == 'delete':
            old_parts.append(_highlight(old_token[i1:i2], removed_bg))
        elif op == 'insert':
            new_parts.append(_highlight(new_token[j1:j2], added_bg))

    return ''.join(old_parts), ''.join(new_parts)


def _process_replace(old_tokens, new_tokens, removed_bg, added_bg, old_parts, new_parts):
    """Process a 'replace' opcode from the token-level diff.

    Pairs up tokens positionally. For each pair, if the tokens are similar
    enough, applies character-level diff; otherwise highlights the whole token.
    Leftover unpaired tokens are fully highlighted.
    """
    pairs = min(len(old_tokens), len(new_tokens))
    for k in range(pairs):
        old_tok = old_tokens[k]
        new_tok = new_tokens[k]
        ratio = SequenceMatcher(None, old_tok, new_tok).ratio()
        if ratio >= _CHAR_DIFF_RATIO_THRESHOLD:
            old_html, new_html = _char_diff_within_token(old_tok, new_tok, removed_bg, added_bg)
            old_parts.append(old_html)
            new_parts.append(new_html)
        else:
            old_parts.append(_highlight(old_tok, removed_bg))
            new_parts.append(_highlight(new_tok, added_bg))
    # Leftover tokens on either side
    for k in range(pairs, len(old_tokens)):
        old_parts.append(_highlight(old_tokens[k], removed_bg))
    for k in range(pairs, len(new_tokens)):
        new_parts.append(_highlight(new_tokens[k], added_bg))


def compute_diff_html(old_text, new_text, text_color):
    """Compute a hybrid word/character-level diff and return (old_html, new_html).

    Strategy:
    1. Tokenize both texts into words, punctuation, and whitespace.
    2. Diff at the token level.
    3. For replaced token pairs that are similar enough (ratio >= threshold),
       do a character-level diff within the token.
    4. For replaced tokens that are too different, highlight the whole token.

    Args:
        old_text: The original text string.
        new_text: The new text string.
        text_color: QColor for the base text color.

    Returns:
        A tuple (old_html, new_html) with highlighted differences.
        Returns (None, None) if inputs are identical.
    """
    if old_text == new_text:
        return None, None

    removed_bg, added_bg = _get_diff_colors()
    text_css = text_color.name()

    old_tokens = _tokenize(old_text)
    new_tokens = _tokenize(new_text)

    matcher = SequenceMatcher(None, old_tokens, new_tokens)
    old_parts = []
    new_parts = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == 'equal':
            chunk = escape(''.join(old_tokens[i1:i2]))
            old_parts.append(chunk)
            new_parts.append(chunk)
        elif op == 'replace':
            _process_replace(
                old_tokens[i1:i2],
                new_tokens[j1:j2],
                removed_bg,
                added_bg,
                old_parts,
                new_parts,
            )
        elif op == 'delete':
            for tok in old_tokens[i1:i2]:
                old_parts.append(_highlight(tok, removed_bg))
        elif op == 'insert':
            for tok in new_tokens[j1:j2]:
                new_parts.append(_highlight(tok, added_bg))

    old_html = f'<span style="color: {text_css};">{"".join(old_parts)}</span>'
    new_html = f'<span style="color: {text_css};">{"".join(new_parts)}</span>'
    return old_html, new_html


def create_diff_document(html, font):
    """Create a QTextDocument configured for rendering diff HTML.

    Args:
        html: HTML string with diff markup.
        font: QFont to use for the document.

    Returns:
        A QTextDocument ready for painting.
    """
    doc = QtGui.QTextDocument()
    doc.setDefaultFont(font)
    doc.setDocumentMargin(2)
    doc.setHtml(html)
    return doc
