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

import io
import logging
import threading
import time

from test.picardtestcase import PicardTestCase

from picard import log
from picard.cli.busy import BusyIndicator
from picard.cli.output import CliOutput


class _Terminal(io.StringIO):
    encoding = 'utf-8'

    def isatty(self):
        return True


def _output(stream, color=True):
    return CliOutput(stdout=io.StringIO(), stderr=stream, color=color)


class BusyIndicatorTest(PicardTestCase):
    def test_nothing_is_shown_for_a_quick_block(self):
        stream = _Terminal()
        with BusyIndicator(_output(stream), lambda: 'busy', delay=10):
            pass
        self.assertEqual('', stream.getvalue())

    def test_nothing_is_shown_when_not_a_terminal(self):
        stream = io.StringIO()
        with BusyIndicator(_output(stream), lambda: 'busy', delay=0, interval=0.01):
            time.sleep(0.05)
        self.assertEqual('', stream.getvalue())

    def test_spinner_is_shown_for_a_long_block_and_erased_after(self):
        stream = _Terminal()
        with BusyIndicator(_output(stream), lambda: 'busy', delay=0, interval=0.01):
            time.sleep(0.1)
        text = stream.getvalue()
        self.assertIn('busy', text)
        self.assertTrue(text.endswith('\r\033[K'))

    def test_spinner_is_erased_when_the_block_raises(self):
        stream = _Terminal()
        with self.assertRaises(KeyboardInterrupt):
            with BusyIndicator(_output(stream), lambda: 'busy', delay=0, interval=0.01):
                time.sleep(0.05)
                raise KeyboardInterrupt
        self.assertTrue(stream.getvalue().endswith('\r\033[K'))

    def test_ascii_frames_when_the_encoding_cannot_show_braille(self):
        stream = _Terminal()
        stream.encoding = 'ascii'
        with BusyIndicator(_output(stream), lambda: 'busy', delay=0, interval=0.01):
            time.sleep(0.05)
        self.assertIn('| ', stream.getvalue())

    def test_nothing_is_shown_without_color(self):
        stream = _Terminal()
        with BusyIndicator(_output(stream, color=False), lambda: 'busy', delay=0, interval=0.01):
            time.sleep(0.05)
        self.assertEqual('', stream.getvalue())

    def test_message_can_follow_what_the_command_does(self):
        stream = _Terminal()
        messages = iter(['first', 'second'] + ['last'] * 100)
        with BusyIndicator(_output(stream), lambda: next(messages), delay=0, interval=0.01):
            time.sleep(0.1)
        text = stream.getvalue()
        self.assertIn('first', text)
        self.assertIn('second', text)

    def test_the_spinner_is_erased_before_a_log_message_to_the_same_stream(self):
        stream = _Terminal()
        handler = logging.StreamHandler(stream)
        log.main_logger.addHandler(handler)
        self.addCleanup(log.main_logger.removeHandler, handler)
        with BusyIndicator(_output(stream), lambda: 'busy', delay=0, interval=10):
            time.sleep(0.1)
            log.main_logger.error('boom')
        text = stream.getvalue()
        self.assertIn('\r\033[Kboom', text)
        self.assertEqual([], handler.filters)

    def test_a_message_that_logs_does_not_block_the_spinner(self):
        stream = _Terminal()
        handler = logging.StreamHandler(stream)
        log.main_logger.addHandler(handler)
        self.addCleanup(log.main_logger.removeHandler, handler)

        def message():
            log.main_logger.error('while choosing the message')
            return 'busy'

        def run():
            with BusyIndicator(_output(stream), message, delay=0, interval=0.01):
                time.sleep(0.1)

        # A deadlock would never end, so the block runs in a thread that is given up on.
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        thread.join(5)
        self.assertFalse(thread.is_alive(), "the spinner is stuck")

    def test_other_handlers_are_left_alone(self):
        handler = logging.StreamHandler(io.StringIO())
        log.main_logger.addHandler(handler)
        self.addCleanup(log.main_logger.removeHandler, handler)
        stream = _Terminal()
        with BusyIndicator(_output(stream), lambda: 'busy', delay=0, interval=0.01):
            self.assertEqual([], handler.filters)
