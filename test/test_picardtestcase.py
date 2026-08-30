# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 The MusicBrainz Team
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


"""Tests for the shared test helpers in test/picardtestcase.py."""

import unittest

from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)


class SubtestCasesTest(PicardTestCase):
    def test_runs_every_case_with_a_sequence(self):
        seen = []

        class Sample(PicardTestCase):
            @subtest_cases("value,expected", [(1, 1), (2, 2), (3, 3)])
            def test_it(self, value, expected):
                seen.append((value, expected))
                assert value == expected

        Sample('test_it').test_it()
        self.assertEqual(seen, [(1, 1), (2, 2), (3, 3)])

    def test_single_argument_takes_plain_values(self):
        seen = []

        class Sample(PicardTestCase):
            @subtest_cases("value", [1, 2, 3])
            def test_it(self, value):
                seen.append(value)

        Sample('test_it').test_it()
        self.assertEqual(seen, [1, 2, 3])

    def test_mapping_labels_cases(self):
        seen = []

        class Sample(PicardTestCase):
            @subtest_cases("value,expected", {'a': (1, 1), 'b': (2, 2)})
            def test_it(self, value, expected):
                seen.append((value, expected))

        Sample('test_it').test_it()
        self.assertEqual(seen, [(1, 1), (2, 2)])

    def test_runs_again_when_inherited(self):
        """A decorated method inherited by two classes must run all cases in both.

        Regression guard: building the case list lazily would leave it
        exhausted after the first class ran, so the second would pass without
        checking anything.
        """
        runs = []

        class Base(PicardTestCase):
            @subtest_cases("value", [1, 2, 3])
            def test_it(self, value):
                runs.append(value)

        class First(Base):
            pass

        class Second(Base):
            pass

        First('test_it').test_it()
        Second('test_it').test_it()
        self.assertEqual(runs, [1, 2, 3, 1, 2, 3])

    def test_failing_case_does_not_stop_the_rest(self):
        seen = []

        class Sample(PicardTestCase):
            @subtest_cases("value", [1, 2, 3])
            def test_it(self, value):
                seen.append(value)
                assert value != 2, "boom"

        result = Sample('test_it').run()
        self.assertEqual(seen, [1, 2, 3])
        self.assertEqual(len(result.failures), 1)

    def test_arity_mismatch_raises(self):
        class Sample(PicardTestCase):
            @subtest_cases("a,b", [(1, 2), (3,)])
            def test_it(self, a, b):
                pass

        with self.assertRaises(ValueError):
            Sample('test_it').test_it()


if __name__ == '__main__':
    unittest.main()
