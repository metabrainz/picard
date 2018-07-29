# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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

import logging
import os

from collections import deque, namedtuple, OrderedDict
from PyQt5 import QtCore
from threading import Lock

_MAX_TAIL_LEN = 10**6

VERBOSITY_DEFAULT = logging.WARNING


def debug_mode(enabled):
    if enabled:
        main_logger.setLevel(logging.DEBUG)
    else:
        main_logger.setLevel(VERBOSITY_DEFAULT)


_feat = namedtuple('_feat', ['name', 'prefix', 'fgcolor'])

levels_features = OrderedDict([
    (logging.ERROR,   _feat('Error',   'E', 'red')),
    (logging.WARNING, _feat('Warning', 'W', 'darkorange')),
    (logging.INFO,    _feat('Info',    'I', 'black')),
    (logging.DEBUG,   _feat('Debug',   'D', 'purple')),
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


class TailLogger(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    def __init__(self, maxlen):
        super().__init__()
        self._log_queue = deque(maxlen=maxlen)
        self._queue_lock = Lock()
        self.log_handler = TailLogHandler(self._log_queue, self, self._queue_lock)

    def contents(self, prev=-1):
        with self._queue_lock:
            contents = [x for x in self._log_queue if x.pos > prev]
        return contents

    def clear(self):
        with self.log_queue_lock:
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
