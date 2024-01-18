# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013, 2018, 2020-2024 Laurent Monin
# Copyright (C) 2016 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020, 2022 Philipp Wolfer
# Copyright (C) 2022 Bob Swift
# Copyright (C) 2022 skelly37
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
import time
import traceback

from PyQt6.QtCore import (
    QCoreApplication,
    QEvent,
    QRunnable,
)

from picard import log


class ProxyToMainEvent(QEvent):

    def __init__(self, func, *args, **kwargs):
        super().__init__(QEvent.Type.User)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.func(*self.args, **self.kwargs)


class Runnable(QRunnable):

    def __init__(self, func, next_func, traceback=True):
        super().__init__()
        self.func = func
        self.next_func = next_func
        self.traceback = traceback

    def run(self):
        try:
            result = self.func()
        except BaseException:
            if self.traceback:
                log.error(traceback.format_exc())
            to_main(self.next_func, error=sys.exc_info()[1])
        else:
            to_main(self.next_func, result=result)


def run_task(func, next_func=None, priority=0, thread_pool=None, traceback=True):
    """Schedules func to be run on a separate thread

    Args:
        func: Function to run on a separate thread.
        next_func: Callback function to run after the thread has been completed.
          The callback will be run on the main thread.
        priority: Priority for the run queue's order of execution.
        thread_pool: Instance of concurrent.futures.Executor to run this task.
        traceback: If set to true the stack trace will be logged to the error log
          if an exception was raised.

    Returns:
        An instance of concurrent.futures.Future
    """
    def _no_operation(*args, **kwargs):
        return

    if not next_func:
        next_func = _no_operation

    if not thread_pool:
        thread_pool = QCoreApplication.instance().thread_pool
    thread_pool.start(Runnable(func, next_func, traceback), priority)


def to_main(func, *args, **kwargs):
    QCoreApplication.postEvent(QCoreApplication.instance(),
                               ProxyToMainEvent(func, *args, **kwargs))


def to_main_with_blocking(func, *args, **kwargs):
    """Executes a command as a user-defined event, and waits until the event has
    closed before returning.  Note that any new threads started while processing
    the event will not be considered when releasing the blocking of the function.

    Args:
        func: Function to run.
    """
    _task = ProxyToMainEvent(func, *args, **kwargs)
    QCoreApplication.postEvent(QCoreApplication.instance(), _task)

    while True:
        try:
            if not _task.isAccepted():
                break
        except Exception:
            break
        time.sleep(.01)
