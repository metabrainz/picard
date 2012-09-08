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
from PyQt4 import QtCore


class ProxyToMainEvent(QtCore.QEvent):

    def __init__(self, func, args, kwargs):
        QtCore.QEvent.__init__(self, QtCore.QEvent.User)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def call(self):
        self.func(*self.args, **self.kwargs)


class Thread(QtCore.QThread):

    def __init__(self, parent, queue):
        QtCore.QThread.__init__(self, parent)
        self.queue = queue
        self.stopping = False

    def stop(self):
        self.stopping = True
        self.queue.put(None)

    def run(self):
        while not self.stopping:
            item = self.queue.get()
            if item is None:
                continue
            self.run_item(item)

    def run_item(self, item):
        func, next, priority = item
        try:
            result = func()
        except:
            self.log.error(traceback.format_exc())
            self.to_main(next, priority, error=sys.exc_info()[1])
        else:
            self.to_main(next, priority, result=result)

    def to_main(self, func, priority, *args, **kwargs):
        event = ProxyToMainEvent(func, args, kwargs)
        QtCore.QCoreApplication.postEvent(self.parent(), event, priority)


class ThreadPool(QtCore.QObject):

    instance = None

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.threads = []
        ThreadPool.instance = self

    def start(self):
        for thread in self.threads:
            thread.start(QtCore.QThread.LowPriority)

    def stop(self):
        queues = set()
        for thread in self.threads:
            thread.stop()
            queues.add(thread.queue)
        for queue in queues:
            queue.unlock()

    def event(self, event):
        if isinstance(event, ProxyToMainEvent):
            try:
                event.call()
            except:
                self.log.error(traceback.format_exc())
            return True
        return False

    def call_from_thread(self, handler, *args, **kwargs):
        priority = kwargs.pop('priority', QtCore.Qt.LowEventPriority)
        event = ProxyToMainEvent(handler, args, kwargs)
        QtCore.QCoreApplication.postEvent(self, event, priority)


# REMOVEME
def proxy_to_main(handler, *args, **kwargs):
    ThreadPool.instance.call_from_thread(handler, *args, **kwargs)
