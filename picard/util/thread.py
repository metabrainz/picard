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
from picard.util.queue import Queue
from PyQt4 import QtCore


_queue = Queue()


class ProxyToMainEvent(QtCore.QEvent):

    def __init__(self, handler, args, kwargs):
        QtCore.QEvent.__init__(self, QtCore.QEvent.User)
        self.handler = handler
        self.args = args
        self.kwargs = kwargs

    def call(self):
        self.handler(*self.args, **self.kwargs)


class HandlerThread(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)
        #QtCore.QThread.__init__(self, parent)
        self.stopping = False

    def stop(self):
        self.stopping = True
        _queue.put(None)

    def run(self):
        self.log.debug("Starting thread")
        while True:
            item = _queue.get()
            if self.stopping or item is None:
                return
            self.log.debug("Running task %r", item)
            handler, args = item
            try:
                handler(*args)
            except:
                import traceback
                self.log.error(traceback.format_exc())

    def add_task(self, handler, *args):
        #handler(*args)
        _queue.put((handler, args))
        #if not self.isAlive():
        #    self.start()



class ThreadAssist(QtCore.QObject):

    def __init__(self, parent):
        QtCore.QObject.__init__(self, parent)
        ThreadAssist.instance = self
        self.to_main = Queue()
        self.threads = []
        self.max_threads = 2
        globals()['proxy_to_main'] = self.proxy_to_main

    def stop(self):
        self.to_main.unlock()
        for thread in self.threads:
            thread.stop()
        for thread in self.threads:
            self.log.debug("Waiting for thread %r", thread)
            self.to_main.unlock()
            thread.wait()

    def event(self, event):
        if isinstance(event, ProxyToMainEvent):
            try: event.call()
            except:
                import traceback
                self.log.error(traceback.format_exc())
            return True
        return False

    def proxy_to_main(self, handler, *args, **kwargs):
        """Invoke ``handler`` with arguments ``args`` in the main thread."""
        priority = kwargs.pop('priority', QtCore.Qt.LowEventPriority)
        event = ProxyToMainEvent(handler, args, kwargs)
        QtCore.QCoreApplication.postEvent(self, event, priority)

    def allocate(self):
        """Allocate a new thread."""
        thread = HandlerThread()
        self.threads.append(thread)
        thread.start(QtCore.QThread.LowPriority)
        thread.log = QtCore.QObject.log
        return thread


def proxy_to_main(handler, *args, **kwargs):
    ThreadAssist.instance.proxy_to_main(handler, *args, **kwargs)



class ProxyToMainEvent(QtCore.QEvent):

    def __init__(self, func, args, kwargs):
        QtCore.QEvent.__init__(self, QtCore.QEvent.User)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def call(self):
        self.func(*self.args, **self.kwargs)


class Thread(QtCore.QThread):

    queue = Queue()

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.stopping = False

    def run(self):
        while not self.stopping:
            item = Thread.queue.get()
            if item is None:
                continue
            func, next, priority = item
            try:
                result = func()
            except:
                self.to_main(next, priority, error=sys.exc_info()[1])
            else:
                self.to_main(next, priority, result=result)
            self.usleep(100)

    def to_main(self, func, priority, *args, **kwargs):
        event = ProxyToMainEvent(func, args, kwargs)
        QtCore.QCoreApplication.postEvent(self.parent(), event, priority)


class ThreadPool(QtCore.QObject):

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.threads = [Thread(self) for i in xrange(3)]

    def start(self):
        for thread in self.threads:
            thread.start(QtCore.QThread.LowPriority)

    def stop(self):
        for thread in self.threads:
            thread.stop()
        for thread in self.threads:
            thread.wait()

    def call(self, func, next, priority=QtCore.Qt.LowEventPriority):
        Thread.queue.put((func, next, priority))

    def event(self, event):
        if isinstance(event, ProxyToMainEvent):
            try: event.call()
            except:
                import traceback
                self.log.error(traceback.format_exc())
            return True
        return False
