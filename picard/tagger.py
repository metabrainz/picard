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

from __future__ import print_function
import sip

sip.setapi("QString", 2)
sip.setapi("QVariant", 2)

from PyQt4 import QtGui, QtCore

import argparse
import os.path
import platform
import re
import shutil
import signal
import sys
from functools import partial
from itertools import chain


# A "fix" for http://python.org/sf/1438480
def _patched_shutil_copystat(src, dst):
    try:
        _orig_shutil_copystat(src, dst)
    except OSError:
        pass


_orig_shutil_copystat = shutil.copystat
shutil.copystat = _patched_shutil_copystat

import picard.resources
import picard.plugins
from picard.i18n import setup_gettext

from picard import (PICARD_APP_NAME, PICARD_ORG_NAME,
                    PICARD_FANCY_VERSION_STR, __version__,
                    log, acoustid, config)
from picard.album import Album, NatAlbum
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster, ClusterList, UnmatchedFiles
from picard.const import USER_DIR, USER_PLUGIN_DIR
from picard.dataobj import DataObject
from picard.disc import Disc
from picard.file import File
from picard.formats import open as open_file
from picard.track import Track, NonAlbumTrack
from picard.releasegroup import ReleaseGroup
from picard.collection import load_user_collections
from picard.ui.mainwindow import MainWindow
from picard.plugin import PluginManager
from picard.acoustidmanager import AcoustIDManager
from picard.config_upgrade import upgrade_config
from picard.util import (
    decode_filename,
    encode_filename,
    thread,
    mbid_validate,
    check_io_encoding,
    uniqify,
    is_hidden,
    versions,
)
from picard.webservice import XmlWebService
from picard.ui.searchdialog import (
    TrackSearchDialog,
    AlbumSearchDialog,
    ArtistSearchDialog
)


