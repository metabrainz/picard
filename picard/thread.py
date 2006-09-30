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
from PyQt4 import QtCore
from picard.util import LockableDict


class HandlerThread(QtCore.QThread):

    def set_handler(self, handler, args):
        self.handler = handler
        self.args = args

    def run(self):
        try:
            self.handler(*self.args)
        except:
            traceback.print_exc()


class ThreadAssist(QtCore.QObject):

    def __init__(self, parent):
        QtCore.QObject.__init__(self, parent)
        self.to_main = LockableDict()
        self.connect(self,
                     QtCore.SIGNAL("proxy_to_main(int, PyObject*, PyObject*)"),
                     self.__on_proxy_to_main, QtCore.Qt.QueuedConnection)
        self.threads = []

    def __on_proxy_to_main(self, obj_id, handler, args):
        handler(*args)
        self.to_main.lock_for_write()
        try:
            del self.to_main[obj_id]
        finally:
            self.to_main.unlock()

    def proxy_to_main(self, handler, args):
        """Invoke ``handler`` with arguments ``args`` in the main thread."""
        self.to_main.lock_for_write()
        try:
            obj = (handler, args)
            obj_id = id(obj)
            self.to_main[obj_id] = obj
            self.emit(QtCore.SIGNAL("proxy_to_main(int, PyObject*, PyObject*)"),
                      obj_id, handler, args)
        finally:
            self.to_main.unlock()

    def spawn(self, handler, args=(), priority=QtCore.QThread.LowPriority):
        """Invoke ``handler`` with arguments ``args`` in a separate thread."""
        thread = None
        for t in self.threads:
            if t.isFinished():
                thread = t
                break
        if not thread:
            thread = HandlerThread(self)
            self.threads.append(thread)
        thread.set_handler(handler, args)
        thread.start(priority)

