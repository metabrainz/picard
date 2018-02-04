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
from collections import deque
from PyQt5 import QtCore
from picard.util import thread


LOG_INFO = 1
LOG_WARNING = 2
LOG_ERROR = 4
LOG_DEBUG = 8


def _onestr2set(domains):
    if isinstance(domains, str):
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
        if self.domains:
            if show_set:
                show_set = _onestr2set(show_set)
                if self.domains.isdisjoint(show_set):
                    return False
            if hide_set:
                hide_set = _onestr2set(hide_set)
                if self.domains.intersection(hide_set):
                    return False
        if verbosity is not None and self.level not in verbosity:
            return False
        return True

    def domains_as_string(self):
        if not self.domains:
            return ""
        return "|".join(self.domains)


class Logger(object):

    def __init__(self, maxlen=0):
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
        if not self.log_level(level):
            return
        if domains is not None:
            domains = _onestr2set(domains)
            self.known_domains.update(domains)
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

    def log_level(self, level):
        return True


# main logger
log_levels = LOG_INFO | LOG_WARNING | LOG_ERROR

main_logger = Logger(50000)
main_logger.log_level = lambda level: log_levels & level


def debug(message, *args, domains=None):
    main_logger.message(LOG_DEBUG, message, *args, domains=domains)


def info(message, *args, domains=None):
    main_logger.message(LOG_INFO, message, *args, domains=domains)


def warning(message, *args, domains=None):
    main_logger.message(LOG_WARNING, message, *args, domains=domains)


def error(message, *args, domains=None):
    main_logger.message(LOG_ERROR, message, *args, domains=domains)


_log_prefixes = {
    LOG_INFO: 'I',
    LOG_WARNING: 'W',
    LOG_ERROR: 'E',
    LOG_DEBUG: 'D',
}


def formatted_log_line(message_obj, timefmt='hh:mm:ss',
                       level_prefixes=None, format='%s %s'):
    msg = format % (message_obj.time.toString(timefmt), message_obj.message)
    if level_prefixes is None:
        level_prefixes = _log_prefixes
    if level_prefixes:
        return "%s: %s" % (level_prefixes[message_obj.level], msg)
    else:
        return msg


def _stderr_receiver(message_obj):
    try:
        sys.stderr.write(formatted_log_line(message_obj) + os.linesep)
    except (UnicodeDecodeError, UnicodeEncodeError):
        sys.stderr.write(formatted_log_line(message_obj, format='%s %r') + os.linesep)


main_logger.register_receiver(_stderr_receiver)


# history of status messages
history_logger = Logger(50000)
history_logger.log_level = lambda level: log_levels & level


def history_info(message, *args):
    history_logger.message(LOG_INFO, message, *args)
