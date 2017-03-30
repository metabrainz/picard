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

# NOTES:
# Threads in Python do NOT operate as you would expect because of Python's Global Interpreter Lock (GIL).
# 1. The GIL essentially allows only one Python thread to execute at any time -
#    threads do NOT execute in parallel on a multi-processor system.
#    (Indeed because of the way this works in Py2 & Py3.1, multi-threading actually
#    works better on a single processor system - or with Python execution constrained
#    to a single processor using affinity - than on a multi-processor system.
#    O/S thread priorities also make little or no difference to which thread is executed.
#    In Py3.2, the GIL was changed to make the choice of thread to execute a little better
#    but Python is still constrained by the GIL to executing a single thread at any time.)
# 2. Threads give up CPU in only 3 circumstances:
#    a. After a certain number of Python byte-code instructions - but it is possible
#       that the same thread will get control again (or even likely or even highly likely -
#       because this thread is already running whilst the O/S has to schedule other threads).
#    b. When a thread has to wait for disk I/O (or other blocking activities)
#    c. When a thread explicitly sleeps.
# 3. Qt runs in an event loop on the main thread - the UI can only respond to user actions
#    and other queued events (like log / status messages) when the main thread is:
#    a. not executing any other code
#    b. is not executing a blacking operation (like I/O) and
#    c. has the GIL (i.e. another thread is not executing)
#    and can therefore process the event queue.
#
# See http://www.dabeaz.com/python/UnderstandingGIL.pdf for an explanation.
#
# As a consequence, the following rules are proposed to help keep the UI responsive:
# 1. All disk I/O and other blocking operations should run in worker threads.
# 2. The number of simultaneous threads should be kept as small as possible as the
#    overheads for switching threads grow exponentially with the number of threads.
#    Ideally we want the minimum number of threads to:
#    a. Maximise but not overload disk I/O
#    b. Allow UI to show multiple activities happening in parallel e.g. directory walking
#       in parallel with guess format in parallel with file loading
#    c. Save files (can only be one file save thread to avoid conflicting writes).
#    d. Process CPU-only workload
#    e. Plus main-thread for UI.
# 3. Qt requires any UI operations need to run in the main thread.
# 4. All CPU intensive work or potentially high-volume activities (i.e. if the user asks
#    for an activity on a large number of files) should run in worker-threads.
# 5. Worker-thread activity that results in a callback for UI changes should be broken into
#    the smallest possible pieces to execute on the worker-thread so that call-back activity is small.
#    If necessary the work to break this into small pieces can itself be run in a worker-thread.
# 6. Worker-threads should sleep for 1ms every so often to give main thread a chance to run
#    to keep UI responsive. Worker threads should also sleep before exit to avoid next thread-pool
#    running without giving chance for other threads to execute.
# 7. Direct main-thread processing of a CPU-intensive UI action can call QCoreApplication.processEvents to
#    keep UI responsive (though CPUintensive code is better run in a worker thread if possible).
#    BUT QCoreApplication.processEvents MUST NOT BE RUN FROM A WORKER-THREAD CALL-BACK as
#    a new worker-thread and its callback may be executed before the remainder of this call-back
#    leading to Python Recursion Level Exceeded errors.

import sys
import traceback
from time import time
from PyQt4.QtCore import QRunnable, QCoreApplication, QEvent, QThread, QMutex
from picard.util import throttle


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
        sleep_now()


def run_task(func, next, priority=0, thread_pool=None):
    if thread_pool is None:
        thread_pool = QCoreApplication.instance().thread_pool
    thread_pool.start(Runnable(func, next), priority)


thread_processEvents_throttle = 100
thread_sleep_throttle = 100
thread_throttle_mutex = QMutex()
thread_processEvents_last = thread_sleep_last = time()
def thread_throttle(throttle, last, func):
    thread_throttle_mutex.lock()
    now = time()
    if (now - last) * 1000.0 < throttle:
        thread_throttle_mutex.unlock()
        return
    last = now
    thread_throttle_mutex.unlock()
    func()


def to_main(func, *args, **kwargs):
    if func is not None:
        QCoreApplication.postEvent(QCoreApplication.instance(),
                                    ProxyToMainEvent(func, *args, **kwargs))
        # Cannot run processEvents here because it may be running a worker-thread
        # call-back in the main-thread e.g. calling debug.log
        sleep()


def processEvents():
    if QCoreApplication.instance():
        if QCoreApplication.instance().thread() == QThread.currentThread():
            thread_throttle(thread_processEvents_throttle, thread_processEvents_last, QCoreApplication.processEvents)
        else:
            sleep()


def sleep():
    thread_throttle(thread_sleep_throttle, thread_sleep_last, sleep_now)

def sleep_now():
    if QCoreApplication.instance() and QCoreApplication.instance().thread() != QThread.currentThread():
        thread_throttle_mutex.lock()
        thread_sleep_last = time()
        thread_throttle_mutex.unlock()
        QThread.currentThread().msleep(10)
