# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 Philipp Wolfer
# Copyright (C) 2022-2024 Laurent Monin
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


from picard.disc.utils import (
    NotSupportedTOCError,
    TocEntry,
    calculate_mb_toc_numbers,
)


def parse_toc_entries(f):
    """Parse a TOC in the format used by SCSI's READ TOC command."""

    data = f.read()
    first_track = data[2]
    last_track = data[3]
    for number in range(first_track, last_track + 1):
        base = ((number - first_track) * 8) + 4
        start_sector = int.from_bytes(data[base + 4 : base + 8], 'big')
        end_sector = int.from_bytes(data[base + 12 : base + 16], 'big')
        if end_sector < start_sector:
            raise NotSupportedTOCError("Track has negative length, likely not an SCSI TOC")
        if number == last_track:
            end_sector -= 1
        yield TocEntry(number, start_sector, end_sector)


def toc_from_file(path):
    """Reads a TOC in the SCSI format, generates MusicBrainz disc TOC listing for use as discid."""

    with open(path, 'rb') as f:
        return calculate_mb_toc_numbers(parse_toc_entries(f))
