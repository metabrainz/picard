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
import threading
import time


def setup_audit(prefixes_string):
    """Setup audit hook according to `audit` command-line option"""
    if not prefixes_string:
        return
    if 'all' in prefixes_string.split(','):
        def event_match(event):
            return ('all', )
    else:
        # prebuild the dict, constant
        PREFIXES_DICT = make_prefixes_dict(prefixes_string)

        def event_match(event):
            return is_matching_a_prefix(event, PREFIXES_DICT)

    start_time = time.time()

    def audit(event, args):
        # we can't use log here, as it generates events
        matched = event_match(event)
        if matched:
            matched = '.'.join(matched)
            tid = threading.get_native_id()
            secs = time.time() - start_time
            print(f'audit:{matched}:{tid}:{secs} {event} args={args}')

    sys.addaudithook(audit)


def list_from_prefixes_string(prefixes_string):
    """Generate a sorted list of prefixes tuples
       A prefixes string is a comma-separated list of dot-separated keys
       "a,b.c,d.e.f,,g" would result in following sorted list:
       [('a',), ('b', 'c'), ('d', 'e', 'f'), ('g',)]
    """
    yield from sorted(set(tuple(e.split('.')) for e in prefixes_string.split(',') if e))


def make_prefixes_dict(prefixes_string):
    """Build a dict with keys = length of prefix"""
    d = defaultdict(list)
    for prefix_tuple in list_from_prefixes_string(prefixes_string):
        d[len(prefix_tuple)].append(prefix_tuple)
    return dict(d)


def prefixes_candidates_for_length(length, prefixes_dict):
    """Generate prefixes that may match this length"""
    for prefix_len, prefixes in prefixes_dict.items():
        if length >= prefix_len:
            yield from prefixes


def is_matching_a_prefix(key, prefixes_dict):
    """Matches dot-separated key against prefixes
       Typical case: we want to match `os.mkdir` if prefix is `os` or `os.mkdir`
       but not the reverse: if prefix is `os.mkdir` we don't want to match a key named `os`
       It returns False, or the matched prefix
    """
    skey = tuple(key.split('.'))
    skey_len = len(skey)
    # only use candidates that may have a chance to match
    for p in prefixes_candidates_for_length(skey_len, prefixes_dict):
        # check that all elements of ev are in p
        if all(v == skey[i] for i, v in enumerate(p)):
            return p
    return False
