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


"""The shell on a real terminal: Ctrl-C and Ctrl-D at the prompt, the history of the lines."""

import os
import select
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from test.picardtestcase import PicardTestCase

from picard.const.sys import (
    IS_LINUX,
    IS_WIN,
)


if not IS_WIN:
    import pty


def _read_until(fd, text, timeout=30):
    """Read from the terminal until ``text`` was seen, or the timeout; return what was read."""
    out = b''
    end = time.monotonic() + timeout
    while text not in out and time.monotonic() < end:
        ready, _w, _x = select.select([fd], [], [], 0.2)
        if ready:
            try:
                data = os.read(fd, 4096)
            except OSError:  # the child has gone
                break
            if not data:
                break
            out += data
    return out


# The input hook of PyQt is the same everywhere, but how readline behaves on a
# pseudo-terminal is not: with the libedit of macOS the prompt never shows up and
# the test waits until CI cancels the job. Linux is enough to catch a regression.
@unittest.skipUnless(IS_LINUX, "needs a pseudo-terminal and GNU readline")
class ShellTerminalTest(PicardTestCase):
    @staticmethod
    def _environment(tmp):
        """The environment of the shell: its history in ``tmp``, not in the folder of the user, and no colors.

        The output is then read as plain text, whatever the colors of the console are.
        """
        return dict(os.environ, PICARD_SHELL_HISTORY_FILE=os.path.join(tmp, 'shell_history'), NO_COLOR='1')

    def _start(self, tmp):
        """Start the shell on a terminal; return it and the side of the terminal to type on."""
        master, slave = pty.openpty()
        shell = subprocess.Popen(
            [sys.executable, '-m', 'picard.cli', '-c', os.path.join(tmp, 'picard.ini'), 'shell'],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            close_fds=True,
            env=self._environment(tmp),
        )
        os.close(slave)
        self.addCleanup(os.close, master)
        self.addCleanup(shell.wait)
        self.addCleanup(shell.kill)
        return shell, master

    @staticmethod
    def _type(master, key):
        """Type ``key`` at the next prompt; return what the shell wrote until then."""
        output = _read_until(master, b'picard> ')
        os.write(master, key)
        return output

    def _end(self, shell, master):
        """Leave the shell; return what it wrote last."""
        output = self._type(master, b'quit\r')
        output += _read_until(master, b'\x00', timeout=10)
        shell.wait(timeout=30)
        return output

    def _run(self, tmp, keys):
        """Start the shell on a terminal, type each of ``keys`` at a prompt, leave, and return what it wrote."""
        shell, master = self._start(tmp)
        output = b''.join(self._type(master, key) for key in keys)
        return output + self._end(shell, master)

    def test_a_line_of_a_session_is_recalled_with_the_up_key_in_the_next(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._run(tmp, [b'help selectors\r'])
            # The history file is readable by the user only.
            self.assertEqual(0o600, os.stat(os.path.join(tmp, 'shell_history')).st_mode & 0o777)
            # Up twice: quit, then help selectors, which runs again.
            output = self._run(tmp, [b'\x1b[A\x1b[A\r'])
        self.assertIn(b'A selector names the objects a command acts on', output)

    def test_two_shells_at_the_same_time_keep_the_lines_of_each_other(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = self._start(tmp)
            second = self._start(tmp)
            self._type(first[1], b'help selectors\r')
            self._type(second[1], b'help paths\r')
            self._end(*first)
            self._end(*second)
            with open(os.path.join(tmp, 'shell_history')) as f:
                lines = f.read().splitlines()
        self.assertEqual(['help selectors', 'quit', 'help paths', 'quit'], lines)

    def test_shell_history_lists_and_clears_the_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._run(tmp, [b'help selectors\r'])
            output = self._run(tmp, [b'help paths\r', b'shell history\r', b'shell history clear\r'])
            with open(os.path.join(tmp, 'shell_history')) as f:
                lines = f.read().splitlines()
        # The lines of both sessions, numbered, the one of the previous session first.
        self.assertIn(b'1  help selectors\r\n2  quit\r\n3  help paths\r\n4  shell history\r\n', output)
        self.assertIn(b'the history is cleared', output)
        # Only what came after the clear is left.
        self.assertEqual(['quit'], lines)

    def test_ctrl_c_then_ctrl_d_leaves_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_file = os.path.join(tmp, 'picard.ini')
            master, slave = pty.openpty()
            try:
                shell = subprocess.Popen(
                    [sys.executable, '-m', 'picard.cli', '-c', config_file, 'shell'],
                    stdin=slave,
                    stdout=slave,
                    stderr=slave,
                    close_fds=True,
                    env=self._environment(tmp),
                )
                os.close(slave)
                try:
                    self.assertIn(b'picard> ', _read_until(master, b'picard> '))
                    # What Ctrl-C does: it cancels the line, and a new prompt comes.
                    shell.send_signal(signal.SIGINT)
                    self.assertIn(b'picard> ', _read_until(master, b'picard> '))
                    os.write(master, b'\x04')  # Ctrl-D leaves
                    output = _read_until(master, b'Traceback', timeout=10)
                    status = shell.wait(timeout=30)
                finally:
                    shell.kill()
                    shell.wait()
            finally:
                os.close(master)
        self.assertNotIn(b'Traceback', output)
        self.assertEqual(0, status)
