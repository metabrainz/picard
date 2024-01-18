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


import yaml

from picard.disc.utils import (
    TocEntry,
    calculate_mb_toc_numbers,
)


def toc_from_file(path):
    """Reads whipper log files, generates musicbrainz disc TOC listing for use as discid.

    Warning: may work wrong for discs having data tracks. May generate wrong
    results on other non-standard cases."""
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
        toc_entries = (
            TocEntry(num, t['Start sector'], t['End sector'])
            for num, t in data['TOC'].items()
        )
        return calculate_mb_toc_numbers(toc_entries)
