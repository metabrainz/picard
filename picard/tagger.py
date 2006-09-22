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
from picard.util import strip_non_alnum
from picard.util.cachedws import CachedWebService

from musicbrainz2.utils import extractUuid
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

        if sys.platform == "win32":
            self._cache_dir = "~\\Local Settings\\Application Data\\MusicBrainz Picard\\cache"
        # FIXME: Mac OS?
        else:
            self._cache_dir = "~/.picard/cache"
        self._cache_dir = os.path.expanduser(self._cache_dir)

        self.load_components()

        self.worker = WorkerThread()
        self.connect(self.worker, QtCore.SIGNAL("add_files(const QStringList &)"), self.onAddFiles)
        self.connect(self.worker, QtCore.SIGNAL("file_updated(int)"), QtCore.SIGNAL("file_updated(int)"))
        self.connect(self.worker,
                     QtCore.SIGNAL("read_file_finished(PyObject*)"),
                     self.read_file_finished)
        self.connect(self.worker,
                     QtCore.SIGNAL("save_file_finished(PyObject*, bool)"),
                     self.save_file_finished)

        self._move_to_album = []
        self.connect(self.worker,
                     QtCore.SIGNAL("load_album_finished(PyObject*)"),
                     self.load_album_finished)

        self.browserIntegration = BrowserIntegration()
        
        self.files = {}
        self.files_mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        
        self.clusters = []
        self.unmatched_files = Cluster(_(u"Unmatched Files"))

        self.albums = []

        self.connect(self.browserIntegration, QtCore.SIGNAL("load_album(const QString &)"), self.load_album)
        
        self.window = MainWindow()
        self.connect(self.window, QtCore.SIGNAL("add_files"), self.onAddFiles)
        self.connect(self.window, QtCore.SIGNAL("addDirectory"), self.onAddDirectory)
        self.connect(self.worker, QtCore.SIGNAL("statusBarMessage(const QString &)"), self.window.setStatusBarMessage)
        self.connect(self.window, QtCore.SIGNAL("file_updated(int)"), QtCore.SIGNAL("file_updated(int)"))

        self.worker.start()
        self.browserIntegration.start()

    def match_files_to_album(self, files, album):
        matches = []
        for file in files:
            for track in album.tracks:
                sim = track.metadata.compare(file.orig_metadata)
                matches.append((sim, file, track))
        matches.sort(reverse=True)
        matched = []
        for sim, file, track in matches:
            if sim <= 0.5:
                continue
            if file in matched:
                continue
            if track.linked_file and track.linked_file.similarity > sim:
                continue
            file.move_to_track(track)
            matched.append(file)

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

    def _get_file_lookup(self):
        """Return a FileLookup object."""
        return FileLookup(self, self.config.setting["server_host"],
                          self.config.setting["server_port"],
                          self.browserIntegration.port)
        
    def search(self, text, type):
        """Search on the MusicBrainz website."""
        lookup = self._get_file_lookup()
        getattr(lookup, type + "Search")(text)

    def lookup(self, metadata):
        """Lookup the metadata on the MusicBrainz website."""
        lookup = self._get_file_lookup()
        lookup.tagLookup(metadata["artist"], metadata["album"], 
                         metadata["title"], metadata["tracknumber"],
                         str(metadata.get("~#length", 1)), 
                         metadata["~filename"], metadata["musicip_puid"])

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
            self.save_file(file)

    def save_file(self, file):
        """Save the file."""
        file.lock_for_write()
        try:
            file.state = File.TO_BE_SAVED
        finally:
            file.unlock()
        self.worker.save_file(file)

    def save_file_finished(self, file, saved):
        """Finalize file saving and notify views."""
        if saved:
            file.lock_for_write()
            try:
                file.orig_metadata.copy(file.metadata)
                file.metadata.changed = False
                file.state = File.SAVED
            finally:
                file.unlock()
        file.update()

    def update_file(self, file):
        """Update views for the specified file."""
        if file.track:
            self.emit(QtCore.SIGNAL("track_updated"), file.track)
        else:
            self.emit(QtCore.SIGNAL("file_updated"), file)

    def remove(self, objects):
        """Remove the specified objects."""
        files = []
        albums = []
        for obj in objects:
            if isinstance(obj, File):
                files.append(obj)
            elif isinstance(obj, Track):
                if obj.linked_file:
                    files.append(obj.linked_file)
            elif isinstance(obj, Album):
                albums.append(obj)
        if files:
            self.remove_files(files)
        for album in albums:
            self.remove_album(album)

    # Albums

    def load_album(self, album_id):
        album = Album(unicode(album_id), "[loading album information]", None)
        self.albums.append(album)
        self.connect(album, QtCore.SIGNAL("track_updated"), self, QtCore.SIGNAL("track_updated"))
        self.emit(QtCore.SIGNAL("albumAdded"), album)
        self.worker.load_album(album)
        return album

    def load_album_finished(self, album):
        self.emit(QtCore.SIGNAL("album_updated"), album)
        for file, target in self._move_to_album:
            if target == album:
                self.match_files_to_album([file], album)

    def get_album_by_id(self, album_id):
        for album in self.albums:
            if album.id == album_id:
                return album
        return None

    def remove_album(self, album):
        """Remove the specified album."""
        self.remove_files(self.get_files_from_objects([album]))
        index = self.albums.index(album)
        del self.albums[index]
        self.emit(QtCore.SIGNAL("albumRemoved"), album, index)

    # Auto-tagging

    def autoTag(self, files):
        # TODO: move to a separate thread
        import math
        
        # If the user selected no or only one file, use all unmatched files
        if len(files) < 1:
            self.files_mutex.lock()
            files = self.files.values()
            self.files_mutex.unlock()
            
        self.log.debug("Auto-tagging started... %r", files)
        
        # Do metadata lookups for all files
        q = Query(ws=self.get_web_service())
        for file in files:
            flt = TrackFilter(title=file.metadata["title"].encode("UTF-8"),
                artistName=strip_non_alnum(file.metadata["artist"]).encode("UTF-8"),
                releaseTitle=strip_non_alnum(file.metadata["album"]).encode("UTF-8"),
                duration=file.metadata.get("~#length", 0),
                limit=5)
            tracks = q.getTracks(filter=flt)
            file.matches = []
            for result in tracks:
                track = result.track
                metadata = Metadata()
                metadata["title"] = track.title
                metadata["artist"] = track.artist.name
                metadata["album"] = track.releases[0].title
                metadata["tracknumber"] = track.releases[0].tracksOffset
                metadata["musicbrainz_trackid"] = extractUuid(track.id)
                metadata["musicbrainz_artistid"] = extractUuid(track.artist.id)
                metadata["musicbrainz_albumid"] = \
                    extractUuid(track.releases[0].id)
                sim = file.orig_metadata.compare(metadata)
                file.matches.append([sim, metadata])

        # Get list of releases used in matches
        max_sim = 0
        usage = {}
        for file in files:
            releases = []
            for similarity, metadata in file.matches:
                release_id = metadata["musicbrainz_albumid"]
                if release_id not in releases:
                    try:
                        usage[release_id] += similarity
                    except KeyError:
                        usage[release_id] = similarity
                    max_sim = max(max_sim, usage[release_id])
                    releases.append(release_id)
        if max_sim:
            max_sim = 1.0 / max_sim

        releases = []
        for file in files:
