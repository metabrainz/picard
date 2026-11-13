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

"""A busy indicator for the commands of an interactive console that take time."""

from collections.abc import Callable
import logging
import threading

from picard import log
from picard.cli.output import CliOutput


_FRAMES = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
_ASCII_FRAMES = '|/-\\'

# Return to the start of the line and erase it.
_CLEAR_LINE = '\r\033[K'


def _frames_for(stream) -> str:
    """The frames the stream can show: the braille ones, or ASCII if its encoding cannot."""
    try:
        _FRAMES.encode(getattr(stream, 'encoding', None) or 'ascii')
    except UnicodeEncodeError:
        return _ASCII_FRAMES
    return _FRAMES


class BusyIndicator:
    """Show a spinner on the error stream while the ``with`` block runs, if it runs long enough.

    ``message`` is a function returning the text next to the spinner, called for
    each frame so that it can follow what the command is doing.

    A quick command shows nothing: the spinner only appears after ``delay``
    seconds. It is never shown when the output has no color (``--no-color``,
    ``NO_COLOR``, or not a terminal) or when the error stream is not a
    terminal, so redirected or scripted use is not changed. The line is erased
    when the block ends, including when it ends with an exception such as Ctrl-C,
    and before a log message is written to the same stream, so that the message
    does not follow the spinner on the same line.
    """

    def __init__(
        self,
        output: CliOutput,
        message: Callable[[], str],
        delay: float = 0.5,
        interval: float = 0.1,
    ):
        self._output = output
        self._message = message
        self._delay = delay
        self._interval = interval
        self._stream = output.stderr
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        # Held to write on the stream, whether a frame or the erasing of it.
        self._lock = threading.Lock()
        self._shown = False
        self._handlers: list[logging.Handler] = []

    def __enter__(self):
        if self._output.color and getattr(self._stream, 'isatty', lambda: False)():
            # The log messages written to our stream erase the spinner first.
            self._handlers = [
                handler
                for handler in log.main_logger.handlers
                if isinstance(handler, logging.StreamHandler) and handler.stream is self._stream
            ]
            for handler in self._handlers:
                handler.addFilter(self._erase_for_log)
            self._thread = threading.Thread(target=self._spin, name='busy-indicator', daemon=True)
            self._thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self._thread is not None:
            self._stop.set()
            self._thread.join()
            self._thread = None
            for handler in self._handlers:
                handler.removeFilter(self._erase_for_log)
            self._handlers = []
        return False

    def _erase_for_log(self, record) -> bool:
        """Filter of the log handlers: erase the spinner, the message is written next."""
        self._erase()
        return True

    def _erase(self):
        with self._lock:
            if self._shown:
                self._stream.write(_CLEAR_LINE)
                self._stream.flush()
                self._shown = False

    def _spin(self):
        # Event.wait returns True as soon as the block has ended.
        if self._stop.wait(self._delay):
            return
        frames = _frames_for(self._stream)
        index = 0
        try:
            while True:
                frame = frames[index % len(frames)]
                # Outside the lock: the message may log, and the log filter takes the lock to erase the line.
                text = self._output.d_busy(f"{frame} {self._message()}")
                with self._lock:
                    self._stream.write(f'{_CLEAR_LINE}{text}')
                    self._stream.flush()
                    self._shown = True
                index += 1
                if self._stop.wait(self._interval):
                    break
        finally:
            self._erase()
