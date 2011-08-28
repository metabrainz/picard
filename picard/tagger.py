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
import getopt
import os.path
import shutil
import signal
import sys
import traceback
import time
from collections import deque

# Install gettext "noop" function.
import __builtin__
__builtin__.__dict__['N_'] = lambda a: a

# Py2exe 0.6.6 has broken fake_getline which doesn't work with Python 2.5
if hasattr(sys, "frozen"):
    import linecache
    def fake_getline(filename, lineno, module_globals = None):
        return ''
    linecache.getline = fake_getline
    del linecache, fake_getline

# A "fix" for http://python.org/sf/1438480
def _patched_shutil_copystat(src, dst):
    try: _orig_shutil_copystat(src, dst)
    except OSError: pass
_orig_shutil_copystat = shutil.copystat
shutil.copystat = _patched_shutil_copystat

import picard.resources
import picard.plugins

from picard import musicdns, version_string, log
from picard.album import Album, NatAlbum
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster, AlbumCluster, UnmatchedCluster
from picard.config import Config
from picard.disc import Disc, DiscError
from picard.file import File
from picard.formats import open as open_file
from picard.metadata import Metadata
from picard.track import Track, NonAlbumTrack
from picard.collection import Collection
from picard.config import IntOption
from picard.script import ScriptParser
from picard.ui.mainwindow import MainWindow
from picard.plugin import PluginManager
from picard.puidmanager import PUIDManager
from picard.util import (
    decode_filename,
    encode_filename,
    make_short_filename,
    replace_win32_incompat,
    replace_non_ascii,
    sanitize_filename,
    icontheme,
    webbrowser2,
    pathcmp,
    partial,
    queue,
    thread,
    mbid_validate
    )
from picard.webservice import XmlWebService

