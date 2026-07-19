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

import re
from typing import NewType


_ISRC_RE = re.compile(r'^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$')

# A validated, normalized ISRC string (uppercase, 12 characters, no separators).
# Use valid_isrc() to obtain a NormalizedISRC from a raw string.
NormalizedISRC = NewType('NormalizedISRC', str)


def _normalize_isrc(value: str) -> str:
    """Normalize an ISRC value by removing hyphens/spaces and uppercasing.

    Args:
        value: Raw ISRC string, possibly with hyphens or spaces.

    Returns:
        Normalized uppercase ISRC string with separators removed.
    """
    return value.strip().replace('-', '').replace(' ', '').upper()


def valid_isrc(value: str) -> NormalizedISRC | None:
    """Validate and normalize an ISRC string.

    A valid ISRC consists of 12 characters: 2-letter country code,
    3-character alphanumeric registrant code, 2-digit year, and 5-digit
    designation code.

    Args:
        value: ISRC string to validate (may contain hyphens or spaces).

    Returns:
        NormalizedISRC if valid, None otherwise.
    """
    normalized = _normalize_isrc(value)
    if _ISRC_RE.match(normalized):
        return NormalizedISRC(normalized)
    return None


def format_isrc(value: str) -> str:
    """Format a normalized ISRC for display with hyphens.

    Converts `CCXXXYYNNNNN` to `CC-XXX-YY-NNNNN`.

    Args:
        value: Normalized 12-character ISRC string.

    Returns:
        Hyphenated display form, or the original value if not a valid ISRC.
    """
    if not _ISRC_RE.match(value):
        return value
    return f"{value[:2]}-{value[2:5]}-{value[5:7]}-{value[7:]}"


def normalized_isrcs(values: list[str]) -> set[NormalizedISRC]:
    """Validate and normalize a list of ISRC strings.

    Filters out invalid ISRCs and returns only validated, normalized ones.

    Args:
        values: Raw ISRC strings (e.g. from metadata.getall('isrc')).

    Returns:
        Set of validated NormalizedISRC values.
    """
    return set(filter(None, (valid_isrc(v) for v in values)))
