# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2011-2012 Michael Wiencek
# Copyright (C) 2013, 2018-2021 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017 Ville Skyttä
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

from picard.util import strip_non_alnum
from picard.util.astrcmp import astrcmp


def normalize(orig_string):
    """Strips non-alphanumeric characters from a string unless doing so would make it blank."""
    string = strip_non_alnum(orig_string.lower())
    if not string:
        string = orig_string
    return string


def similarity(a1, b1):
    """Calculates similarity of single words as a function of their edit distance."""
    a2 = normalize(a1)
    if a2:
        b2 = normalize(b1)
    else:
        b2 = ""
    return astrcmp(a2, b2)


_split_words_re = re.compile(r'\W+', re.UNICODE)


def similarity2(a, b):
    """Calculates similarity of a multi-word strings."""
    alist = list(filter(bool, _split_words_re.split(a.lower())))
    blist = list(filter(bool, _split_words_re.split(b.lower())))
    total = 0
    score = 0.0
    if len(alist) > len(blist):
        alist, blist = blist, alist
    for av in alist:
        ms = 0.0
        mp = None
        for position, bv in enumerate(blist):
            s = astrcmp(av, bv)
            if s > ms:
                ms = s
                mp = position
        if mp is not None:
            score += ms
            if ms > 0.6:
                del blist[mp]
        total += 1
    total += len(blist) * 0.4
    if total:
        return score / total
    else:
        return 0
