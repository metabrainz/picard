# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007, 2011 Lukáš Lalinský
# Copyright (C) 2008-2010, 2019, 2021 Philipp Wolfer
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013, 2015, 2018-2019 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2021 Gabriel Ferreira
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


from collections import (
    OrderedDict,
    deque,
    namedtuple,
)
import logging
import os
from threading import Lock

from PyQt5 import QtCore


_MAX_TAIL_LEN = 10**6

VERBOSITY_DEFAULT = logging.WARNING


def set_level(level):
    main_logger.setLevel(level)


def get_effective_level():
    return main_logger.getEffectiveLevel()


_feat = namedtuple('_feat', ['name', 'prefix', 'color_key'])

levels_features = OrderedDict([
    (logging.ERROR,   _feat('Error',   'E', 'log_error')),
    (logging.WARNING, _feat('Warning', 'W', 'log_warning')),
    (logging.INFO,    _feat('Info',    'I', 'log_info')),
    (logging.DEBUG,   _feat('Debug',   'D', 'log_debug')),
])


# COMMON CLASSES


TailLogTuple = namedtuple(
    'TailLogTuple', ['pos', 'message', 'level'])


class TailLogHandler(logging.Handler):

    def __init__(self, log_queue, tail_logger, log_queue_lock):
        super().__init__()
        self.log_queue = log_queue
        self.tail_logger = tail_logger
        self.log_queue_lock = log_queue_lock
        self.pos = 0

    def emit(self, record):
        with self.log_queue_lock:
            self.log_queue.append(
                TailLogTuple(
                    self.pos,
                    self.format(record),
                    record.levelno
                )
            )
            self.pos += 1
        self.tail_logger.updated.emit()


def _calculate_bounds(previous_position, first_position, last_position, queue_length):
    # If first item of the queue is bigger than prev, use first item position - 1 as prev
    # e.g. queue = [8, 9, 10] , prev = 6, new_prev = 8-1 = 7
    if previous_position < first_position:
        previous_position = first_position-1

    # The offset of the first item in the queue is
    # equal to the length of the queue, minus the length to be printed
    offset = queue_length - (last_position - previous_position)

    # If prev > last_position, offset will be bigger than queue length offset > queue_length
    # This will force an empty list
    if offset > queue_length:
        offset = queue_length

    # If offset < 1, there is a discontinuity in the queue positions
    # Setting queue_length to 0 informs the caller that something is wrong and the slow path should be taken
    return offset, queue_length


class TailLogger(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    def __init__(self, maxlen):
        super().__init__()
        self._log_queue = deque(maxlen=maxlen)
        self._queue_lock = Lock()
        self.log_handler = TailLogHandler(self._log_queue, self, self._queue_lock)

    def contents(self, prev=-1):
        with self._queue_lock:
            # If log queue is empty, return
            if not self._log_queue:
                return []
            offset, length = _calculate_bounds(prev, self._log_queue[0].pos, self._log_queue[-1].pos, len(self._log_queue))

            if offset >= 0:
                return (self._log_queue[i] for i in range(offset, length))
                # If offset < 0, there is a discontinuity in the queue positions
                # Use a slower approach to get the new content.
            else:
                return (x for x in self._log_queue if x.pos > prev)

    def clear(self):
        with self._queue_lock:
            self._log_queue.clear()


# MAIN LOGGER

main_logger = logging.getLogger('main')

main_logger.setLevel(logging.INFO)


def name_filter(record):
    # provide a significant name from the filepath of the module
    name, _ = os.path.splitext(os.path.normpath(record.pathname))
    prefix = os.path.normpath(__package__)
    # In case the module exists within picard, remove the picard prefix
    # else, in case of something like a plugin, keep the path as it is.
    if name.startswith(prefix):
        name = name[len(prefix) + 1:].replace(os.sep, ".").replace('.__init__', '')
    record.name = name
    return True


main_logger.addFilter(name_filter)

main_tail = TailLogger(_MAX_TAIL_LEN)

main_fmt = '%(levelname).1s: %(asctime)s,%(msecs)03d %(name)s.%(funcName)s:%(lineno)d: %(message)s'
main_time_fmt = '%H:%M:%S'
main_inapp_fmt = main_fmt
main_inapp_time_fmt = main_time_fmt

main_handler = main_tail.log_handler
main_formatter = logging.Formatter(main_inapp_fmt, main_inapp_time_fmt)
main_handler.setFormatter(main_formatter)

main_logger.addHandler(main_handler)

main_console_handler = logging.StreamHandler()
main_console_formatter = logging.Formatter(main_fmt, main_time_fmt)

main_console_handler.setFormatter(main_console_formatter)

main_logger.addHandler(main_console_handler)


debug = main_logger.debug
info = main_logger.info
warning = main_logger.warning
error = main_logger.error
exception = main_logger.exception
log = main_logger.log

# HISTORY LOGGING


history_logger = logging.getLogger('history')
history_logger.setLevel(logging.INFO)

history_tail = TailLogger(_MAX_TAIL_LEN)

history_handler = history_tail.log_handler
history_formatter = logging.Formatter('%(asctime)s - %(message)s')
history_handler.setFormatter(history_formatter)

history_logger.addHandler(history_handler)


def history_info(message, *args):
    history_logger.info(message, *args)
