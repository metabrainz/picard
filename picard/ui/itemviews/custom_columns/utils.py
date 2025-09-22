# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the GNU General Public License Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Utility functions for custom column parsing and formatting."""

from __future__ import annotations

import re


def parse_time_format(time_str: str) -> float:
    """Parse time format (e.g., '3:00', '1:02:59') to seconds.

    Parameters
    ----------
    time_str : str
        Time string in format MM:SS or HH:MM:SS.

    Returns
    -------
    float
        Time in seconds.

    Raises
    ------
    ValueError
        If the time format is invalid.
    """
    if not time_str or time_str == "?:??":
        return 0.0
    parts = time_str.split(':')
    if len(parts) == 2:  # MM:SS
        minutes, seconds = map(float, parts)
        return minutes * 60 + seconds
    elif len(parts) == 3:  # HH:MM:SS
        hours, minutes, seconds = map(float, parts)
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid time format: {time_str}")


def parse_file_size(size_str: str) -> float:
    """Parse file size format (e.g., '1.0 MB', '1.0 MiB') to bytes.

    Parameters
    ----------
    size_str : str
        File size string with optional unit (B, KB, MB, GB, TB).

    Returns
    -------
    float
        Size in bytes.

    Raises
    ------
    ValueError
        If the size format is invalid.
    """
    if not size_str:
        return 0.0
    # Remove any parentheses content like "(1.0 MiB)"
    size_str = size_str.split('(')[0].strip()
    size_str = size_str.upper()

    # Extract number and unit
    match = re.match(r'^([\d.]+)\s*([KMGT]?B?)$', size_str)
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")

    number, unit = match.groups()
    number = float(number)

    # Convert to bytes
    multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    return number * multipliers.get(unit, 1)


def parse_bitrate(bitrate_str: str) -> float:
    """Parse bitrate format (e.g., '320 kbps', '128 kbps') to kbps.

    Parameters
    ----------
    bitrate_str : str
        Bitrate string with numeric value.

    Returns
    -------
    float
        Bitrate in kbps.

    Raises
    ------
    ValueError
        If the bitrate format is invalid.
    """
    if not bitrate_str:
        return 0.0
    # Extract number from bitrate string
    match = re.search(r'([\d.]+)', bitrate_str)
    if not match:
        raise ValueError(f"Invalid bitrate format: {bitrate_str}")
    return float(match.group(1))
