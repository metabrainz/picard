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

import traceback
import Queue
from PyQt4 import QtCore


class HandlerThread(QtCore.QThread):

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.jobs = Queue.Queue()

    def add_job(self, handler, args):
        self.jobs.put((handler, args))

    def run(self):
        try:
            while True:
                handler, args = self.jobs.get_nowait()
                try:
                    handler(*args)
                except:
                    traceback.print_exc()
        except Queue.Empty:
            pass


class ThreadAssist(QtCore.QObject):

    def __init__(self, parent):
        QtCore.QObject.__init__(self, parent)
        self.to_main = Queue.Queue()
        self.connect(self, QtCore.SIGNAL("proxy_to_main()"),
                     self.__on_proxy_to_main, QtCore.Qt.QueuedConnection)
        self.threads = []
        self.max_threads = 10

    def stop(self):
        for thread in self.threads:
            self.log.debug("Waiting for thread %r", thread)
            thread.wait()

    def __on_proxy_to_main(self):
        handler, args = self.to_main.get()
        handler(*args)

    def proxy_to_main(self, handler, *args):
        """Invoke ``handler`` with arguments ``args`` in the main thread."""
        self.to_main.put((handler, args))
        self.emit(QtCore.SIGNAL("proxy_to_main()"))

    def allocate(self):
        """Allocate a new thread."""
        thread = HandlerThread(self)
        self.threads.append(thread)
        return thread

    def spawn(self, handler, *args, **kwargs):
        """Invoke ``handler`` with arguments ``args`` in a separate thread."""
        priority = kwargs.get("priority", QtCore.QThread.NormalPriority)
        thread = kwargs.get("thread")
        if not thread:
            # Find a free thread
            for t in self.threads:
                if t.isFinished():
                    thread = t
                    break
            else:
                # Find the least used thread
                if len(self.threads) >= self.max_threads:
                    min_jobs = 10000
                    for t in self.threads:
                        jobs = t.jobs.qsize()
                        if jobs < min_jobs:
                            min_jobs = jobs
                            thread = t
                # Allocate a new thread
                else:
                    thread = self.allocate()
        thread.add_job(handler, args)
        thread.start(priority)
