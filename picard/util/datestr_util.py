# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

"""Utility functions for date str/obj."""

import re


def _int_or_none(value: str) -> int | None:
    value = value.strip()
    if value == "":
        return 0
    try:
        return int(value)
    except ValueError:
        return None


def _clamp_year(value: int | None) -> int | None:
    if value is None:
        return None
    if value < 0:
        return None
    if value > 9999:
        return None
    return value


def _is_valid_month(value: int) -> bool:
    return 0 <= value <= 12


def _is_valid_day(value: int) -> bool:
    return 0 <= value <= 31


def _parse_pure_year(value: str) -> str | None:
    m = re.fullmatch(r"(\d{4})", value)
    if not m:
        return None
    year = _clamp_year(int(m.group(1)))
    if year in (None, 0):
        return ""
    return f"{year:04d}"


def _format_from_components(year: int | None, month: int | None, day: int | None) -> str:
    y = _clamp_year(year if year is not None else -1)
    if y is None:
        return ""
    # y could be 0 here for partial unknown dates; treat specially below
    if month is None and day is None:
        return "" if y == 0 else f"{y:04d}"

    m = month if month is not None else 0
    d = day if day is not None else 0
    if not _is_valid_month(m) or not _is_valid_day(d):
        return ""

    if d == 0:
        if m == 0:
            return "" if y == 0 else f"{y:04d}"
        return f"{y:04d}-{m:02d}"

    if m == 0:
        return f"{y:04d}-00-{d:02d}"

    return f"{y:04d}-{m:02d}-{d:02d}"


def _parse_iso_like(value: str) -> str | None:
    if "-" not in value:
        return None
    parts = value.split("-")
    if not (1 <= len(parts) <= 3):
        return None

    parsed: list[int] = []
    for part in reversed(parts):
        num = _int_or_none(part)
        if num is None:
            return None
        if num or (num == 0 and parsed):
            parsed.append(num)
    parsed.reverse()

    if len(parsed) == 1:
        return _format_from_components(parsed[0], None, None)
    if len(parsed) == 2:
        y, m = parsed
        return _format_from_components(y, m, None)
    if len(parsed) == 3:
        y, m, d = parsed
        # Handle swapped middle and last if clearly YYYY-DD-MM
        if m > 12 and d <= 12:
            m, d = d, m
        return _format_from_components(y, m, d)
    return None


def _parse_slash_separated(value: str) -> str | None:
    # We only expect 3 tokens (two slashes)
    try:
        tokens = value.split("/", 2)
        a = _int_or_none(tokens[0])
        b = _int_or_none(tokens[1])
        c = _int_or_none(tokens[2])
    except IndexError:
        return None

    if a is None or b is None or c is None or not (0 < c <= 9999):
        return None
    y = _clamp_year(c) or None
    if y is None:
        return ""
    if a > 12 and _is_valid_month(b) and _is_valid_day(a):
        d, m = a, b
    elif b > 12 and _is_valid_month(a) and _is_valid_day(b):
        m, d = a, b
    else:
        return None
    if not _is_valid_month(m) or not _is_valid_day(d) or m == 0:
        return ""
    if d == 0:
        return f"{y:04d}-{m:02d}"
    return f"{y:04d}-{m:02d}-{d:02d}"


def _parse_compact_eight(value: str) -> str | None:
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", value)
    if not m:
        return None

    y = _clamp_year(int(m.group(1)))
    if y is None:
        return ""

    a = int(m.group(2))
    b = int(m.group(3))
    if _is_valid_month(a) and _is_valid_day(b) and a != 0:
        return f"{y:04d}-{a:02d}-{b:02d}"
    if _is_valid_month(b) and _is_valid_day(a) and b != 0:
        return f"{y:04d}-{b:02d}-{a:02d}"
    if a == 0 and _is_valid_day(b):
        return f"{y:04d}"
    if _is_valid_month(a) and b == 0:
        if a == 0:
            return f"{y:04d}"
        return f"{y:04d}-{a:02d}"
    return ""


def sanitize_date(datestr: str, disable_sanitization: bool = False) -> str:
    """Normalize a date string with optional sanitization bypass.

    Parameters
    ----------
    datestr : str
        Raw date string to normalize. Supported inputs include:
        - "YYYY", "YYYY-MM", "YYYY-MM-DD"
        - "YYYY-DD-MM" (normalized to "YYYY-MM-DD" when unambiguous)
        - "DD/MM/YYYY" and "MM/DD/YYYY" (disambiguated heuristically)
        - "YYYYMMDD" and "YYYYDDMM"
        Unknown components may be provided as "00" (or left empty for
        hyphenated inputs, e.g. "2006--"), meaning the component is unknown.
    disable_sanitization : bool, default False
        If True, returns the input unchanged.

    Returns
    -------
    str
        Normalized date in one of: "YYYY", "YYYY-MM", or "YYYY-MM-DD".
        Returns an empty string if the input cannot be normalized when
        sanitization is enabled.

    Notes
    -----
    - Unknown components are preserved without shifting other components.
      For example, month "00" with a known day stays as month "00":
      "2005-00-12" -> "2005-00-12" (not "2005-12").
    - Day "00" drops the day component: "2005-12-00" -> "2005-12".
    - Month "00" drops only the month when no day is given: "2005-00" -> "2005".
    - Fully unknown date "0000-00-00" normalizes to an empty string, but
      partially unknown values such as "0000-00-23" are preserved.

    Examples
    --------
    >>> sanitize_date('2005-12-00')
    '2005-12'
    >>> sanitize_date('2005-00-12')
    '2005-00-12'
    >>> sanitize_date('31/12/2005')
    '2005-12-31'
    >>> sanitize_date('20051231')
    '2005-12-31'
    >>> sanitize_date('20053112')
    '2005-12-31'
    >>> sanitize_date('2006--')
    '2006'
    """
    if disable_sanitization:
        return datestr

    if not datestr or not isinstance(datestr, str):
        return ""

    value = datestr.strip()
    if value == "":
        return ""

    # 1) Pure year
    result = _parse_pure_year(value)
    if result is not None:
        return result

    # 2) Hyphen-separated ISO-like
    result = _parse_iso_like(value)
    if result is not None:
        return result

    # 3) Slash-separated
    result = _parse_slash_separated(value)
    if result is not None:
        return result

    # 4) Compact YYYYMMDD or YYYYDDMM
    result = _parse_compact_eight(value)
    if result is not None:
        return result

    return ""
