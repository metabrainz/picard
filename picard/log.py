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

from __future__ import print_function
import sys
import os
from collections import deque
from PyQt5 import QtCore
from picard.util import thread


LOG_INFO = 1
LOG_WARNING = 2
LOG_ERROR = 4
LOG_DEBUG = 8


class Logger(object):

    def __init__(self, maxlen=0):
        self._receivers = []
        self.maxlen = maxlen
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

    def message(self, level, message, *args):
        if not self.log_level(level):
            return
        if not isinstance(message, str):
            message = repr(message)
        if args:
            message = message % args
        time = QtCore.QTime.currentTime()
        message = "%s" % (message,)
        self.entries.append((level, time, message))
        for func in self._receivers:
            try:
                thread.to_main(func, level, time, message)
            except:
                import traceback
                traceback.print_exc()

    def log_level(self, level):
        return True


# main logger
log_levels = LOG_INFO | LOG_WARNING | LOG_ERROR

main_logger = Logger(50000)
main_logger.log_level = lambda level: log_levels & level


def debug(message, *args):
    main_logger.message(LOG_DEBUG, message, *args)


def info(message, *args):
    main_logger.message(LOG_INFO, message, *args)


def warning(message, *args):
    main_logger.message(LOG_WARNING, message, *args)


def error(message, *args):
    main_logger.message(LOG_ERROR, message, *args)


_log_prefixes = {
    LOG_INFO: 'I',
    LOG_WARNING: 'W',
    LOG_ERROR: 'E',
    LOG_DEBUG: 'D',
}


def formatted_log_line(level, time, message, timefmt='hh:mm:ss',
                       level_prefixes=_log_prefixes, format='%s %s'):
    msg = format % (time.toString(timefmt), message)
    if level_prefixes:
        return "%s: %s" % (level_prefixes[level], msg)
    else:
        return msg


def _stderr_receiver(level, time, msg):
    try:
        sys.stderr.write(formatted_log_line(level, time, msg) + os.linesep)
    except (UnicodeDecodeError, UnicodeEncodeError):
        sys.stderr.write(formatted_log_line(level, time, msg, format='%s %r') + os.linesep)


main_logger.register_receiver(_stderr_receiver)


# history of status messages
history_logger = Logger(50000)
history_logger.log_level = lambda level: log_levels & level


def history_info(message, *args):
    history_logger.message(LOG_INFO, message, *args)
