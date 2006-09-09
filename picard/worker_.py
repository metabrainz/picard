from PyQt4 import QtCore
from Queue import Queue
from threading import Thread
import os.path
import sys
from picard import util

class WorkerThread(Thread, QtCore.QObject):
    
    def __init__(self):
        QtCore.QObject.__init__(self)
        Thread.__init__(self)
        self.exitThread = False
        self.queue = Queue()
        self.files = []
    
    def stop(self):
        """Stop the thread"""
        self.exitThread = True
        self.queue.put(None)
        self.join()
    
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

        # And add them to the file manager
        for file in files:
            self.tagger.addFile(file)

