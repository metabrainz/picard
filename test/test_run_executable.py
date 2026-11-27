# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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


import sys

from test.picardtestcase import PicardTestCase

from picard.util import run_executable


class TestRunExecutable(PicardTestCase):
    """Tests for run_executable, in particular the optional stdin input."""

    def test_passes_input_on_stdin(self):
        rc, out, _err = run_executable(
            sys.executable,
            '-c',
            'import sys; sys.stdout.write(sys.stdin.read())',
            input=b'hello stdin',
        )
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'hello stdin')

    def test_no_input_closes_stdin(self):
        # With no input, stdin is DEVNULL: reading it yields empty, not a hang.
        rc, out, _err = run_executable(
            sys.executable,
            '-c',
            'import sys; sys.stdout.write("got:" + sys.stdin.read())',
        )
        self.assertEqual(rc, 0)
        self.assertEqual(out, 'got:')

    def test_returns_exit_code(self):
        rc, _out, _err = run_executable(sys.executable, '-c', 'raise SystemExit(3)')
        self.assertEqual(rc, 3)
