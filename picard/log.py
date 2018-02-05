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


def debug(message, *args, domains=None):
    main_logger.message(logging.DEBUG, message, *args, domains=domains)


def info(message, *args, domains=None):
    main_logger.message(logging.INFO, message, *args, domains=domains)


def warning(message, *args, domains=None):
    main_logger.message(logging.WARNING, message, *args, domains=domains)


def error(message, *args, domains=None):
    main_logger.message(logging.ERROR, message, *args, domains=domains)


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


def _stderr_receiver(message_obj):
    try:
        sys.stderr.write(formatted_log_line(message_obj) + os.linesep)
    except (UnicodeDecodeError, UnicodeEncodeError):
        sys.stderr.write(formatted_log_line(message_obj, fmt='%s %r') + os.linesep)


main_logger.register_receiver(_stderr_receiver)


# history of status messages
history_logger = Logger(50000)
history_logger.log_level = logging.INFO


def history_info(message, *args):
    history_logger.message(logging.INFO, message, *args)
