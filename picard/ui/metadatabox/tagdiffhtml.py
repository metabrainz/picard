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

"""Hybrid word/character-level diff computation for tag values.

This module contains the pure diff logic without any Qt dependency.
It tokenizes text, computes diffs, and produces HTML markup strings
that can be rendered by the UI layer.

Strategy:
1. Tokenize both texts into words, punctuation, and whitespace.
2. Diff at the token level using SequenceMatcher.
3. For replaced token pairs that are similar enough (ratio >= threshold),
   refine with character-level diff within the token.
4. For dissimilar replaced tokens, highlight the entire token.
"""

from difflib import SequenceMatcher
from html import escape
import re


# If two replaced tokens have a similarity ratio at or above this threshold,
# show character-level diff within the token. Below this, highlight the
# entire token as changed.
CHAR_DIFF_RATIO_THRESHOLD = 0.5

# Split text into tokens: runs of word characters, or individual non-word
# characters (punctuation, symbols), or whitespace runs.
# This ensures punctuation is a separate token from the word it's attached to,
# e.g. "Rock'n'Roll!" -> ["Rock", "'", "n", "'", "Roll", "!"]
_TOKEN_RE = re.compile(r"(\w+|[^\w\s]|\s+)")


def tokenize(text: str) -> list[str]:
    """Split text into tokens: words, punctuation, and whitespace separately.

    Args:
        text: The input string to tokenize.

    Returns:
        A list of token strings.
    """
    return _TOKEN_RE.findall(text)


def _highlight(text: str, bg_color: str) -> str:
    """Wrap escaped text in a colored background span.

    Args:
        text: The raw text to highlight.
        bg_color: CSS color value for the background.

    Returns:
        An HTML span string with the text escaped and highlighted.
    """
    return f'<span style="background-color: {bg_color};">{escape(text)}</span>'


def _char_diff_within_token(
    old_token: str,
    new_token: str,
    removed_bg: str,
    added_bg: str,
) -> tuple[str, str]:
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
    old_parts: list[str] = []
    new_parts: list[str] = []

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


def _process_replace(
    old_tokens: list[str],
    new_tokens: list[str],
    removed_bg: str,
    added_bg: str,
    old_parts: list[str],
    new_parts: list[str],
    threshold: float = CHAR_DIFF_RATIO_THRESHOLD,
) -> None:
    """Process a 'replace' opcode from the token-level diff.

    Pairs up tokens positionally. For each pair, if the tokens are similar
    enough (ratio >= threshold), applies character-level diff; otherwise
    highlights the whole token.
    Leftover unpaired tokens are fully highlighted.

    Args:
        old_tokens: List of old tokens in the replaced range.
        new_tokens: List of new tokens in the replaced range.
        removed_bg: CSS color for removed token background.
        added_bg: CSS color for added token background.
        old_parts: Accumulator list for old HTML parts (mutated in place).
        new_parts: Accumulator list for new HTML parts (mutated in place).
        threshold: Similarity ratio threshold for character-level refinement.
    """
    pairs = min(len(old_tokens), len(new_tokens))
    for old_tok, new_tok in zip(old_tokens[:pairs], new_tokens[:pairs], strict=True):
        sm = SequenceMatcher(None, old_tok, new_tok)
        # quick_ratio() is an upper bound; if even that is below threshold,
        # skip the expensive full ratio() computation.
        if sm.quick_ratio() >= threshold and sm.ratio() >= threshold:
            old_html, new_html = _char_diff_within_token(old_tok, new_tok, removed_bg, added_bg)
            old_parts.append(old_html)
            new_parts.append(new_html)
        else:
            old_parts.append(_highlight(old_tok, removed_bg))
            new_parts.append(_highlight(new_tok, added_bg))
    # Leftover unpaired tokens on either side
    old_parts.extend(_highlight(tok, removed_bg) for tok in old_tokens[pairs:])
    new_parts.extend(_highlight(tok, added_bg) for tok in new_tokens[pairs:])


def compute_diff(
    old_text: str,
    new_text: str,
    removed_bg: str,
    added_bg: str,
    text_color: str,
    threshold: float = CHAR_DIFF_RATIO_THRESHOLD,
) -> tuple[str | None, str | None]:
    """Compute a hybrid word/character-level diff and return (old_html, new_html).

    This is the main entry point for diff computation. It takes raw CSS color
    strings so it has no dependency on Qt or the color configuration system.

    Args:
        old_text: The original text string.
        new_text: The new text string.
        removed_bg: CSS color for removed/deleted highlights.
        added_bg: CSS color for added/inserted highlights.
        text_color: CSS color for the base text.
        threshold: Similarity ratio threshold for character-level refinement
                   within replaced tokens.

    Returns:
        A tuple (old_html, new_html) with highlighted differences.
        Returns (None, None) if inputs are identical.
    """
    if old_text == new_text:
        return None, None

    old_tokens = tokenize(old_text)
    new_tokens = tokenize(new_text)

    matcher = SequenceMatcher(None, old_tokens, new_tokens)
    old_parts: list[str] = []
    new_parts: list[str] = []

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
                threshold,
            )
        elif op == 'delete':
            old_parts.extend(_highlight(tok, removed_bg) for tok in old_tokens[i1:i2])
        elif op == 'insert':
            new_parts.extend(_highlight(tok, added_bg) for tok in new_tokens[j1:j2])

    old_html = f'<span style="color: {text_color};">{"".join(old_parts)}</span>'
    new_html = f'<span style="color: {text_color};">{"".join(new_parts)}</span>'
    return old_html, new_html


def highlight_full(
    old_text: str,
    new_text: str,
    removed_bg: str,
    added_bg: str,
    text_color: str,
) -> tuple[str | None, str | None]:
    """Highlight the entire old and new strings as fully replaced.

    Used for opaque values (MBIDs, etc.) or completely different strings
    where character-level diff is meaningless.

    Args:
        old_text: The original text string.
        new_text: The new text string.
        removed_bg: CSS color for the removed highlight background.
        added_bg: CSS color for the added highlight background.
        text_color: CSS color for the base text.

    Returns:
        A tuple (old_html, new_html) with full-string highlights.
        Returns (None, None) if inputs are identical.
    """
    if old_text == new_text:
        return None, None
    old_html = f'<span style="color: {text_color};">{_highlight(old_text, removed_bg)}</span>'
    new_html = f'<span style="color: {text_color};">{_highlight(new_text, added_bg)}</span>'
    return old_html, new_html
