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

from collections import namedtuple

from picard.disc.utils import (
    DATA_TRACK_GAP,
    PREGAP_LENGTH,
    NotSupportedTOCError,
)


ScsiTocEntry = namedtuple('ScsiTocEntry', 'number start_sector is_data')


def parse_toc_entries(f):
    """Parse a TOC in the format used by SCSI's READ TOC command."""

    data = f.read()

    datalen = int.from_bytes(data[:2], 'big')
    if datalen % 8 != 2:
        raise NotSupportedTOCError("Unexpected data length, likely not a SCSI TOC")

    first_track = data[2]
    last_track = data[3]

    entries = []
    leadout_offset = None

    for i, off in enumerate(range(4, 2 + datalen, 8)):
        entry = data[off : off + 8]
        number = entry[2]
        if number != first_track + i and number != 0xAA:
            raise NotSupportedTOCError("Unexpected track number, likely not a SCSI TOC")

        start_sector = int.from_bytes(entry[4:8], 'big')
        is_data = entry[1] & 0x4 != 0

        if number == 0xAA:
            leadout_offset = start_sector
        else:
            entries.append(ScsiTocEntry(number, start_sector, is_data))

    if entries[-1].is_data:
        leadout_offset = entries[-1].start_sector - DATA_TRACK_GAP
        entries.pop(-1)
        last_track = entries[-1].number

    offsets = tuple(entry.start_sector + PREGAP_LENGTH for entry in entries)
    return (first_track, last_track, leadout_offset + PREGAP_LENGTH) + offsets


def toc_from_file(path):
    """Reads a TOC in the SCSI format, generates MusicBrainz disc TOC listing for use as discid."""

    with open(path, 'rb') as f:
        return parse_toc_entries(f)
