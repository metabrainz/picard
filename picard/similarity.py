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

def distance(a,b):
    """Calculates the Levenshtein distance between a and b."""
    
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
            
    return current[n]
    
def boost(sim):
    sim2 = sim
    sim = min(1, (math.exp(sim) - 1) / (math.e - 1.2))
    sim = math.pow(sim, 0.8)
    sim = max(sim2, sim)
    return sim
    
def raw_similarity(a, b):
    if not a or not b:
        return 0.0
    # string distance => <0,1> similarity
    sim = 1 - distance(a, b) * 1.0 / max(len(a), len(b))
    # human brain doesn't think linear! :)
    return boost(sim)
    
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
    
def similarity(a1, b1):
    a2 = a1
    b2 = b1
    for w, r in _replace_words.items():
        a2 = a2.replace(w, r)
    def flt(a):
        def flt(a):
            return a not in _stop_words and len(a) > 1
#        print _split_re.split(a.lower())
        return u" ".join(filter(flt, _split_re.split(a.lower())))
    a2 = flt(a2)
    b2 = flt(b2)
    sim1 = raw_similarity(a1, b1)
    sim2 = raw_similarity(a2, b2)
    #print a2, b2
    #print sim1, sim2
    # just to not have 100% matches on e.g. 'ABC' vs 'abc'
    sim = sim1 * 0.1 + sim2 * 0.9
    #sim = sim2
    return sim

