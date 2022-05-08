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

from picard.disc.utils import calculate_mb_toc_numbers


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


PREGAP_LENGTH = 150


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


ENCODING_BOMS = {
    b'\xff\xfe': 'utf-16-le',
    b'\xfe\xff': 'utf-16-be',
    b'\00\00\xff\xfe': 'utf-32-le',
    b'\00\00\xfe\xff': 'utf-32-be',
}


def _detect_encoding(path):
    with open(path, 'rb') as f:
        first_bytes = f.read(4)
        for bom, encoding in ENCODING_BOMS.items():
            if first_bytes.startswith(bom):
                return encoding
        return 'utf-8'


def toc_from_file(path):
    """Reads EAC / XLD log files, generates musicbrainz disc TOC listing for use as discid.

    Warning: may work wrong for discs having data tracks. May generate wrong
    results on other non-standard cases."""
    encoding = _detect_encoding(path)
    with open(path, 'r', encoding=encoding) as f:
        return calculate_mb_toc_numbers(filter_toc_entries(f))
