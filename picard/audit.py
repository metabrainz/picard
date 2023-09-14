# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2023 Laurent Monin
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

from collections import defaultdict
import sys


def setup_audit(prefixes_string):
    """Setup audit hook according to `audit` command-line option"""
    if not prefixes_string:
        return
    if 'all' in prefixes_string.split(','):
        def event_match(event):
            return ('all', )
    else:
        # prebuild the dict, constant
        PREFIXES_DICT = make_events_prefixes(prefixes_string)

        def event_match(event):
            return event_match_prefixes(event, PREFIXES_DICT)

    def audit(event, args):
        # we can't use log here, as it generates events
        matched = event_match(event)
        if matched:
            matched = '.'.join(matched)
            print(f'audit:{matched}: {event} args={args}')

    sys.addaudithook(audit)


def make_events_prefixes(prefixes_string):
    """Build a dict with keys = length of prefix"""
    d = defaultdict(list)
    for p in sorted(set(tuple(e.split('.')) for e in prefixes_string.split(',') if e)):
        d[len(p)].append(p)
    return d


def prefixes_candidates_for_length(length, prefixes_dict):
    """Generate prefixes that may match this length"""
    for plen, v in prefixes_dict.items():
        if length >= plen:
            yield from v


def event_match_prefixes(event, prefixes_dict):
    """Matches event against prefixes
       Typical case: we want to match `os.mkdir` if prefix is `os` or `os.mkdir`
       but not the reverse: if prefix is `os.mkdir` we don't want to match an event named `os`
       It returns False, or the matched prefix
    """
    ev = tuple(event.split('.'))
    ev_len = len(ev)
    # only use candidates that may have a chance to match
    for p in prefixes_candidates_for_length(ev_len, prefixes_dict):
        # check that all elements of ev are in p
        if all(v == ev[i] for i, v in enumerate(p)):
            return p
    return False
