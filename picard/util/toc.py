# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 metaisfacil
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


def parse_toc_itunes_cddb(tag_value):
    """
    Parse iTunes_CDDB_1 format TOC tag.

    Format: cddb_id+leadout_lba+num_tracks+track_lba_1+track_lba_2+...
    All values are decimal.
    """
    parts = tag_value.split('+')
    if len(parts) < 4:
        raise ValueError('Tag has unexpected format')

    # CDDB ID should be present
    cddb_id = parts[0]
    if not cddb_id:
        raise ValueError("CDDB ID is absent")

    # Validate leadout LBA is positive
    try:
        leadout_lba = int(parts[1])
    except ValueError as err:
        raise ValueError("Leadout LBA is not a valid integer") from err

    if leadout_lba <= 0:
        raise ValueError("Leadout LBA must be positive")

    # Validate track count is positive
    try:
        num_tracks = int(parts[2])
    except ValueError as err:
        raise ValueError("Track count is not a valid integer") from err

    if num_tracks <= 0:
        raise ValueError("Number of tracks must be positive")

    # Parse track LBAs
    try:
        track_lbas = [int(lba) for lba in parts[3:]]
    except ValueError as err:
        raise ValueError("One or more track offsets are not valid integers") from err

    # Validate track count matches offset count
    if len(track_lbas) != num_tracks:
        raise ValueError(f"Expected {num_tracks} track offsets, got {len(track_lbas)}")

    # Validate all track offsets are non-negative
    if any(lba < 0 for lba in track_lbas):
        raise ValueError("Track offsets must be non-negative")

    # Validate that all offsets are monotonically increasing
    all_offsets = track_lbas + [leadout_lba]
    for i in range(1, len(all_offsets)):
        if all_offsets[i] <= all_offsets[i - 1]:
            raise ValueError(
                f"Track offsets must be strictly increasing (offset {i}: {all_offsets[i]} <= {all_offsets[i - 1]})"
            )

    return num_tracks, leadout_lba, track_lbas
