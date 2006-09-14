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

import os.path
import sys
from PyQt4 import QtCore
from Queue import Queue
from picard.util import decode_filename, encode_filename

class WorkerThread(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.exit_thread = False
        self.queue = Queue()
        self.files = []

    def start(self):
        self.log.debug("Starting the worker thread")
        QtCore.QThread.start(self)
        self.setPriority(QtCore.QThread.LowPriority)

    def stop(self):
        self.log.debug("Stopping the worker thread")
        if self.isRunning():
            self.exit_thread = True
            self.queue.put(None)
            self.wait()

    def run(self):
        while not self.exit_thread:
            item = self.queue.get(True)
            if not item:
                continue
            item[0](item)
            if self.queue.empty():
                self.emit(QtCore.SIGNAL("statusBarMessage(const QString &)"),
                          QtCore.QString(_(u"Done")))

    def load_album(self, album):
        """Load the album information from MusicBrainz."""
        self.queue.put((self.do_load_album, album))

    def do_load_album(self, args):
        album = args[1]
        self.emit(QtCore.SIGNAL("statusBarMessage(const QString &)"),
                  QtCore.QString(_(u"Loading album %s ...") % album.id))
        album.load()
        self.emit(QtCore.SIGNAL("albumLoaded(const QString &)"), album.id)

    def read_directory(self, directory):
        """Read the directory recursively and add all files to the tagger."""
        self.queue.put((self.do_read_directory, directory))

    def do_read_directory(self, args):        
        root = args[1]
        self.emit(QtCore.SIGNAL("statusBarMessage(const QString &)"),
                  QtCore.QString(_("Reading directory %s ...") % root))
        files = QtCore.QStringList()
        for name in os.listdir(encode_filename(root)):
            name = os.path.join(root, name)
            if os.path.isdir(name):
                self.read_directory(name)
            else:
                files.append(QtCore.QString(decode_filename(name)))
        if files:
            self.emit(QtCore.SIGNAL("add_files(const QStringList &)"), files)

    def read_file(self, filename, opener):
        self.queue.put((self.do_read_file, (filename, opener)))

    def do_read_file(self, args):
        filename, opener = args[1]
        self.emit(QtCore.SIGNAL("statusBarMessage(const QString &)"),
                  QtCore.QString(_(u"Reading file %s ...") % filename))
        files = opener(filename)
        self.tagger.add_files(files)

    def save_file(self, file):
        self.queue.put((self.do_save_file, file))

    def do_save_file(self, args):
        file = args[1]
        self.log.debug("Saving file %s", file)
        self.emit(QtCore.SIGNAL("statusBarMessage(const QString &)"), 
                  QtCore.QString(_(u"Saving file %s ...") % file.filename))
        file.save()
        self.emit(QtCore.SIGNAL("file_updated(int)"), file.id)