class Tagger(QtGui.QApplication):

    tagger_stats_changed = QtCore.pyqtSignal()
    listen_port_changed = QtCore.pyqtSignal(int)
    cluster_added = QtCore.pyqtSignal(Cluster)
    cluster_removed = QtCore.pyqtSignal(Cluster)
    album_added = QtCore.pyqtSignal(Album)
    album_removed = QtCore.pyqtSignal(Album)

    __instance = None

    def __init__(self, picard_args, unparsed_args, localedir, autoupdate):
        # Set the WM_CLASS to 'MusicBrainz-Picard' so desktop environments
        # can use it to look up the app
        QtGui.QApplication.__init__(self, ['MusicBrainz-Picard'] + unparsed_args)
        self.__class__.__instance = self

        self._cmdline_files = picard_args.FILE
        self._autoupdate = autoupdate
        self._debug = False

        # FIXME: Figure out what's wrong with QThreadPool.globalInstance().
        # It's a valid reference, but its start() method doesn't work.
        self.thread_pool = QtCore.QThreadPool(self)

        # Use a separate thread pool for file saving, with a thread count of 1,
        # to avoid race conditions in File._save_and_rename.
        self.save_thread_pool = QtCore.QThreadPool(self)
        self.save_thread_pool.setMaxThreadCount(1)

        if not sys.platform == "win32":
            # Set up signal handling
            # It's not possible to call all available functions from signal
            # handlers, therefore we need to set up a QSocketNotifier to listen
            # on a socket. Sending data through a socket can be done in a
            # signal handler, so we use the socket to notify the application of
            # the signal.
            # This code is adopted from
            # https://qt-project.org/doc/qt-4.8/unix-signals.html

            # To not make the socket module a requirement for the Windows
            # installer, import it here and not globally
            import socket
            self.signalfd = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM, 0)

            self.signalnotifier = QtCore.QSocketNotifier(self.signalfd[1].fileno(),
                                                         QtCore.QSocketNotifier.Read, self)
            self.signalnotifier.activated.connect(self.sighandler)

            signal.signal(signal.SIGHUP, self.signal)
            signal.signal(signal.SIGINT, self.signal)
            signal.signal(signal.SIGTERM, self.signal)

        # Setup logging
        self.debug(picard_args.debug or "PICARD_DEBUG" in os.environ)
        log.debug("Starting Picard from %r", os.path.abspath(__file__))
        log.debug("Platform: %s %s %s", platform.platform(),
                  platform.python_implementation(), platform.python_version())
        log.debug("Versions: %s", versions.as_string())
        if config.storage_type == config.REGISTRY_PATH:
            log.debug("Configuration registry path: %s", config.storage)
        else:
            log.debug("Configuration file path: %s", config.storage)

        # TODO remove this before the final release
        if sys.platform == "win32":
            olduserdir = "~\\Local Settings\\Application Data\\MusicBrainz Picard"
        else:
            olduserdir = "~/.picard"
        olduserdir = os.path.expanduser(olduserdir)
        if os.path.isdir(olduserdir):
            log.info("Moving %s to %s", olduserdir, USER_DIR)
            try:
                shutil.move(olduserdir, USER_DIR)
            except:
                pass
        log.debug("User directory: %s", os.path.abspath(USER_DIR))

        # for compatibility with pre-1.3 plugins
        QtCore.QObject.tagger = self
        QtCore.QObject.config = config
        QtCore.QObject.log = log

        check_io_encoding()

        # Must be before config upgrade because upgrade dialogs need to be
        # translated
        setup_gettext(localedir, config.setting["ui_language"], log.debug)

        upgrade_config()

        self.xmlws = XmlWebService()

        load_user_collections()

        # Initialize fingerprinting
        self._acoustid = acoustid.AcoustIDClient()
        self._acoustid.init()

        # Load plugins
        self.pluginmanager = PluginManager()
        if hasattr(sys, "frozen"):
            self.pluginmanager.load_plugindir(os.path.join(os.path.dirname(sys.argv[0]), "plugins"))
        else:
            mydir = os.path.dirname(os.path.abspath(__file__))
            self.pluginmanager.load_plugindir(os.path.join(mydir, "plugins"))
            self.pluginmanager.load_plugindir(os.path.join(mydir, os.pardir, "contrib", "plugins"))

        if not os.path.exists(USER_PLUGIN_DIR):
            os.makedirs(USER_PLUGIN_DIR)
        self.pluginmanager.load_plugindir(USER_PLUGIN_DIR)
        self.pluginmanager.query_available_plugins()

        self.acoustidmanager = AcoustIDManager()
        self.browser_integration = BrowserIntegration()

        self.files = {}
        self.clusters = ClusterList()
        self.albums = {}
        self.release_groups = {}
        self.mbid_redirects = {}
        self.unmatched_files = UnmatchedFiles()
        self.nats = None
        self.window = MainWindow()
        self.exit_cleanup = []

    def register_cleanup(self, func):
        self.exit_cleanup.append(func)

    def run_cleanup(self):
        for f in self.exit_cleanup:
            f()

    def debug(self, debug):
        if self._debug == debug:
            return
        if debug:
            log.log_levels = log.log_levels | log.LOG_DEBUG
            log.debug("Debug mode on")
        else:
            log.debug("Debug mode off")
            log.log_levels = log.log_levels & ~log.LOG_DEBUG
        self._debug = debug

    def move_files_to_album(self, files, albumid=None, album=None):
        """Move `files` to tracks on album `albumid`."""
        if album is None:
            album = self.load_album(albumid)
        if album.loaded:
            album.match_files(files)
        else:
            for file in list(files):
                file.move(album.unmatched_files)

    def move_file_to_album(self, file, albumid):
        """Move `file` to a track on album `albumid`."""
        self.move_files_to_album([file], albumid)

    def move_file_to_track(self, file, albumid, recordingid):
        """Move `file` to recording `recordingid` on album `albumid`."""
        album = self.load_album(albumid)
        file.move(album.unmatched_files)
        album.run_when_loaded(partial(album.match_file, file, recordingid))

    def create_nats(self):
        if self.nats is None:
            self.nats = NatAlbum()
            self.albums["NATS"] = self.nats
            self.album_added.emit(self.nats)
        return self.nats

    def move_file_to_nat(self, file, recordingid, node=None):
        self.create_nats()
        file.move(self.nats.unmatched_files)
        nat = self.load_nat(recordingid, node=node)
        nat.run_when_loaded(partial(file.move, nat))
        if nat.loaded:
            self.nats.update()

    def exit(self):
        log.debug("exit")
        self.stopping = True
        self._acoustid.done()
        self.thread_pool.waitForDone()
        self.browser_integration.stop()
        self.xmlws.stop()
        for f in self.exit_cleanup:
            f()

    def _run_init(self):
        if self._cmdline_files:
            files = []
            for file in self._cmdline_files:
                if os.path.isdir(file):
                    self.add_directory(decode_filename(file))
                else:
                    files.append(decode_filename(file))
            if files:
                self.add_files(files)
            del self._cmdline_files

    def run(self):
        if config.setting["browser_integration"]:
            self.browser_integration.start()
        self.window.show()
        QtCore.QTimer.singleShot(0, self._run_init)
        res = self.exec_()
        self.exit()
        return res

    def event(self, event):
        if isinstance(event, thread.ProxyToMainEvent):
            event.run()
        elif event.type() == QtCore.QEvent.FileOpen:
            f = str(event.file())
            self.add_files([f])
            # We should just return True here, except that seems to
            # cause the event's sender to get a -9874 error, so
            # apparently there's some magic inside QFileOpenEvent...
            return 1
        return QtGui.QApplication.event(self, event)

    def _file_loaded(self, file, target=None):
        if file is not None and not file.has_error():
            recordingid = file.metadata.getall('musicbrainz_recordingid')[0] \
                if 'musicbrainz_recordingid' in file.metadata else ''
            if target is not None:
                self.move_files([file], target)
            elif not config.setting["ignore_file_mbids"]:
                albumid = file.metadata.getall('musicbrainz_albumid')[0] \
                    if 'musicbrainz_albumid' in file.metadata else ''
                if mbid_validate(albumid):
                    if mbid_validate(recordingid):
                        self.move_file_to_track(file, albumid, recordingid)
                    else:
                        self.move_file_to_album(file, albumid)
                elif mbid_validate(recordingid):
                    self.move_file_to_nat(file, recordingid)
                elif config.setting['analyze_new_files'] and file.can_analyze():
                    self.analyze([file])
            elif config.setting['analyze_new_files'] and file.can_analyze():
                self.analyze([file])

    def move_files(self, files, target):
        if isinstance(target, (Track, Cluster)):
            for file in files:
                file.move(target)
        elif isinstance(target, File):
            for file in files:
                file.move(target.parent)
        elif isinstance(target, Album):
            self.move_files_to_album(files, album=target)
        elif isinstance(target, ClusterList):
            self.cluster(files)

    def add_files(self, filenames, target=None):
        """Add files to the tagger."""
        ignoreregex = None
        pattern = config.setting['ignore_regex']
        if pattern:
            ignoreregex = re.compile(pattern)
        ignore_hidden = config.setting["ignore_hidden_files"]
        new_files = []
        for filename in filenames:
            filename = os.path.normpath(os.path.realpath(filename))
            if ignore_hidden and is_hidden(filename):
                log.debug("File ignored (hidden): %s" % (filename))
                continue
            if ignoreregex is not None and ignoreregex.search(filename):
                log.info("File ignored (matching %s): %s" % (pattern, filename))
                continue
            if filename not in self.files:
                file = open_file(filename)
                if file:
                    self.files[filename] = file
                    new_files.append(file)
        if new_files:
            log.debug("Adding files %r", new_files)
            new_files.sort(key=lambda x: x.filename)
            if target is None or target is self.unmatched_files:
                self.unmatched_files.add_files(new_files)
                target = None
            for file in new_files:
                file.load(partial(self._file_loaded, target=target))

    def add_directory(self, path):
        ignore_hidden = config.setting["ignore_hidden_files"]
        walk = os.walk(unicode(path))

        def get_files():
            try:
                root, dirs, files = next(walk)
                if ignore_hidden:
                    dirs[:] = [d for d in dirs if not is_hidden(os.path.join(root, d))]
            except StopIteration:
                return None
            else:
                number_of_files = len(files)
                if number_of_files:
                    mparms = {
                        'count': number_of_files,
                        'directory': root,
                    }
                    log.debug("Adding %(count)d files from '%(directory)s'" %
                              mparms)
                    self.window.set_statusbar_message(
                        ungettext(
                            "Adding %(count)d file from '%(directory)s' ...",
                            "Adding %(count)d files from '%(directory)s' ...",
                            number_of_files),
                        mparms,
                        translate=None,
                        echo=None
                    )
                return (os.path.join(root, f) for f in files)

        def process(result=None, error=None):
            if result:
                if error is None:
                    self.add_files(result)
                thread.run_task(get_files, process)

        process(True, False)

    def get_file_lookup(self):
        """Return a FileLookup object."""
        return FileLookup(self, config.setting["server_host"],
                          config.setting["server_port"],
                          self.browser_integration.port)

    def search(self, text, type, adv=False):
        """Search on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        if config.setting["builtin_search"]:
            if type == "track" and not lookup.mbidLookup(text, 'recording'):
                dialog = TrackSearchDialog(self.window)
                dialog.search(text)
                dialog.exec_()
            elif type == "album" and not lookup.mbidLookup(text, 'release'):
                dialog = AlbumSearchDialog(self.window)
                dialog.search(text)
                dialog.exec_()
            elif type == "artist" and not lookup.mbidLookup(text, 'artist'):
                dialog = ArtistSearchDialog(self.window)
                dialog.search(text)
                dialog.exec_()
        else:
            getattr(lookup, type + "Search")(text, adv)

    def collection_lookup(self):
        """Lookup the users collections on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        lookup.collectionLookup(config.persist["oauth_username"])

    def browser_lookup(self, item):
        """Lookup the object's metadata on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        metadata = item.metadata
        # Only lookup via MB IDs if matched to a DataObject; otherwise ignore and use metadata details
        if isinstance(item, DataObject):
            itemid = item.id
            if isinstance(item, Track):
                lookup.recordingLookup(itemid)
            elif isinstance(item, Album):
                lookup.albumLookup(itemid)
        else:
            lookup.tagLookup(
                metadata["albumartist"] if item.is_album_like() else metadata["artist"],
                metadata["album"],
                metadata["title"],
                metadata["tracknumber"],
                '' if item.is_album_like() else str(metadata.length),
                item.filename if isinstance(item, File) else '')

    def get_files_from_objects(self, objects, save=False):
        """Return list of files from list of albums, clusters, tracks or files."""
        return uniqify(chain(*[obj.iterfiles(save) for obj in objects]))

    def save(self, objects):
        """Save the specified objects."""
        files = self.get_files_from_objects(objects, save=True)
        for file in files:
            file.save()

    def load_album(self, id, discid=None):
        id = self.mbid_redirects.get(id, id)
        album = self.albums.get(id)
        if album:
            log.debug("Album %s already loaded.", id)
            return album
        album = Album(id, discid=discid)
        self.albums[id] = album
        self.album_added.emit(album)
        album.load()
        return album

    def load_nat(self, id, node=None):
        self.create_nats()
        nat = self.get_nat_by_id(id)
        if nat:
            log.debug("NAT %s already loaded.", id)
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

    def get_release_group_by_id(self, id):
        return self.release_groups.setdefault(id, ReleaseGroup(id))

    def remove_files(self, files, from_parent=True):
        """Remove files from the tagger."""
        for file in files:
            if file.filename in self.files:
                file.clear_lookup_task()
                self._acoustid.stop_analyze(file)
                del self.files[file.filename]
                file.remove(from_parent)

    def remove_album(self, album):
        """Remove the specified album."""
        log.debug("Removing %r", album)
        album.stop_loading()
        self.remove_files(self.get_files_from_objects([album]))
        del self.albums[album.id]
        if album.release_group:
            album.release_group.remove_album(album.id)
        if album == self.nats:
            self.nats = None
        self.album_removed.emit(album)

    def remove_cluster(self, cluster):
        """Remove the specified cluster."""
        if not cluster.special:
            log.debug("Removing %r", cluster)
            files = list(cluster.files)
            cluster.files = []
            cluster.clear_lookup_task()
            self.remove_files(files, from_parent=False)
            self.clusters.remove(cluster)
            self.cluster_removed.emit(cluster)

    def remove(self, objects):
        """Remove the specified objects."""
        files = []
        for obj in objects:
            if isinstance(obj, File):
                files.append(obj)
            elif isinstance(obj, Track):
                files.extend(obj.linked_files)
            elif isinstance(obj, Album):
                self.window.set_statusbar_message(
                    N_("Removing album %(id)s: %(artist)s - %(album)s"),
                    {
                        'id': obj.id,
                        'artist': obj.metadata['albumartist'],
                        'album': obj.metadata['album']
                    }
                )
                self.remove_album(obj)
            elif isinstance(obj, Cluster):
                self.remove_cluster(obj)
        if files:
            self.remove_files(files)

    def _lookup_disc(self, disc, result=None, error=None):
        self.restore_cursor()
        if error is not None:
            QtGui.QMessageBox.critical(self.window, _(u"CD Lookup Error"),
                                       _(u"Error while reading CD:\n\n%s") % error)
        else:
            disc.lookup()

    def lookup_cd(self, action):
        """Reads CD from the selected drive and tries to lookup the DiscID on MusicBrainz."""
        if isinstance(action, QtGui.QAction):
            device = unicode(action.text())
        elif config.setting["cd_lookup_device"] != '':
            device = config.setting["cd_lookup_device"].split(",", 1)[0]
        else:
            # rely on python-discid auto detection
            device = None

        disc = Disc()
        self.set_wait_cursor()
        thread.run_task(
            partial(disc.read, encode_filename(device)),
            partial(self._lookup_disc, disc))

    @property
    def use_acoustid(self):
        return config.setting["fingerprinting_system"] == "acoustid"

    def analyze(self, objs):
        """Analyze the file(s)."""
        files = self.get_files_from_objects(objs)
        for file in files:
            file.set_pending()
            if self.use_acoustid:
                self._acoustid.analyze(file, partial(file._lookup_finished, 'acoustid'))

    # =======================================================================
    #  Metadata-based lookups
    # =======================================================================

    def autotag(self, objects):
        for obj in objects:
            if obj.can_autotag():
                obj.lookup_metadata()

    # =======================================================================
    #  Clusters
    # =======================================================================

    def cluster(self, objs):
        """Group files with similar metadata to 'clusters'."""
        log.debug("Clustering %r", objs)
        if len(objs) <= 1 or self.unmatched_files in objs:
            files = list(self.unmatched_files.files)
        else:
            files = self.get_files_from_objects(objs)
        fcmp = lambda a, b: (
            cmp(a.discnumber, b.discnumber) or
            cmp(a.tracknumber, b.tracknumber) or
            cmp(a.base_filename, b.base_filename))
        for name, artist, files in Cluster.cluster(files, 1.0):
            QtCore.QCoreApplication.processEvents()
            cluster = self.load_cluster(name, artist)
            for file in sorted(files, fcmp):
                file.move(cluster)

    def load_cluster(self, name, artist):
        for cluster in self.clusters:
            cm = cluster.metadata
            if name == cm["album"] and artist == cm["albumartist"]:
                return cluster
        cluster = Cluster(name, artist)
        self.clusters.append(cluster)
        self.cluster_added.emit(cluster)
        return cluster

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
            if obj.can_refresh():
                obj.load(priority=True, refresh=True)

    @classmethod
    def instance(cls):
        return cls.__instance

    def signal(self, signum, frame):
        log.debug("signal %i received", signum)
        # Send a notification about a received signal from the signal handler
        # to Qt.
        self.signalfd[0].sendall("a")

    def sighandler(self):
        self.signalnotifier.setEnabled(False)
        self.exit()
        self.quit()
        self.signalnotifier.setEnabled(True)


def version():
    print("%s %s %s" % (PICARD_ORG_NAME, PICARD_APP_NAME, PICARD_FANCY_VERSION_STR))


def longversion():
    print(versions.as_string())


def process_picard_args():
    parser = argparse.ArgumentParser(
        epilog="If one of the filenames begins with a hyphen, use -- to separate the options from the filenames."
    )
    parser.add_argument("-d", "--debug", action='store_true',
                        help="enable debug-level logging")
    parser.add_argument('-v', '--version', action='store_true',
                        help="display version information and exit")
    parser.add_argument("-V", "--long-version", action='store_true',
                        help="display long version information and exit")
    parser.add_argument('FILE', nargs='*')
    picard_args, unparsed_args = parser.parse_known_args()
    return picard_args, unparsed_args


def main(localedir=None, autoupdate=True):
    # Some libs (ie. Phonon) require those to be set
    QtGui.QApplication.setApplicationName(PICARD_APP_NAME)
    QtGui.QApplication.setOrganizationName(PICARD_ORG_NAME)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    picard_args, unparsed_args = process_picard_args()
    if picard_args.version:
        return version()
    if picard_args.long_version:
        return longversion()

    tagger = Tagger(picard_args, unparsed_args, localedir, autoupdate)
    tagger.startTimer(1000)
    sys.exit(tagger.run())
