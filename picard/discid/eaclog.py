# -*- coding: utf-8 -*-
#
# MIT License
#
# Copyright(c) 2018 Konstantin Mochalov
# Copyright(c) 2022 Philipp Wolfer
#
# Original code from https://gist.github.com/kolen/765526
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re


RE_TOC_TABLE_HEADER = re.compile(r""" \s*
    \s*.+\s+ \| # track
    \s+.+\s+ \| # start
    \s+.+\s+ \| # length
    \s+.+\s+ \| # start sector
    \s+.+\s*$   # end sector
    """, re.VERBOSE)

RE_TOC_TABLE_LINE = re.compile(r"""
    ^\s*
    (?P<num>\d+)
    \s*\|\s*
    (?P<start_time>[0-9:.]+)
    \s*\|\s*
    (?P<length_time>[0-9:.]+)
    \s*\|\s*
    (?P<start_sector>\d+)
    \s*\|\s*
    (?P<end_sector>\d+)
    \s*$""", re.VERBOSE)


class NotSupportedTOCError(Exception):
    pass


def filter_toc_entries(lines):
    """
    Take iterator of lines, return iterator of toc entries
    """

    # Search the TOC table header
    for line in lines:
        # to allow internationalized EAC output where column headings
        # may differ
        if RE_TOC_TABLE_HEADER.match(line):
            # Skip over the table header separator
            next(lines)
            break

    for line in lines:
        m = RE_TOC_TABLE_LINE.match(line)
        if not m:
            break
        yield m.groupdict()


def calculate_mb_toc_numbers(eac_entries):
    """
    Take iterator of toc entries, return list of numbers for musicbrainz disc id
    """
    eac = list(eac_entries)
    num_tracks = len(eac)
    if not num_tracks:
        raise NotSupportedTOCError("Empty track list: %s", eac)

    tracknums = [int(e['num']) for e in eac]
    if list(range(1, num_tracks+1)) != tracknums:
        raise NotSupportedTOCError("Non-standard track number sequence: %s", tracknums)

    leadout_offset = int(eac[-1]['end_sector']) + 150 + 1
    offsets = [(int(x['start_sector']) + 150) for x in eac]
    return [1, num_tracks, leadout_offset] + offsets


def toc_from_file(path):
    """Reads EAC / XLD log files, generates musicbrainz disc TOC listing for use as discid.

    Warning: may work wrong for discs having data tracks. May generate wrong
    results on other non-standard cases."""
    with open(path, encoding='utf-8') as f:
        return calculate_mb_toc_numbers(filter_toc_entries(f))
