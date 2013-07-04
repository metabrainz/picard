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
from PyQt4 import QtCore
from picard.util import thread


LOG_INFO = 1
LOG_WARNING = 2
LOG_ERROR = 4
LOG_DEBUG = 8

entries = deque(maxlen=50000)
_receivers = []
log_levels = LOG_INFO|LOG_WARNING|LOG_ERROR


def register_receiver(receiver):
    _receivers.append(receiver)


def unregister_receiver(receiver):
    _receivers.remove(receiver)


def _message(level, message, args, kwargs):
    if not log_levels & level:
        return
    if not (isinstance(message, str) or isinstance(message, unicode)):
        message = repr(message)
    if args:
        message = message % args
    time = QtCore.QTime.currentTime()
    message = "%s" % (message,)
    if isinstance(message, unicode):
        message = message.encode("utf-8", "replace")
    entries.append((level, time, message))
    for func in _receivers:
        try:
            func(level, time, message)
        except Exception, e:
            import traceback
            traceback.print_exc()


def debug(message, *args, **kwargs):
    thread.proxy_to_main(_message, LOG_DEBUG, message, args, kwargs)


def info(message, *args, **kwargs):
    thread.proxy_to_main(_message, LOG_INFO, message, args, kwargs)


def warning(message, *args, **kwargs):
    thread.proxy_to_main(_message, LOG_WARNING, message, args, kwargs)


def error(message, *args, **kwargs):
    thread.proxy_to_main(_message, LOG_ERROR, message, args, kwargs)


_log_prefixes = {
    LOG_INFO: 'I',
    LOG_WARNING: 'W',
    LOG_ERROR: 'E',
    LOG_DEBUG: 'D',
}


def _stderr_receiver(level, time, msg):
    sys.stderr.write("%s: %s %s%s" % (_log_prefixes[level],
                                      time.toString('hh:mm:ss'), msg,
                                      os.linesep))


register_receiver(_stderr_receiver)
