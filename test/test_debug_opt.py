# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Laurent Monin
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

from test.picardtestcase import PicardTestCase

from picard.debug_opts import DebugOptEnum


class TestDebugOpt(DebugOptEnum):
    A = 1, 'titleA', 'descriptionA'
    B = 2, 'titleB', 'descriptionB'


class DebugOptTest(PicardTestCase):
    def setUp(self):
        TestDebugOpt.set_registry(set())

    def test_enabled(self):
        self.assertFalse(TestDebugOpt.A.enabled)
        self.assertFalse(TestDebugOpt.B.enabled)
        TestDebugOpt.A.enabled = True
        self.assertTrue(TestDebugOpt.A.enabled)

    def test_optname(self):
        self.assertEqual(TestDebugOpt.A.optname, 'a')
        self.assertEqual(TestDebugOpt.B.optname, 'b')

    def test_title(self):
        self.assertEqual(TestDebugOpt.A.title, 'titleA')
        self.assertEqual(TestDebugOpt.B.title, 'titleB')

    def test_description(self):
        self.assertEqual(TestDebugOpt.A.description, 'descriptionA')
        self.assertEqual(TestDebugOpt.B.description, 'descriptionB')

    def test_opt_names(self):
        self.assertEqual(TestDebugOpt.opt_names(), 'a,b')

    def test_from_string_simple(self):
        TestDebugOpt.from_string('a')
        self.assertTrue(TestDebugOpt.A.enabled)
        self.assertFalse(TestDebugOpt.B.enabled)
        TestDebugOpt.from_string('a,b')
        self.assertTrue(TestDebugOpt.A.enabled)
        self.assertTrue(TestDebugOpt.B.enabled)

    def test_from_string_complex(self):
        TestDebugOpt.from_string('something, A,x,b')
        self.assertTrue(TestDebugOpt.A.enabled)
        self.assertTrue(TestDebugOpt.B.enabled)

    def test_from_string_remove(self):
        TestDebugOpt.set_registry({TestDebugOpt.B})
        self.assertTrue(TestDebugOpt.B.enabled)
        TestDebugOpt.from_string('A')
        self.assertTrue(TestDebugOpt.A.enabled)
        self.assertFalse(TestDebugOpt.B.enabled)

    def test_to_string(self):
        self.assertEqual('', TestDebugOpt.to_string())
        TestDebugOpt.A.enabled = True
        self.assertEqual('a', TestDebugOpt.to_string())
        TestDebugOpt.B.enabled = True
        self.assertEqual('a,b', TestDebugOpt.to_string())

    def test_set_get_registry(self):
        old_set = TestDebugOpt.get_registry()
        TestDebugOpt.A.enabled = True
        self.assertTrue(TestDebugOpt.A.enabled)
        new_set = set()
        TestDebugOpt.set_registry(new_set)
        self.assertFalse(TestDebugOpt.A.enabled)
        TestDebugOpt.B.enabled = True
        self.assertFalse(TestDebugOpt.A.enabled)
        self.assertTrue(TestDebugOpt.B.enabled)
        TestDebugOpt.set_registry(old_set)
        self.assertTrue(TestDebugOpt.A.enabled)
        self.assertFalse(TestDebugOpt.B.enabled)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            class BuggyOpt(DebugOptEnum):
                C = "x", "x", "x"

    def test_invalid2(self):
        with self.assertRaises(TypeError):
            class BuggyOpt(DebugOptEnum):
                C = 1, "x"
