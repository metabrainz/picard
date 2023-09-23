# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 Philipp Wolfer
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

from picard.disc.utils import (
    NotSupportedTOCError,
    TocEntry,
    calculate_mb_toc_numbers,
)
from picard.util import detect_unicode_encoding


RE_TOC_ENTRY = re.compile(
    r"^Track (?P<num>\d+):\s+Ripped LBA (?P<start_sector>\d+) to (?P<end_sector>\d+)")


def filter_toc_entries(lines):
    """
    Take iterator of lines, return iterator of toc entries
    """
    last_track_num = 0
    for line in lines:
        m = RE_TOC_ENTRY.match(line)
        if m:
            track_num = int(m['num'])
            if last_track_num + 1 != track_num:
                raise NotSupportedTOCError(f"Non consecutive track numbers ({last_track_num} => {track_num}) in dBPoweramp log. Likely a partial rip, disc ID cannot be calculated")
            last_track_num = track_num
            yield TocEntry(track_num, int(m['start_sector']), int(m['end_sector'])-1)


def toc_from_file(path):
    """Reads dBpoweramp log files, generates MusicBrainz disc TOC listing for use as discid."""
    encoding = detect_unicode_encoding(path)
    with open(path, 'r', encoding=encoding) as f:
        return calculate_mb_toc_numbers(filter_toc_entries(f))
