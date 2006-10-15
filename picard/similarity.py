# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

import math
import re
from picard.util import unaccent, strip_non_alnum
from picard.util.astrcmp import astrcmp


_split_re = re.compile("\W", re.UNICODE)
_stop_words = ["the", "--", "in", "of", "a", "feat"]

_replace_words = {
    "disc 1": "CD1",
    "disc 2": "CD2",
    "disc 3": "CD3",
    "disc 4": "CD4",
    "disc 5": "CD5",
    "disc 6": "CD6",
    "disc 7": "CD7",
    "disc 8": "CD8",
}

def normalize(string):
    string = strip_non_alnum(string.lower())
    #string = " ".join(filter(lambda a: a not in _stop_words and len(a) > 1,
    #                         _split_re.split(string)))
    #string = unaccent(string)
    return string

def similarity(a1, b1):
#    return astrcmp(a1, b1)
    """Calculates "smart" similarity of strings ``a`` and ``b``."""
    a2 = normalize(a1)
    if a2:
        b2 = normalize(b1)
    else:
        b2 = ""
    return astrcmp(a2, b2)
    #sim1 = astrcmp(a1, b1)
    #if a2 or b2:
    #    sim2 = astrcmp(a2, b2)
    #    sim = sim1 * 0.1 + sim2 * 0.9
    #else:
    #    sim = sim1
    #return sim

