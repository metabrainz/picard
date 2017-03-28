# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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
import traceback
from PyQt4.QtCore import QRunnable, QCoreApplication, QEvent, QThread


class ProxyToMainEvent(QEvent):

    def __init__(self, func, *args, **kwargs):
        QEvent.__init__(self, QEvent.User)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.func(*self.args, **self.kwargs)


class Runnable(QRunnable):

    def __init__(self, func, next):
        QRunnable.__init__(self)
        self.func = func
        self.next = next

    def run(self):
        try:
            result = self.func()
        except:
            from picard import log
            log.error(traceback.format_exc())
            to_main(self.next, error=sys.exc_info()[1])
        else:
            to_main(self.next, result=result)


def run_task(func, next, priority=0, thread_pool=None):
    if thread_pool is None:
        thread_pool = QCoreApplication.instance().thread_pool
    thread_pool.start(Runnable(func, next), priority)


def to_main(func, *args, **kwargs):
    # TODO Sophist
    # At present we use processEvents which both processes events sent to the generic window
    # and processes UI events as well.
    # We should consider whether we would have greater control over returning here if we either
    # a. Use processEvents with flags to exclude user events or socket notifiers; or
    # b. Use a specific event receiver for to_main rather than the generic receiver and use
    # sendPostedEvents to execute this code.
    # c.Use signals rather than events to execute code on the main thread
    # see http://www.qtcentre.org/threads/7167-Main-thread-worker-thread-communication
    # My current thoughts are that these are no more likely to switch back to this task,
    # and just avoid processing UI events which we want processed to keep the UI responsive.
    # TODO Sophist
    if func is not None:
        QCoreApplication.postEvent(QCoreApplication.instance(),
                                   ProxyToMainEvent(func, *args, **kwargs))
    processEvents()


def processEvents():
   if QCoreApplication.instance() and QCoreApplication.instance().thread() != QThread.currentThread():
        # If we are in a worker thread, use QApplication.processEvents to pass control to the
        # main thread to execute the event we just posted. If we don't do this
        # the main thread may not get CPU to process the function for a long time.
        # See http://www.dabeaz.com/python/UnderstandingGIL.pdf for details.
        #
        # If we are in the main thread and post the event and call processEvents then,
        # IF there are worker threads queued, it is possible (or based on experience likely)
        # that instead of returning here and finish executing to_main, instead
        # Python will dispatch a worker thread which will finish by running to_main again.
        # The multiple instances of to_main will only finish executing when there is no other work.
        # With sufficient worker thread tasks queued, we will get Recursion Level Exceeded errors.
        #
        # Calling from within a worker thread is OK because the number of threads
        # in thread pools is small and well below Python's recursion limit.
        QCoreApplication.instance().processEvents()
        # Sleep this thread for a few ms to allow main thread to get CPU.
        # TODO Python 3 has a different thread dispatch mechanism which needs to be tested
        QThread.currentThread().msleep(10)
