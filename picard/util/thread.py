# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013, 2018, 2020-2021 Laurent Monin
# Copyright (C) 2016 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020, 2022 Philipp Wolfer
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


from functools import partial
import sys
import traceback

from PyQt5.QtCore import (
    QCoreApplication,
    QEvent,
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


def future_callback(callback, future, log_traceback=True):
    try:
        result = future.result()
        error = None
    except BaseException:
        if log_traceback:
            log.error(traceback.format_exc())
        result = None
        error = sys.exc_info()[1]
    to_main(callback, result=result, error=error)


def run_task(func, next_func, priority=0, thread_pool=None, traceback=True):
    """Schedules func to be run on a separate thread

    Args:
        func: Function to run on a separate thread.
        next_func: Callback function to run after the thread has been completed.
          The callback will be run on the main thread.
        priority: Deprecated, for backward compatibility only
        thread_pool: Instance of concurrent.futures.Executor to run this task.
        traceback: If set to true the stack trace will be logged to the error log
          if an exception was raised.

    Returns:
        An instance of concurrent.futures.Future
    """
    if not thread_pool:
        thread_pool = QCoreApplication.instance().thread_pool
    future = thread_pool.submit(func)
    future.add_done_callback(partial(future_callback, next_func, log_traceback=traceback))
    return future


def to_main(func, *args, **kwargs):
    QCoreApplication.postEvent(QCoreApplication.instance(),
                               ProxyToMainEvent(func, *args, **kwargs))
