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

import io
import logging
import os
import sys
import traceback

from collections import deque, namedtuple, OrderedDict
from functools import partial, wraps
from PyQt5 import QtCore


_MAX_TAIL_LEN = 10**6


def domain(*domains):
    def wrapper(f):
        @wraps(f)
        def caller(*args, **kwargs):
            log = sys.modules['picard.log']
            saved = {}
            methods = ('debug', 'info', 'error', 'warning')
            for method in methods:
                saved[method] = getattr(log, method)
                setattr(log, method, partial(
                    saved[method], domains=set(domains)))
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


def _DummyFn(*args, **kwargs):
    """Placeholder function.

    Raises:
        NotImplementedError
    """
    _, _ = args, kwargs
    raise NotImplementedError()


# _srcfile is used when walking the stack to check when we've got the first
# caller stack frame, by skipping frames whose filename is that of this
# module's source. It therefore should contain the filename of this module's
# source file.
_srcfile = os.path.normcase(_DummyFn.__code__.co_filename)
if hasattr(sys, '_getframe'):
    def currentframe():
        return sys._getframe(3)
else:  # pragma: no cover
    def currentframe():
        """Return the frame object for the caller's stack frame."""
        try:
            raise Exception
        except Exception:
            return sys.exc_info()[2].tb_frame.f_back


class OurLogger(logging.getLoggerClass()):

    @staticmethod
    def _fix_kwargs(kwargs):
        key = 'domains'
        if key in kwargs:
            kv_dict = {key: kwargs[key]}
            if 'extra' in kwargs:
                kwargs['extra'].update(kv_dict)
            else:
                kwargs['extra'] = kv_dict
            del kwargs[key]
        return kwargs

    def log(self, level, msg, *args, **kwargs):
        kwargs = self._fix_kwargs(kwargs)
        super().log(level, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        kwargs = self._fix_kwargs(kwargs)
        super().debug(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        kwargs = self._fix_kwargs(kwargs)
        super().error(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        kwargs = self._fix_kwargs(kwargs)
        super().warning(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        kwargs = self._fix_kwargs(kwargs)
        super().info(msg, *args, **kwargs)

    # copied from https://github.com/python/cpython/blob/3.5/Lib/logging/__init__.py#L1353-L1381
    # see https://stackoverflow.com/questions/4957858/how-to-write-own-logging-methods-for-own-logging-levels
    def findCaller(self, stack_info=False):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = currentframe()
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)", None
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == _srcfile:
                f = f.f_back
                continue
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                sio.write('Stack (most recent call last):\n')
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
                sio.close()
            rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
            break
        return rv


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

    def clear(self):
        self._log_queue.clear()
        self.known_domains = set()


# MAIN LOGGER

logging.setLoggerClass(OurLogger)

main_logger = logging.getLogger('main')

main_logger.setLevel(logging.INFO)


def name_filter(record):
    # provide a significant name, because module sucks
    logpydir = os.path.dirname(os.path.realpath(__file__))
    pathname = os.path.realpath(record.pathname)
    record.name, _ = os.path.splitext(os.path.relpath(pathname, logpydir))
    return True


main_logger.addFilter(name_filter)

main_tail = TailLogger(_MAX_TAIL_LEN)

main_fmt = '%(levelname).1s: %(asctime)s,%(msecs)03d %(name)s %(funcName)s(): %(message)s'
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
