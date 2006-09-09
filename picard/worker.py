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

from PyQt4 import QtCore
from Queue import Queue
import os.path
import sys
from picard import util

class WorkerThread(QtCore.QThread):
    
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.setPriority(QtCore.QThread.LowestPriority)
        self.exitThread = False
        self.queue = Queue()
        self.files = []
    
    def start(self):
        self.log.debug("Starting the worker thread")
        QtCore.QThread.start(self)
        
    def stop(self):
        self.log.debug("Stopping the worker thread")
        if self.isRunning():
            self.exitThread = True
            self.queue.put(None)
            self.wait()
    
    def run(self):
        while not self.exitThread:
            item = self.queue.get(True)
            if not item:
                continue
                
            item[0](item)
            
            if self.queue.empty():
                # TR: Status bar message
                message = QtCore.QString(_(u"Done"))
                self.emit(QtCore.SIGNAL("statusBarMessage(const QString &)"), message)

    def loadAlbum(self, album):
        """Load the album information from MusicBrainz."""
        self.queue.put((self.doLoadAlbum, album))
        
    def doLoadAlbum(self, args):
        album = args[1]
        
        message = QtCore.QString(_(u"Loading album %s ...") % album.id)
        self.emit(QtCore.SIGNAL("statusBarMessage(const QString &)"), message)
        
        album.load()
        self.emit(QtCore.SIGNAL("albumLoaded(const QString &)"), album.id)
        
    def readDirectory(self, directory):
        """Read the directory recursively and add all files to the tagger."""
        self.queue.put((self.doReadDirectory, directory))
        
    def doReadDirectory(self, args):        
        root = args[1]
        # Show status bar message
        message = QtCore.QString(_(u"Reading directory %s ...") % root)
        self.emit(QtCore.SIGNAL("statusBarMessage(const QString &)"), message)
        # Read the directory listing
        files = QtCore.QStringList()
        for name in os.listdir(util.encode_filename(root)):
            name = os.path.join(root, name)
            if os.path.isdir(name):
                self.readDirectory(name)
            else:
                files.append(QtCore.QString(util.decode_filename(name)))
        if files:
            self.emit(QtCore.SIGNAL("addFiles(const QStringList &)"), files)

    def readFile(self, filename, opener):
        self.queue.put((self.doReadFile, (filename, opener)))
            
    def doReadFile(self, args):
        filename, opener = args[1]
        # Show status bar message
        message = QtCore.QString(_(u"Reading file %s ...") % filename)
        self.emit(QtCore.SIGNAL("statusBarMessage(const QString &)"), message)
        # Load files
        files = opener(filename)
        # Add loaded files to the tagger
        self.tagger.add_files(files)

    def saveFile(self, file):
        self.queue.put((self.doSaveFile, file))
        
    def doSaveFile(self, args):
        file = args[1]
        filename = file.filename

        self.log.debug("Saving file %r", file)
        
        # Show status bar message
        message = QtCore.QString(_(u"Saving file %s ...") % filename)
        self.emit(QtCore.SIGNAL("statusBarMessage(const QString &)"), message)
        
        
