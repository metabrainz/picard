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

import sys
import unittest
from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.audit import (
    event_match_prefixes,
    make_events_prefixes,
    prefixes_candidates_for_length,
    setup_audit,
)


class AuditTest(PicardTestCase):
    def test_make_events_prefixes(self):
        d = dict(make_events_prefixes(''))
        self.assertEqual(d, {})
        d = dict(make_events_prefixes('a'))
        self.assertEqual(d, {1: [('a',)]})
        d = dict(make_events_prefixes('a.b'))
        self.assertEqual(d, {2: [('a', 'b')]})
        d = dict(make_events_prefixes('a.b,c.d,a.b'))
        self.assertEqual(d, {2: [('a', 'b'), ('c', 'd')]})
        d = dict(make_events_prefixes('a,a.b,,a.b.c'))
        self.assertEqual(d, {1: [('a',)], 2: [('a', 'b')], 3: [('a', 'b', 'c')]})

    def test_prefixes_candidates_for_length(self):
        d = make_events_prefixes('a,a.b,c.d,a.b.c,d.e.f,g.h.i')
        self.assertEqual(list(prefixes_candidates_for_length(0, d)), [])
        self.assertEqual(list(prefixes_candidates_for_length(1, d)), [('a',)])
        self.assertEqual(list(prefixes_candidates_for_length(2, d)), [('a',), ('a', 'b'), ('c', 'd')])
        expected = [('a',), ('a', 'b'), ('c', 'd'), ('a', 'b', 'c'), ('d', 'e', 'f'), ('g', 'h', 'i')]
        self.assertEqual(list(prefixes_candidates_for_length(3, d)), expected)
        self.assertEqual(list(prefixes_candidates_for_length(4, d)), expected)

    def test_event_match_prefixes(self):
        d = make_events_prefixes('a.b')
        self.assertEqual(event_match_prefixes('a', d), False)
        self.assertEqual(event_match_prefixes('a.b', d), ('a', 'b'))
        self.assertEqual(event_match_prefixes('a.b.c', d), ('a', 'b'))
        self.assertEqual(event_match_prefixes('b.c', d), False)


@unittest.skipUnless(sys.version_info[:3] > (3, 8), "sys.addaudithook() available since Python 3.8")
class AuditHookTest(PicardTestCase):
    def test_setup_audit_1(self):
        with patch('sys.addaudithook') as mock:
            setup_audit('a,b.c')
            self.assertTrue(mock.called)

    def test_setup_audit_2(self):
        with patch('sys.addaudithook') as mock:
            setup_audit('')
            self.assertFalse(mock.called)
