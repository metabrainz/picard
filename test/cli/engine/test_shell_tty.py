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


"""The shell on a real terminal: Ctrl-C and Ctrl-D at the prompt."""

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
