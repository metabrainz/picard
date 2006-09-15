# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
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

from PyQt4 import QtGui, QtCore

import gettext
import locale
import logging
import os.path
import sys

import picard.resources

from picard.album import Album
from picard.api import IFileOpener, ITaggerScript
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster
from picard.component import ComponentManager, Interface, ExtensionPoint, Component
from picard.config import Config
from picard.file import File
from picard.metadata import Metadata
from picard.track import Track
from picard.ui.mainwindow import MainWindow
from picard.worker import WorkerThread

from musicbrainz2.webservice import Query, TrackFilter

# Install gettext "noop" function.
import __builtin__
__builtin__.__dict__['N_'] = lambda a: a 

class Tagger(QtGui.QApplication, ComponentManager, Component):
    
    file_openers = ExtensionPoint(IFileOpener)
    scripting = ExtensionPoint(ITaggerScript)
    
    def __init__(self, localeDir):
        QtGui.QApplication.__init__(self, sys.argv)
        ComponentManager.__init__(self)

        self.config = Config()
        
        logging.basicConfig(level=logging.DEBUG,
                    format='%(message)s',
#                    format='%(asctime)s %(levelname)-8s %(pathname)s#%(lineno)d [%(thread)04d]\n%(message)s',
                    datefmt='%H:%M:%S')        
        self.log = logging.getLogger('picard')
        
        QtCore.QObject.tagger = self
        QtCore.QObject.config = self.config
        QtCore.QObject.log = self.log

        self.setup_gettext(localeDir)
        self.load_components()

        self.worker = WorkerThread()
        self.connect(self.worker, QtCore.SIGNAL("add_files(const QStringList &)"), self.onAddFiles)
        self.connect(self.worker, QtCore.SIGNAL("file_updated(int)"), QtCore.SIGNAL("file_updated(int)"))
        
        self.browserIntegration = BrowserIntegration()
        
        self.files = {}
        self.files_mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        self.connect(self, QtCore.SIGNAL("file_added(int)"), self.on_file_added)
        
        self.clusters = []
        self.unmatched_files = Cluster(_(u"Unmatched Files"))

        self.albums = []

        self.connect(self.browserIntegration, QtCore.SIGNAL("load_album(const QString &)"), self.load_album)
        
        self.window = MainWindow()
        self.connect(self.window, QtCore.SIGNAL("add_files"), self.onAddFiles)
        self.connect(self.window, QtCore.SIGNAL("addDirectory"), self.onAddDirectory)
        self.connect(self.worker, QtCore.SIGNAL("statusBarMessage(const QString &)"), self.window.setStatusBarMessage)
        self.connect(self.window, QtCore.SIGNAL("search"), self.onSearch)
        self.connect(self.window, QtCore.SIGNAL("lookup"), self.onLookup)
        self.connect(self.window, QtCore.SIGNAL("file_updated(int)"), QtCore.SIGNAL("file_updated(int)"))
        
        self.worker.start()
        self.browserIntegration.start()
        
    def exit(self):
        self.browserIntegration.stop()
        self.worker.stop()
        
    def run(self):
        self.window.show()
        res = self.exec_()
        self.exit()
        return res
        
    def setup_gettext(self, localeDir):
        """Setup locales, load translations, install gettext functions."""
        if sys.platform == "win32":
            try:
                locale.setlocale(locale.LC_ALL, os.environ["LANG"])
            except KeyError:    
                os.environ["LANG"] = locale.getdefaultlocale()[0]
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        else:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass

        try:
            self.log.debug("Loading gettext translation, localeDir=%r", localeDir)
            self.translation = gettext.translation("picard", localeDir)
            self.translation.install(True)
        except IOError, e:
            __builtin__.__dict__['_'] = lambda a: a 
            self.log.warning(e)

    def load_components(self):
        # Load default components
        default_components = (
            'picard.plugins.picardmutagen',
            'picard.plugins.cuesheet',
            'picard.plugins.csv_opener',
            'picard.tagz',
            )
        for module in default_components:
            __import__(module)
            
    def get_supported_formats(self):
        """Returns list of supported formats.
        
        Format:
            [('.mp3', 'MPEG Layer-3 File'), ('.cue', 'Cuesheet'), ...]
        """
        formats = []
        for opener in self.file_openers:
            formats.extend(opener.get_supported_formats())
        return formats

    def onAddFiles(self, files):
        files = map(lambda f: os.path.normpath(unicode(f)), files)
        self.log.debug("onAddFiles(%r)", files)
        for filename in files:
            for opener in self.file_openers:
                if opener.can_open_file(filename):
                    self.worker.read_file(filename, opener.open_file)
        
    def onAddDirectory(self, directory):
        directory = os.path.normpath(directory)
        self.log.debug("onAddDirectory(%r)", directory)
        self.worker.read_directory(directory)

    def onSearch(self, text, type_):
        lookup = FileLookup(self, "musicbrainz.org", 80, self.browserIntegration.port)
        getattr(lookup, type_ + "Search")(text)

    def onLookup(self, metadata):
        lookup = FileLookup(self, "musicbrainz.org", 80, self.browserIntegration.port)
        lookup.tagLookup(
            metadata["artist"],
            metadata["album"],
            metadata["title"],
            metadata["tracknumber"],
            str(metadata.get("~#length", 0)),
            metadata["~filename"],
            metadata["musicip_puid"])

    def get_files_from_objects(self, objects):
        """Return list of files from list of albums, clusters, tracks or files."""
        files = []
        for obj in objects:
            if isinstance(obj, Album):
                for track in obj.tracks:
                    if track.linked_file and track.linked_file not in files:
                        files.append(track.linked_file)
            elif isinstance(obj, Track):
                if obj.linked_file and obj.linked_file not in files:
                    files.append(obj.linked_file)
            elif isinstance(obj, Cluster):
                for file in obj.files:
                    if file not in files:
                        files.append(file)
            elif isinstance(obj, File):
                if obj not in files:
                    files.append(obj)
        return files

    def save(self, objects):
        """Save the specified objects."""
        for file in self.get_files_from_objects(objects):
            self.worker.save_file(file)

    def remove(self, objects):
        """Remove the specified objects."""
        files = []
        albums = []
        for obj in objects:
            if isinstance(obj, File):
                files.append(obj)
            elif isinstance(obj, Track):
                if obj.isLinked():
                    files.append(obj.getLinkedFile())
            elif isinstance(obj, Album):
                albums.append(obj)
        if files:
            self.remove_files(files)
        for album in albums:
            self.remove_album(album)

    # Albums
    
    def load_album(self, albumId):
        album = Album(unicode(albumId), "[loading album information]", None)
        self.albums.append(album)
        self.connect(album, QtCore.SIGNAL("trackUpdated"), self, QtCore.SIGNAL("trackUpdated"))
        self.emit(QtCore.SIGNAL("albumAdded"), album)
        self.worker.load_album(album)

    def getAlbumById(self, albumId):
        for album in self.albums:
            if album.id == albumId:
                return album
        return None

    def remove_album(self, album):
        # Move all linked files to "Unmatched Files"
        for track in album.tracks:
            if track.isLinked():
                file = track.getLinkedFile()
                file.move_to_cluster(self.unmatched_files)
        # Remove the album
        index = self.albums.index(album)
        del self.albums[index]
        self.emit(QtCore.SIGNAL("albumRemoved"), album, index)

    # Auto-tagging

    def autoTag(self, files):
        # If the user selected no or only one file, use all unmatched files
        if len(files) < 1:
            self.files_mutex.lock()
            files = self.files.values()
            self.files_mutex.unlock()
            
        self.log.debug("Auto-tagging started... %r", files)
        
        # Do metadata lookups for all files
        q = Query()
        for file in files:
            flt = TrackFilter(title=file.metadata["title"].encode("UTF-8"),
                artistName=file.metadata["artist"].encode("UTF-8"),
                releaseTitle=file.metadata["album"].encode("UTF-8"),
                duration=file.metadata.get("~#length", 0),
                limit=5)
            tracks = q.getTracks(filter=flt)
            file.matches = []
            for result in tracks:
                track = result.track
                metadata = Metadata()
                metadata["title"] = track.title
                print repr(track.title)
                metadata["artist"] = track.artist.name
                metadata["album"] = track.releases[0].title
                metadata["tracknumber"] = track.releases[0].tracksOffset
                metadata["musicbrainz_trackid"] = track.id
                metadata["musicbrainz_artistid"] = track.artist.id
                metadata["musicbrainz_albumid"] = track.releases[0].id
                file.matches.append((file.get_similarity(metadata), metadata))

        # Get list of releases used in matches
        releases = {}
        for file in files:
            for similarity, metadata in file.matches:
                print metadata["album"], similarity
                try:
                    releases[metadata["musicbrainz_albumid"]] += similarity
                except KeyError:
                    releases[metadata["musicbrainz_albumid"]] = similarity

        # Sort releases by usage, load the most used one
        if releases:
            releases = releases.items()
            releases.sort(lambda a, b: int(100 * (b[1] - a[1])))
            self.load_album(releases[0][0])

    # File manager

    def get_file_by_id(self, file_id):
        """Get file by a file ID."""
        locker = QtCore.QMutexLocker(self.files_mutex)
        return self.files[file_id]

    def add_file(self, file):
        """Add new file to the tagger."""
        self.log.debug("Adding file %s", str(file));
        self.files_mutex.lock()
        self.files[file.id] = file
#        if not file.metadata["title"] and not file.metadata["artist"] and not file.metadata["album"]:
#            parseFileName(file.filename, file.metadata)
        self.files_mutex.unlock()
        self.emit(QtCore.SIGNAL("file_added(int)"), file.id)

    def add_files(self, files):
        """Add new files to the tagger."""
        # TODO: optimize this
        for file in files:
            self.add_file(file)

    def on_file_added(self, file_id):
        file = self.get_file_by_id(file_id)
        file.move_to_cluster(self.unmatched_files)

    def remove_files(self, files):
        """Remove files from the tagger."""
        locker = QtCore.QMutexLocker(self.files_mutex)
        for file in files:
            file.remove_from_cluster()
            file.remove_from_track()
            del self.files[file.id]

    def evaluate_script(self, script, context={}):
        if not self.scripting:
            raise Exception, "No tagger script interpreter."

        return self.scripting[0].evaluate_script(script, context)

def main(localedir=None):
    tagger = Tagger(localedir)
    sys.exit(tagger.run())