class Tagger(QtGui.QApplication):

    file_state_changed = QtCore.pyqtSignal(int)
    file_updated = QtCore.pyqtSignal(File)
    files_added = QtCore.pyqtSignal(list)
    file_moved_to_track = QtCore.pyqtSignal(File, Track)
    files_moved_to_cluster = QtCore.pyqtSignal(list, Cluster)

    cluster_added = QtCore.pyqtSignal(AlbumCluster)
    cluster_removed = QtCore.pyqtSignal(Cluster)
    cluster_updated = QtCore.pyqtSignal(Cluster)
    cluster_hidden = QtCore.pyqtSignal(UnmatchedCluster, bool)

    album_added = QtCore.pyqtSignal(Album)
    album_updated = QtCore.pyqtSignal(Album, bool)
    album_removed = QtCore.pyqtSignal(Album)
    track_updated = QtCore.pyqtSignal(Track)

    collection_updated = QtCore.pyqtSignal(Collection, bool)
    releases_added_to_collection = QtCore.pyqtSignal(set, Collection, bool)
    releases_removed_from_collection = QtCore.pyqtSignal(set, Collection)
    releases_updated = QtCore.pyqtSignal(list, bool)

    __instance = None

    def __init__(self, args, localedir, autoupdate, debug=False):
        QtGui.QApplication.__init__(self, args)
        self.__class__.__instance = self

        self._args = args
        self._autoupdate = autoupdate
        self.config = Config()

        if sys.platform == "win32":
            userdir = os.environ.get("APPDATA", "~\\Application Data")
        else:
            userdir = os.environ.get("XDG_CONFIG_HOME", "~/.config")
        self.userdir = os.path.join(os.path.expanduser(userdir), "MusicBrainz", "Picard")

        # Initialize threading and allocate threads
        self.thread_pool = thread.ThreadPool(self)

        self.load_queue = queue.Queue()
        self.save_queue = queue.Queue()
        self.analyze_queue = queue.Queue()
        self.other_queue = queue.Queue()

        threads = self.thread_pool.threads
        threads.append(thread.Thread(self.thread_pool, self.load_queue))
        threads.append(thread.Thread(self.thread_pool, self.load_queue))
        threads.append(thread.Thread(self.thread_pool, self.save_queue))
        threads.append(thread.Thread(self.thread_pool, self.other_queue))
        threads.append(thread.Thread(self.thread_pool, self.other_queue))
        threads.append(thread.Thread(self.thread_pool, self.analyze_queue))

        self.thread_pool.start()
        self.stopping = False

        # Setup logging
        if debug or "PICARD_DEBUG" in os.environ:
            self.log = log.DebugLog()
        else:
            self.log = log.Log()
        self.log.debug("Starting Picard %s from %r", picard.__version__, os.path.abspath(__file__))

        # TODO remove this before the final release
        if sys.platform == "win32":
            olduserdir = "~\\Local Settings\\Application Data\\MusicBrainz Picard"
        else:
            olduserdir = "~/.picard"
        olduserdir = os.path.expanduser(olduserdir)
        if os.path.isdir(olduserdir):
            self.log.info("Moving %s to %s", olduserdir, self.userdir)
            try:
                shutil.move(olduserdir, self.userdir)
            except:
                pass

        QtCore.QObject.tagger = self
        QtCore.QObject.config = self.config
        QtCore.QObject.log = self.log

        self.setup_gettext(localedir)

        self.xmlws = XmlWebService()

        # Initialize fingerprinting
        self._ofa = musicdns.OFA()
        self._ofa.init()

        # Load plugins
        self.pluginmanager = PluginManager()
        self.user_plugin_dir = os.path.join(self.userdir, "plugins")
        if not os.path.exists(self.user_plugin_dir):
            os.makedirs(self.user_plugin_dir)
        self.pluginmanager.load_plugindir(self.user_plugin_dir)
        if hasattr(sys, "frozen"):
            self.pluginmanager.load_plugindir(os.path.join(os.path.dirname(sys.argv[0]), "plugins"))
        else:
            self.pluginmanager.load_plugindir(os.path.join(os.path.dirname(__file__), "plugins"))

        self.puidmanager = PUIDManager()

        self.browser_integration = BrowserIntegration()

        self.files = {}
        self.unmatched_files = UnmatchedCluster(always_visible=True)

        self.clusters = {}
        self.albums = {}
        self.mbid_redirects = {}

        self.window = MainWindow()

        self.nats = None

    def setup_gettext(self, localedir):
        """Setup locales, load translations, install gettext functions."""
        if self.config.setting["ui_language"]:
            os.environ['LANGUAGE'] = ''
            os.environ['LANG'] = self.config.setting["ui_language"]
        if sys.platform == "win32":
            try:
                locale.setlocale(locale.LC_ALL, os.environ["LANG"])
            except KeyError:
                os.environ["LANG"] = locale.getdefaultlocale()[0]
                try:
                    locale.setlocale(locale.LC_ALL, "")
                except:
                    pass
            except:
                pass
        else:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        try:
            self.log.debug("Loading gettext translation, localedir=%r", localedir)
            self.translation = gettext.translation("picard", localedir)
            self.translation.install(True)
            ungettext = self.translation.ungettext
        except IOError:
            __builtin__.__dict__['_'] = lambda a: a
            def ungettext(a, b, c):
                if c == 1: return a
                else: return b
        __builtin__.__dict__['ungettext'] = ungettext

    def move_files_to_album(self, files, albumid=None, album=None):
        """Move `files` to tracks on album `albumid`."""
        if album is None:
            album = self.load_album(albumid)
        if album.loaded:
            album.match_files(files)
        else:
            for file in files:
                file.move(album.unmatched_files)

    def move_file_to_album(self, file, albumid):
        """Move `file` to a track on album `albumid`."""
        self.move_files_to_album([file], albumid)

    def move_file_to_track(self, file, albumid, trackid):
        """Move `file` to track `trackid` on album `albumid`."""
        album = self.load_album(albumid)
        if album.loaded:
            album.match_file(file, trackid)
        else:
            file.move(album.unmatched_files)
            album.run_when_loaded(partial(album.match_file, file, trackid))

    def create_nats(self):
        if self.nats is None:
            self.nats = NatAlbum()
            self.albums["NATS"] = self.nats
            self.album_added.emit(self.nats)
        return self.nats

    def move_file_to_nat(self, file, trackid, node=None):
        self.create_nats()
        file.move(self.nats.unmatched_files)
        nat = self.load_nat(trackid, node=node)
        nat.run_when_loaded(partial(file.move, nat))
        if nat.loaded:
            self.nats.update(False)

    def exit(self):
        self.stopping = True
        self._ofa.done()
        self.thread_pool.stop()
        self.browser_integration.stop()
        self.xmlws.stop()

    def _run_init(self):
        if self._args:
            files = []
            for file in self._args:
                if os.path.isdir(file):
                    self.add_directory(decode_filename(file))
                else:
                    files.append(decode_filename(file))
            if files:
                self.add_files(files)
            del self._args

    def run(self):
        self.browser_integration.start()
        self.window.show()
        QtCore.QTimer.singleShot(0, self._run_init)
        res = self.exec_()
        self.exit()
        return res

    def event(self, event):
        if event.type() == QtCore.QEvent.FileOpen:
            f = str(event.file())
            self.add_files([f])
            # We should just return True here, except that seems to
            # cause the event's sender to get a -9874 error, so
            # apparently there's some magic inside QFileOpenEvent...
            return 1
        return QtGui.QApplication.event(self, event)

    def _file_loaded(self, result=None, error=None):
        return
        file = result
        if file is not None and error is None and not file.has_error():
            puid = file.metadata['musicip_puid']
            trackid = file.metadata['musicbrainz_trackid']
            albumid = file.metadata['musicbrainz_albumid']
            self.puidmanager.add(puid, trackid)
            if mbid_validate(albumid):
                if mbid_validate(trackid):
                    self.move_file_to_track(file, albumid, trackid)
                else:
                    self.move_file_to_album(file, albumid)
            elif mbid_validate(trackid):
                self.move_file_to_nat(file, trackid)
            elif self.config.setting['analyze_new_files']:
                self.analyze([file])

    def add_files(self, filenames):
        """Add files to the tagger."""
        self.log.debug("Adding files %r", filenames)
        new_files = []
        normpath = os.path.normpath
        realpath = os.path.realpath
        for filename in filenames:
            filename = normpath(realpath(filename))
            if filename not in self.files:
                file = open_file(filename)
                if file:
                    self.files[filename] = file
                    new_files.append(file)
        if new_files:
            for file in new_files:
                file.load(self._file_loaded)
                file.parent = self.unmatched_files
            self.unmatched_files.files.extend(new_files)
            self.files_added.emit(new_files)

    def process_directory_listing(self, root, queue, result=None, error=None):
        try:
            # Read directory listing
            if result is not None and error is None:
                files = []
                directories = deque()
                try:
                    for path in result:
                        path = os.path.join(root, path)
                        if os.path.isdir(path):
                            directories.appendleft(path)
                        else:
                            try:
                                files.append(decode_filename(path))
                            except UnicodeDecodeError:
                                self.log.warning("Failed to decode filename: %r", path)
                                continue
                finally:
                    if files:
                        self.add_files(files)
                    queue.extendleft(directories)
        finally:
            # Scan next directory in the queue
            try:
                path = queue.popleft()
            except IndexError: pass
            else:
                self.other_queue.put((
                    partial(os.listdir, path),
                    partial(self.process_directory_listing, path, queue),
                    QtCore.Qt.LowEventPriority))

    def add_directory(self, path):
        path = encode_filename(path)
        self.other_queue.put((partial(os.listdir, path),
                              partial(self.process_directory_listing, path, deque()),
                              QtCore.Qt.LowEventPriority))

    def add_urls(self, urls):
        files = []
        for url in urls:
            if url.scheme() == "file" or not url.scheme():
                filename = unicode(url.toLocalFile())
                if os.path.isdir(encode_filename(filename)):
                    self.add_directory(filename)
                else:
                    files.append(filename)
            elif url.scheme() == "http":
                path = unicode(url.path())
                match = re.search(r"/(release|recording)/([0-9a-z\-]{36})", path)
                if not match:
                    continue
                entity = match.group(1)
                mbid = match.group(2)
                if entity == "release":
                    self.load_album(mbid)
                elif entity == "recording":
                    self.load_nat(mbid)
        if files:
            self.add_files(files)

    def get_file_by_id(self, id):
        """Get file by a file ID."""
        for file in self.files.itervalues():
            if file.id == id:
                return file
        return None

    def get_file_by_filename(self, filename):
        """Get file by a filename."""
        return self.files.get(filename, None)

    def get_file_lookup(self):
        """Return a FileLookup object."""
        return FileLookup(self, self.config.setting["server_host"],
                          self.config.setting["server_port"],
                          self.browser_integration.port)

    def search(self, text, type, adv=False):
        """Search on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        getattr(lookup, type + "Search")(text, adv)

    def lookup(self, metadata):
        """Lookup the metadata on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        albumid = metadata["musicbrainz_albumid"]
        trackid = metadata["musicbrainz_trackid"]
        if trackid:
            lookup.trackLookup(trackid)
        elif albumid:
            lookup.albumLookup(albumid)
        else:
            lookup.tagLookup(metadata["artist"], metadata["album"],
                             metadata["title"], metadata["tracknumber"],
                             str(metadata.length),
                             metadata["~filename"], metadata["musicip_puid"])

    def get_files_from_objects(self, objects, save=False):
        """Return list of files from list of albums, clusters, tracks or files."""
        files = []
        for obj in objects:
            for file in obj.iterfiles(save):
                if file not in files:
                    files.append(file)
        return files

    def _file_saved(self, result=None, error=None):
        if error is None:
            file, old_filename, new_filename = result
            del self.files[old_filename]
            self.files[new_filename] = file

    def save(self, objects):
        """Save the specified objects."""
        files = self.get_files_from_objects(objects, save=True)
        for file in files:
            file.save(self._file_saved, self.tagger.config.setting)

    def load_album(self, id, discid=None):
        id = self.mbid_redirects.get(id, id)
        album = self.albums.get(id)
        if album:
            return album
        album = Album(id, discid=discid)
        self.albums[id] = album
        self.album_added.emit(album)
        album.load()
        return album

    def reload_album(self, album):
        if album == self.nats:
            album.update()
        else:
            album.load()

    def load_nat(self, id, node=None):
        self.create_nats()
        nat = self.get_nat_by_id(id)
        if nat:
            return nat
        nat = NonAlbumTrack(id)
        self.nats.tracks.append(nat)
        self.nats.update(True)
        if node:
            nat._parse_recording(node)
        else:
            nat.load()
        return nat

    def get_nat_by_id(self, id):
        if self.nats is not None:
            for nat in self.nats.tracks:
                if nat.id == id:
                    return nat

    def _lookup_disc(self, disc, result=None, error=None):
        self.restore_cursor()
        if error is not None:
            QtGui.QMessageBox.critical(self.window, _(u"CD Lookup Error"),
                _(u"Error while reading CD:\n\n%s") % error)
        else:
            disc.lookup()

    def lookup_cd(self, action=None):
        """Reads CD from the selected drive and tries to lookup the DiscID on MusicBrainz."""
        if action is None:
            device = self.config.setting["cd_lookup_device"].split(",", 1)[0]
        else:
            device = unicode(action.text())

        disc = Disc()
        self.set_wait_cursor()
        self.other_queue.put((
            partial(disc.read, encode_filename(device)),
            partial(self._lookup_disc, disc),
            QtCore.Qt.LowEventPriority))

    def _lookup_puid(self, file, result=None, error=None):
        puid = result
        if file.state == File.PENDING:
            if puid:
                self.puidmanager.add(puid, None)
                file.metadata['musicip_puid'] = puid
                file.lookup_puid(puid)
            else:
                self.window.set_statusbar_message(N_("Could not find PUID for file %s"), file.filename)
                file.clear_pending()

    def analyze(self, objs):
        """Analyze the file(s)."""
        files = self.get_files_from_objects(objs)
        for file in files:
            file.set_pending()
            self._ofa.analyze(file, partial(self._lookup_puid, file))

    # =======================================================================
    #  Metadata-based lookups
    # =======================================================================

    def autotag(self, objects):
        if objects == [self.unmatched_files]:
            objects = self.unmatched_files.files
        for obj in iter(objects):
            if isinstance(obj, (File, AlbumCluster)) and not obj.lookup_task:
                obj.lookup_metadata()

    # =======================================================================
    #  Clusters
    # =======================================================================

    def cluster(self, files):
        """Group files with similar metadata to 'clusters'."""
        self.window.enable_cluster(False)

        if len(files) <= 1:
            files = self.unmatched_files.files
        self.log.debug("Clustering %r", files)

        fcmp = lambda a, b: (
            cmp(a.discnumber, b.discnumber) or
            cmp(a.tracknumber, b.tracknumber) or
            cmp(a.base_filename, b.base_filename))

        for name, artist, files in AlbumCluster.cluster(files, 1.0):
            cluster = self.clusters.get((name, artist))
            if cluster is None:
                cluster = AlbumCluster(name, artist)
                self.clusters[(name, artist)] = cluster
                self.cluster_added.emit(cluster)

            files.sort(fcmp)
            self.unmatched_files.remove_files(files)
            for file in files:
                file.parent = cluster
            cluster.add_files(files)

            QtCore.QCoreApplication.processEvents()

        self.window.enable_cluster(True)

    # =======================================================================
    #  Utils
    # =======================================================================

    def set_wait_cursor(self):
        """Sets the waiting cursor."""
        QtGui.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor))

    def restore_cursor(self):
        """Restores the cursor set by ``set_wait_cursor``."""
        QtGui.QApplication.restoreOverrideCursor()

    def refresh(self, objs):
        for obj in objs:
            if isinstance(obj, Album):
                self.reload_album(obj)
            elif isinstance(obj, NonAlbumTrack):
                obj.load()

    @classmethod
    def instance(cls):
        return cls.__instance

    def num_files(self):
        return len(self.files)

    def num_pending_files(self):
        return len([file for file in self.files.values() if file.state == File.PENDING])


def help():
    print """Usage: %s [OPTIONS] [FILE] [FILE] ...

Options:
    -d, --debug             enable debug-level logging
    -h, --help              display this help and exit
    -v, --version           display version information and exit
""" % (sys.argv[0],)


def version():
    print """MusicBrainz Picard %s""" % (version_string)


def main(localedir=None, autoupdate=True):
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    opts, args = getopt.getopt(sys.argv[1:], "hvd", ["help", "version", "debug"])
    kwargs = {}
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            return help()
        elif opt in ("-v", "--version"):
            return version()
        elif opt in ("-d", "--debug"):
            kwargs["debug"] = True
    tagger = Tagger(args, localedir, autoupdate, **kwargs)
    sys.exit(tagger.run())
