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
from PyQt5 import QtCore
from picard.util import thread


def _onestr2set(domains):
    if not domains:
        return set()
    elif isinstance(domains, str):
        # this is a shortcut: allow one to pass a domains as sole
        # argument, but use it as first argument of set
        return set((domains,))
    else:
        return set(domains)


class LogMessage(object):

    def __init__(self, level, time, message, domains):
        self.level = level
        self.time = time
        self.message = message
        self.domains = domains

    def is_shown(self, verbosity=None, show_set=None, hide_set=None):
        show = True
        if show_set:
            if not self.domains:
                show = False
            else:
                show_set = _onestr2set(show_set)
                if self.domains.isdisjoint(show_set):
                    show = False
        if self.domains and hide_set:
            hide_set = _onestr2set(hide_set)
            if self.domains.intersection(hide_set):
                return False
        if verbosity is not None and self.level not in verbosity:
            return False
        return show

    def domains_as_string(self):
        if not self.domains:
            return ""
        return "|".join(self.domains)


class Logger(QtCore.QObject):
    domains_updated = QtCore.pyqtSignal()

    def __init__(self, maxlen=0):
        super().__init__()
        self._receivers = []
        self.maxlen = maxlen
        self.known_domains = set()
        self.reset()

    def reset(self):
        if self.maxlen > 0:
            self.entries = deque(maxlen=self.maxlen)
        else:
            self.entries = []

    def register_receiver(self, receiver):
        self._receivers.append(receiver)

    def unregister_receiver(self, receiver):
        self._receivers.remove(receiver)

    def message(self, level, message, *args, domains=None):
        if level < self.log_level:
            return
        if domains is not None:
            domains = _onestr2set(domains)
            count = len(self.known_domains)
            self.known_domains.update(domains)
            if count != len(self.known_domains):
                self.domains_updated.emit()
        if not isinstance(message, str):
            message = repr(message)
        if args:
            message = message % args
        time = QtCore.QTime.currentTime()
        message = "%s" % (message,)
        message_obj = LogMessage(level, time, message, domains)
        self.entries.append(message_obj)
        for func in self._receivers:
            try:
                thread.to_main(func, message_obj)
            except:
                import traceback
                traceback.print_exc()


# main logger

main_logger = Logger(50000)
main_logger.log_level = logging.INFO


def debug_mode(enabled):
    if enabled:
        main_logger.log_level = logging.DEBUG
    else:
        main_logger.log_level = logging.INFO


def n_main_logger_wrapper(level, message, *args, domains=None):
    n_main_logger.log(level, message, *args,
                      extra={'domains': _onestr2set(domains)})


def debug(message, *args, domains=None):
    main_logger.message(logging.DEBUG, message, *args, domains=domains)
    n_main_logger_wrapper(logging.DEBUG, message, *args, domains=domains)


def info(message, *args, domains=None):
    main_logger.message(logging.INFO, message, *args, domains=domains)
    n_main_logger_wrapper(logging.INFO, message, *args, domains=domains)


def warning(message, *args, domains=None):
    main_logger.message(logging.WARNING, message, *args, domains=domains)
    n_main_logger_wrapper(logging.WARNING, message, *args, domains=domains)


def error(message, *args, domains=None):
    main_logger.message(logging.ERROR, message, *args, domains=domains)
    n_main_logger_wrapper(logging.ERROR, message, *args, domains=domains)


_feat = namedtuple('_feat', ['name', 'prefix', 'fgcolor'])

levels_features = OrderedDict([
    (logging.INFO,    _feat('Info',    'I', 'black')),
    (logging.WARNING, _feat('Warning', 'W', 'darkorange')),
    (logging.ERROR,   _feat('Error',   'E', 'red')),
    (logging.DEBUG,   _feat('Debug',   'D', 'purple')),
])


def formatted_log_line(message_obj, timefmt='hh:mm:ss',
                       level_prefixes=True, fmt='%s %s'):
    msg = fmt % (message_obj.time.toString(timefmt), message_obj.message)
    if level_prefixes:
        return "%s: %s" % (levels_features[message_obj.level].prefix, msg)
    else:
        return msg


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


n_main_logger = logging.getLogger('main')

n_main_logger.setLevel(logging.DEBUG)

n_main_tail = TailLogger(100000)

n_main_handler = n_main_tail.log_handler
n_main_formatter = logging.Formatter('%(asctime)s %(message)s', '%H:%M:%S')
n_main_handler.setFormatter(n_main_formatter)

n_main_logger.addHandler(n_main_handler)

n_main_console_handler = logging.StreamHandler()
n_main_console_formatter = logging.Formatter(
    '%(levelname).1s: %(asctime)s,%(msecs)03d %(message)s',
    '%H:%M:%S'
)
n_main_console_handler.setFormatter(n_main_console_formatter)

n_main_logger.addHandler(n_main_console_handler)

# HISTORY LOGGING


history_logger = logging.getLogger('history')
history_logger.setLevel(logging.DEBUG)

history_tail = TailLogger(100000)

history_handler = history_tail.log_handler
history_formatter = logging.Formatter('%(asctime)s - %(message)s')
history_handler.setFormatter(history_formatter)

history_logger.addHandler(history_handler)


def history_info(message, *args):
    history_logger.info(message, *args)
