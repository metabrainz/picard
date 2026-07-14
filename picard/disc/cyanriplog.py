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


from collections.abc import (
    Iterable,
    Iterator,
)
import re

from picard.disc.utils import (
    NotSupportedTOCError,
    TocEntry,
    TocNumbers,
    calculate_mb_toc_numbers,
)


RE_TRACK_HEADER = re.compile(r"^Track (?P<num>\d+) ripped")
RE_START_LSN = re.compile(r"^\s+Start LSN:\s+(?P<lsn>\d+)\s*$")
RE_END_LSN = re.compile(r"^\s+End LSN:\s+(?P<lsn>\d+)\s*$")
RE_CYANRIP_HEADER = re.compile(r"^cyanrip\s+\d+\.\d+")


def filter_toc_entries(lines: Iterable[str]) -> Iterator[TocEntry]:
    """Parse cyanrip log lines and yield TocEntry for each track."""
    current_track = None
    start_lsn = None

    for line in lines:
        track_match = RE_TRACK_HEADER.match(line)
        if track_match:
            current_track = int(track_match['num'])
            start_lsn = None
            continue

        if current_track is not None:
            start_match = RE_START_LSN.match(line)
            if start_match:
                start_lsn = int(start_match['lsn'])
                continue

            end_match = RE_END_LSN.match(line)
            if end_match and start_lsn is not None:
                end_lsn = int(end_match['lsn'])
                yield TocEntry(current_track, start_lsn, end_lsn)
                current_track = None
                start_lsn = None


def toc_from_file(path: str) -> TocNumbers:
    """Reads cyanrip log files, generates MusicBrainz disc TOC listing for use as discid."""
    with open(path, encoding='utf-8') as f:
        first_line = f.readline()
        if not RE_CYANRIP_HEADER.match(first_line):
            raise NotSupportedTOCError("Not a cyanrip log file")
        f.seek(0)
        return calculate_mb_toc_numbers(filter_toc_entries(f))
