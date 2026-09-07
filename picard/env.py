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

"""Helpers for reading environment variables.

This module is intentionally dependency-free (standard library only) and lives
at the top level of the ``picard`` package so it can be imported from build
tooling such as ``setup.py`` and ``picard.spec`` without pulling in PyQt6 or
the heavier ``picard.util`` package.
"""

import os


# Recognized string values for boolean environment variables.
_ENV_TRUTHY_VALUES = frozenset({'1', 'true', 'yes', 'on'})
_ENV_FALSY_VALUES = frozenset({'0', 'false', 'no', 'off', ''})


def parse_bool_env(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable.

    Interprets common truthy/falsy string values case-insensitively and
    ignoring surrounding whitespace:

    - Truthy: ``1``, ``true``, ``yes``, ``on``
    - Falsy: ``0``, ``false``, ``no``, ``off``, empty string

    If the variable is unset or holds an unrecognized value, ``default`` is
    returned. This provides a single, predictable convention for all
    Picard-owned boolean environment variables.

    Args:
        name: Name of the environment variable to read.
        default: Value returned when the variable is unset or unrecognized.

    Returns:
        The parsed boolean value.
    """
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip().lower()
    if value in _ENV_TRUTHY_VALUES:
        return True
    if value in _ENV_FALSY_VALUES:
        return False
    return default


def parse_int_env(name: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    """Parse a non-negative integer environment variable.

    Reads the variable, strips surrounding whitespace and parses it as a base-10
    integer. If the variable is unset, empty, or holds a value that cannot be
    parsed as an integer, ``default`` is returned. When parsing succeeds the
    value is clamped to the inclusive ``[minimum, maximum]`` range if those
    bounds are provided.

    This provides a single, predictable convention for Picard-owned integer
    environment variables (e.g. timeouts and limits).

    Args:
        name: Name of the environment variable to read.
        default: Value returned when the variable is unset or unparseable.
        minimum: Optional inclusive lower bound to clamp the parsed value to.
        maximum: Optional inclusive upper bound to clamp the parsed value to.

    Returns:
        The parsed (and optionally clamped) integer value.
    """
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        parsed = int(value.strip())
    except (ValueError, TypeError):
        return default
    if minimum is not None and parsed < minimum:
        parsed = minimum
    if maximum is not None and parsed > maximum:
        parsed = maximum
    return parsed