#            print file
            for match in file.matches:
                match[0] *= usage[match[1]["musicbrainz_albumid"]] * max_sim
#                print "+  ", match[0], repr(match[1]["album"]), repr(match[1]["musicbrainz_albumid"])
            file.matches.sort(lambda a, b: cmp(a[0], b[0]),reverse=True)
            match = file.matches[0]
            release_id = match[1]["musicbrainz_albumid"]
            if match[0] > 0.1 and release_id not in releases:
                releases.append(release_id)

        # Sort releases by usage, load the most used one
        for release in releases:
            self.load_album(release)

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

    def add_files(self, files):
        """Add new files to the tagger."""
        # TODO: optimize this
        for file in files:
            self.add_file(file)

    def read_file_finished(self, file):
        album_id = file.metadata["musicbrainz_albumid"]
        if album_id:
            album = self.get_album_by_id(album_id)
            if not album:
                album = self.load_album(album_id)
            if album.loaded:
                self.match_files_to_album([file], album)
            else:
                self._move_to_album.append((file, album))
        if not file.track:
            file.move_to_cluster(self.unmatched_files)

    def remove_files(self, files):
        """Remove files from the tagger."""
        locker = QtCore.QMutexLocker(self.files_mutex)
        for file in files:
            file.remove_from_cluster()
            file.remove_from_track()
            del self.files[file.id]

    def evaluate_script(self, script, context={}):
        """Evaluate the script and return the result."""
        if not self.scripting:
            raise Exception, "No tagger script interpreter."

        return self.scripting[0].evaluate_script(script, context)

    def get_web_service(self):
        return CachedWebService(cache_dir=self._cache_dir)

def main(localedir=None):
    tagger = Tagger(localedir)
    sys.exit(tagger.run())

