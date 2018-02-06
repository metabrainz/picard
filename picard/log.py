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

import sys
import os
import logging

from collections import deque, namedtuple, OrderedDict
from functools import partial, wraps
from PyQt5 import QtCore

from picard.util import thread


def domain(*domains):
    def wrapper(f):
        @wraps(f)
        def caller(*args, **kwargs):
            extra = {'domains': set(domains)}
            log = sys.modules['picard.log']
            saved = {}
            methods = ('debug', 'info', 'error', 'warning')
            for method in methods:
                saved[method] = getattr(log, method)
                setattr(log, method, partial(saved[method], extra=extra))
            result = f(*args, **kwargs)
            for method in methods:
                setattr(log, method, saved[method])
            return result
        return caller
    return wrapper


def debug_mode(enabled):
    if enabled:
        main_logger.setLevel(logging.DEBUG)
    else:
        main_logger.setLevel(logging.INFO)



_feat = namedtuple('_feat', ['name', 'prefix', 'fgcolor'])

levels_features = OrderedDict([
    (logging.INFO,    _feat('Info',    'I', 'black')),
    (logging.WARNING, _feat('Warning', 'W', 'darkorange')),
    (logging.ERROR,   _feat('Error',   'E', 'red')),
    (logging.DEBUG,   _feat('Debug',   'D', 'purple')),
])


# COMMON CLASSES


TailLogTuple = namedtuple(
    'TailLogTuple', ['pos', 'message', 'level', 'domains'])


class TailLogHandler(logging.Handler):

    def __init__(self, log_queue, tail_logger):
        super().__init__()
        self.log_queue = log_queue
        self.tail_logger = tail_logger
        self.pos = 0

    def emit(self, record):
        domains = getattr(record, 'domains', None)
        if domains and not domains.issubset(self.tail_logger.known_domains):
            self.tail_logger.known_domains.update(domains)
            self.tail_logger.domains_updated.emit()
        self.log_queue.append(
            TailLogTuple(
                self.pos,
                self.format(record),
                record.levelno,
                domains
            )
        )
        self.pos += 1
        self.tail_logger.updated.emit()


class TailLogger(QtCore.QObject):
    updated = QtCore.pyqtSignal()
    domains_updated = QtCore.pyqtSignal()

    def __init__(self, maxlen):
        super().__init__()
        self._log_queue = deque(maxlen=maxlen)
        self.known_domains = set()
        self.log_handler = TailLogHandler(self._log_queue, self)

    def contents(self, prev=-1):
        return [x for x in self._log_queue if x.pos > prev]


# MAIN LOGGER


main_logger = logging.getLogger('main')

main_logger.setLevel(logging.INFO)

main_tail = TailLogger(100000)

main_handler = main_tail.log_handler
main_formatter = logging.Formatter('%(asctime)s %(message)s', '%H:%M:%S')
main_handler.setFormatter(main_formatter)

main_logger.addHandler(main_handler)

main_console_handler = logging.StreamHandler()
main_console_formatter = logging.Formatter(
    '%(levelname).1s: %(asctime)s,%(msecs)03d %(module)s %(funcName)s: %(message)s',
    '%H:%M:%S'
)
main_console_handler.setFormatter(main_console_formatter)

main_logger.addHandler(main_console_handler)


debug = main_logger.debug
info = main_logger.info
warning = main_logger.warning
error = main_logger.error


# HISTORY LOGGING


history_logger = logging.getLogger('history')
history_logger.setLevel(logging.INFO)

history_tail = TailLogger(100000)

history_handler = history_tail.log_handler
history_formatter = logging.Formatter('%(asctime)s - %(message)s')
history_handler.setFormatter(history_formatter)

history_logger.addHandler(history_handler)


def history_info(message, *args):
    history_logger.info(message, *args)
