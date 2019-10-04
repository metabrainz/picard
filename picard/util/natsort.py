# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Philipp Wolfer
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

"""Functions for natural sorting of strings containing numbers.
"""

from locale import strxfrm
import re


RE_NUMBER = re.compile(r'(\d+)')


def natkey(text):
    """
    Return a sort key for a string for natural sort order.
    """
    return [int(s) if s.isdigit() else strxfrm(s)
            for s in RE_NUMBER.split(str(text))]


def natsorted(values):
    """
    Returns a copy of the given list sorted naturally.

    >>> sort(['track02', 'track10', 'track1'])
    ['track1', 'track02', 'track10']
    """
    return sorted(values, key=natkey)
