# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Laurent Monin
# Copyright (C) 2024 Philipp Wolfer
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


class DebugOptTestCase(DebugOptEnum):
    A = 1, 'titleA', 'descriptionA'
    B = 2, 'titleB', 'descriptionB'


class TestDebugOpt(PicardTestCase):
    def setUp(self):
        super().setUp()
        DebugOptTestCase.set_registry(set())

    def test_enabled(self):
        self.assertFalse(DebugOptTestCase.A.enabled)
        self.assertFalse(DebugOptTestCase.B.enabled)
        DebugOptTestCase.A.enabled = True
        self.assertTrue(DebugOptTestCase.A.enabled)

    def test_optname(self):
        self.assertEqual(DebugOptTestCase.A.optname, 'a')
        self.assertEqual(DebugOptTestCase.B.optname, 'b')

    def test_title(self):
        self.assertEqual(DebugOptTestCase.A.title, 'titleA')
        self.assertEqual(DebugOptTestCase.B.title, 'titleB')

    def test_description(self):
        self.assertEqual(DebugOptTestCase.A.description, 'descriptionA')
        self.assertEqual(DebugOptTestCase.B.description, 'descriptionB')

    def test_opt_names(self):
        self.assertEqual(DebugOptTestCase.opt_names(), 'a,b')

    def test_from_string_simple(self):
        DebugOptTestCase.from_string('a')
        self.assertTrue(DebugOptTestCase.A.enabled)
        self.assertFalse(DebugOptTestCase.B.enabled)
        DebugOptTestCase.from_string('a,b')
        self.assertTrue(DebugOptTestCase.A.enabled)
        self.assertTrue(DebugOptTestCase.B.enabled)

    def test_from_string_complex(self):
        DebugOptTestCase.from_string('something, A,x,b')
        self.assertTrue(DebugOptTestCase.A.enabled)
        self.assertTrue(DebugOptTestCase.B.enabled)

    def test_from_string_remove(self):
        DebugOptTestCase.set_registry({DebugOptTestCase.B})
        self.assertTrue(DebugOptTestCase.B.enabled)
        DebugOptTestCase.from_string('A')
        self.assertTrue(DebugOptTestCase.A.enabled)
        self.assertFalse(DebugOptTestCase.B.enabled)

    def test_to_string(self):
        self.assertEqual('', DebugOptTestCase.to_string())
        DebugOptTestCase.A.enabled = True
        self.assertEqual('a', DebugOptTestCase.to_string())
        DebugOptTestCase.B.enabled = True
        self.assertEqual('a,b', DebugOptTestCase.to_string())

    def test_set_get_registry(self):
        old_set = DebugOptTestCase.get_registry()
        DebugOptTestCase.A.enabled = True
        self.assertTrue(DebugOptTestCase.A.enabled)
        new_set = set()
        DebugOptTestCase.set_registry(new_set)
        self.assertFalse(DebugOptTestCase.A.enabled)
        DebugOptTestCase.B.enabled = True
        self.assertFalse(DebugOptTestCase.A.enabled)
        self.assertTrue(DebugOptTestCase.B.enabled)
        DebugOptTestCase.set_registry(old_set)
        self.assertTrue(DebugOptTestCase.A.enabled)
        self.assertFalse(DebugOptTestCase.B.enabled)

    def test_invalid(self):
        with self.assertRaises(ValueError):

            class BuggyOpt(DebugOptEnum):
                C = "x", "x", "x"

    def test_invalid2(self):
        with self.assertRaises(TypeError):

            class BuggyOpt(DebugOptEnum):
                C = 1, "x"


class TestDebugOptTiming(PicardTestCase):
    def setUp(self):
        super().setUp()
        DebugOptTestCase.set_registry(set())

    def test_timing_disabled_no_logging(self):
        """When disabled, timing should not log anything."""
        self.assertFalse(DebugOptTestCase.A.enabled)
        with DebugOptTestCase.A.timing("should not appear"):
            pass
        # No exception means it worked as a no-op

    def test_timing_disabled_body_executes(self):
        """The wrapped code must still execute when timing is disabled."""
        result = []
        with DebugOptTestCase.A.timing("test"):
            result.append(1)
        self.assertEqual(result, [1])

    def test_timing_enabled_body_executes(self):
        """The wrapped code must execute when timing is enabled."""
        DebugOptTestCase.A.enabled = True
        result = []
        with DebugOptTestCase.A.timing("test"):
            result.append(1)
        self.assertEqual(result, [1])

    def test_timing_enabled_logs_message(self):
        """When enabled, timing should log the formatted message with elapsed time."""
        from unittest.mock import patch

        DebugOptTestCase.A.enabled = True
        with patch('picard.log.debug') as mock_debug:
            with DebugOptTestCase.A.timing("Batch: %d items", 25):
                pass
            mock_debug.assert_called_once()
            fmt, msg, elapsed = mock_debug.call_args[0]
            self.assertEqual(fmt, "%s in %.1f ms")
            self.assertEqual(msg, "Batch: 25 items")
            self.assertIsInstance(elapsed, float)
            self.assertGreaterEqual(elapsed, 0.0)

    def test_timing_msg_func(self):
        """msg_func should be called lazily only when enabled."""
        from unittest.mock import patch

        DebugOptTestCase.A.enabled = True
        called = []
        with patch('picard.log.debug') as mock_debug:
            with DebugOptTestCase.A.timing(msg_func=lambda: (called.append(1), "Lazy msg")[1]):
                pass
            self.assertEqual(called, [1])
            fmt, msg, _elapsed = mock_debug.call_args[0]
            self.assertEqual(msg, "Lazy msg")

    def test_timing_msg_func_not_called_when_disabled(self):
        """msg_func must not be called when the option is disabled."""
        called = []
        with DebugOptTestCase.A.timing(msg_func=lambda: (called.append(1), "nope")[1]):
            pass
        self.assertEqual(called, [])
