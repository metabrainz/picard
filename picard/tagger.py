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

from PyQt5 import QtGui, QtCore, QtWidgets

import argparse
import logging
import os.path
import platform
import re
import shutil
import signal
import sys
from functools import partial
from itertools import chain
from operator import attrgetter


# A "fix" for https://bugs.python.org/issue1438480
def _patched_shutil_copystat(src, dst, *, follow_symlinks=True):
    try:
        _orig_shutil_copystat(src, dst, follow_symlinks=follow_symlinks)
    except OSError:
        pass


_orig_shutil_copystat = shutil.copystat
shutil.copystat = _patched_shutil_copystat

import picard.resources
from picard.i18n import setup_gettext

from picard import (PICARD_APP_NAME, PICARD_ORG_NAME, PICARD_FANCY_VERSION_STR,
                    log, acoustid, config)
from picard.album import Album, NatAlbum
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster, ClusterList, UnclusteredFiles
from picard.const import USER_DIR, USER_PLUGIN_DIR
from picard.dataobj import DataObject
from picard.disc import Disc
from picard.file import File
from picard.formats import open_ as open_file
from picard.track import Track, NonAlbumTrack
from picard.releasegroup import ReleaseGroup
from picard.collection import load_user_collections
from picard.ui.mainwindow import MainWindow
from picard.ui.itemviews import BaseTreeView
from picard.plugin import PluginManager
from picard.acoustid.manager import AcoustIDManager
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
from picard.webservice import WebService
from picard.webservice.api_helpers import MBAPIHelper, AcoustIdAPIHelper
from picard.ui.searchdialog.artist import ArtistSearchDialog
from picard.ui.searchdialog.track import TrackSearchDialog
from picard.ui.searchdialog.album import AlbumSearchDialog



class Tagger(QtWidgets.QApplication):

    tagger_stats_changed = QtCore.pyqtSignal()
    listen_port_changed = QtCore.pyqtSignal(int)
    cluster_added = QtCore.pyqtSignal(Cluster)
    cluster_removed = QtCore.pyqtSignal(Cluster)
    album_added = QtCore.pyqtSignal(Album)
    album_removed = QtCore.pyqtSignal(Album)

    __instance = None

    _debug = False
    _no_restore = False

    def __init__(self, picard_args, unparsed_args, localedir, autoupdate):

        # Use the new fusion style from PyQt5 for a modern and consistent look
        # across all OSes.
        self.setStyle('Fusion')

        # Set the WM_CLASS to 'MusicBrainz-Picard' so desktop environments
        # can use it to look up the app
        super().__init__(['MusicBrainz-Picard'] + unparsed_args)
        self.__class__.__instance = self
        config._setup(self, picard_args.config_file)

        # Allow High DPI Support
        self.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
        self.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        super().setStyleSheet(
            'QGroupBox::title { /* PICARD-1206, Qt bug workaround */ }'
        )

        self._cmdline_files = picard_args.FILE
        self._autoupdate = autoupdate
        self._no_restore = picard_args.no_restore

        self.debug(
            picard_args.debug
            or "PICARD_DEBUG" in os.environ
            or config.setting['log_verbosity'] == logging.DEBUG
        )

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
        log.debug("Starting Picard from %r", os.path.abspath(__file__))
        log.debug("Platform: %s %s %s", platform.platform(),
                  platform.python_implementation(), platform.python_version())
        log.debug("Versions: %s", versions.as_string())
        log.debug("Configuration file path: %r", config.config.fileName())

        log.debug("User directory: %r", os.path.abspath(USER_DIR))

        # for compatibility with pre-1.3 plugins
        QtCore.QObject.tagger = self
        QtCore.QObject.config = config
        QtCore.QObject.log = log

        check_io_encoding()

        # Must be before config upgrade because upgrade dialogs need to be
        # translated
        setup_gettext(localedir, config.setting["ui_language"], log.debug)

        upgrade_config()

        self.webservice = WebService()
        self.mb_api = MBAPIHelper(self.webservice)
        self.acoustid_api = AcoustIdAPIHelper(self.webservice)

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
        self.unclustered_files = UnclusteredFiles()
        self.nats = None
        self.window = MainWindow()
        self.exit_cleanup = []
        self.stopping = False

    def register_cleanup(self, func):
        self.exit_cleanup.append(func)

    def run_cleanup(self):
        for f in self.exit_cleanup:
            f()

    def debug(self, debug):
        self._debug = debug
        if debug:
            log.debug_mode(True)
            log.debug("Debug mode on")
        else:
            log.info("Debug mode off")
            log.debug_mode(False)

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
        if self.stopping:
            return
        self.stopping = True
        log.debug("Picard stopping")
        self._acoustid.done()
        self.thread_pool.waitForDone()
        self.save_thread_pool.waitForDone()
        self.browser_integration.stop()
        self.webservice.stop()
        self.run_cleanup()
        QtCore.QCoreApplication.processEvents()

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
            f = string_(event.file())
            self.add_files([f])
            # We should just return True here, except that seems to
            # cause the event's sender to get a -9874 error, so
            # apparently there's some magic inside QFileOpenEvent...
            return 1
        return super().event(event)

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
        if target is None:
            log.debug("Aborting move since target is invalid")
            return
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
                log.debug("File ignored (hidden): %r" % (filename))
                continue
            # Ignore .smbdelete* files which Applie iOS SMB creates by renaming a file when it cannot delete it
            if os.path.basename(filename).startswith(".smbdelete"):
                log.debug("File ignored (.smbdelete): %r", filename)
                continue
            if ignoreregex is not None and ignoreregex.search(filename):
                log.info("File ignored (matching %r): %r" % (pattern, filename))
                continue
            if filename not in self.files:
                file = open_file(filename)
                if file:
                    self.files[filename] = file
                    new_files.append(file)
        if new_files:
            log.debug("Adding files %r", new_files)
            new_files.sort(key=lambda x: x.filename)
            if target is None or target is self.unclustered_files:
                self.unclustered_files.add_files(new_files)
                target = None
            for file in new_files:
                file.load(partial(self._file_loaded, target=target))

    def add_directory(self, path):
        if config.setting['recursively_add_files']:
            self._add_directory_recursive(path)
        else:
            self._add_directory_non_recursive(path)

    def _add_directory_recursive(self, path):
        ignore_hidden = config.setting["ignore_hidden_files"]
        walk = os.walk(path)

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
                    log.debug("Adding %(count)d files from '%(directory)r'" %
                              mparms)
                    self.window.set_statusbar_message(
                        ngettext(
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

    def _add_directory_non_recursive(self, path):
        files = []
        for f in os.listdir(path):
            listing = os.path.join(path, f)
            if os.path.isfile(listing):
                files.append(listing)
        number_of_files = len(files)
        if number_of_files:
            mparms = {
                'count': number_of_files,
                'directory': path,
            }
            log.debug("Adding %(count)d files from '%(directory)r'" %
                      mparms)
            self.window.set_statusbar_message(
                ngettext(
                    "Adding %(count)d file from '%(directory)s' ...",
                    "Adding %(count)d files from '%(directory)s' ...",
                    number_of_files),
                mparms,
                translate=None,
                echo=None
            )
            # Function call only if files exist
            self.add_files(files)

    def get_file_lookup(self):
        """Return a FileLookup object."""
        return FileLookup(self, config.setting["server_host"],
                          config.setting["server_port"],
                          self.browser_integration.port)

    def copy_files(self, objects):
        mimeData = QtCore.QMimeData()
        mimeData.setUrls([QtCore.QUrl.fromLocalFile(f.filename) for f in (self.get_files_from_objects(objects))])
        self.clipboard().setMimeData(mimeData)

    def paste_files(self, target):
        mimeData = self.clipboard().mimeData()
        if mimeData.hasUrls():
            BaseTreeView.drop_urls(mimeData.urls(), target)

    def search(self, text, search_type, adv=False, mbid_matched_callback=None):
        """Search on the MusicBrainz website."""
        search_types = {
            'track': {
                'entity': 'recording',
                'dialog': TrackSearchDialog
            },
            'album': {
                'entity': 'release',
                'dialog': AlbumSearchDialog
            },
            'artist': {
                'entity': 'artist',
                'dialog': ArtistSearchDialog
            },
        }
        if search_type not in search_types:
            return
        search = search_types[search_type]
        lookup = self.get_file_lookup()
        if config.setting["builtin_search"]:
            if not lookup.mbid_lookup(text, search['entity'],
                                      mbid_matched_callback=mbid_matched_callback):
                dialog = search['dialog'](self.window)
                dialog.search(text)
                dialog.exec_()
        else:
            lookup.search_entity(search['entity'], text, adv, mbid_matched_callback=mbid_matched_callback)

    def collection_lookup(self):
        """Lookup the users collections on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        lookup.collection_lookup(config.persist["oauth_username"])

    def browser_lookup(self, item):
        """Lookup the object's metadata on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        metadata = item.metadata
        # Only lookup via MB IDs if matched to a DataObject; otherwise ignore and use metadata details
        if isinstance(item, DataObject):
            itemid = item.id
            if isinstance(item, Track):
                lookup.recording_lookup(itemid)
            elif isinstance(item, Album):
                lookup.album_lookup(itemid)
        else:
            lookup.tag_lookup(
                metadata["albumartist"] if item.is_album_like() else metadata["artist"],
                metadata["album"],
                metadata["title"],
                metadata["tracknumber"],
                '' if item.is_album_like() else string_(metadata.length),
                item.filename if isinstance(item, File) else '')

    def get_files_from_objects(self, objects, save=False):
        """Return list of files from list of albums, clusters, tracks or files."""
        return uniqify(chain(*[obj.iterfiles(save) for obj in objects]))

    def save(self, objects):
        """Save the specified objects."""
        files = self.get_files_from_objects(objects, save=True)
        for file in files:
            file.save()

    def load_album(self, album_id, discid=None):
        album_id = self.mbid_redirects.get(album_id, album_id)
        album = self.albums.get(album_id)
        if album:
            log.debug("Album %s already loaded.", album_id)
            return album
        album = Album(album_id, discid=discid)
        self.albums[album_id] = album
        self.album_added.emit(album)
        album.load()
        return album

    def load_nat(self, nat_id, node=None):
        self.create_nats()
        nat = self.get_nat_by_id(nat_id)
        if nat:
            log.debug("NAT %s already loaded.", nat_id)
            return nat
        nat = NonAlbumTrack(nat_id)
        self.nats.tracks.append(nat)
        self.nats.update(True)
        if node:
            nat._parse_recording(node)
        else:
            nat.load()
        return nat

    def get_nat_by_id(self, nat_id):
        if self.nats is not None:
            for nat in self.nats.tracks:
                if nat.id == nat_id:
                    return nat

    def get_release_group_by_id(self, rg_id):
        return self.release_groups.setdefault(rg_id, ReleaseGroup(rg_id))

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
            elif isinstance(obj, UnclusteredFiles):
                files.extend(list(obj.files))
            elif isinstance(obj, Cluster):
                self.remove_cluster(obj)
        if files:
            self.remove_files(files)

    def _lookup_disc(self, disc, result=None, error=None):
        self.restore_cursor()
        if error is not None:
            QtWidgets.QMessageBox.critical(self.window, _("CD Lookup Error"),
                                       _("Error while reading CD:\n\n%s") % error)
        else:
            disc.lookup()

    def lookup_cd(self, action):
        """Reads CD from the selected drive and tries to lookup the DiscID on MusicBrainz."""
        if isinstance(action, QtWidgets.QAction):
            device = action.text()
        elif config.setting["cd_lookup_device"] != '':
            device = config.setting["cd_lookup_device"].split(",", 1)[0]
        else:
            # rely on python-discid auto detection
            device = None

        disc = Disc()
        self.set_wait_cursor()
        thread.run_task(
            partial(disc.read, encode_filename(device)),
            partial(self._lookup_disc, disc),
            traceback=self._debug)

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
        if len(objs) <= 1 or self.unclustered_files in objs:
            files = list(self.unclustered_files.files)
        else:
            files = self.get_files_from_objects(objs)
        for name, artist, files in Cluster.cluster(files, 1.0):
            QtCore.QCoreApplication.processEvents()
            cluster = self.load_cluster(name, artist)
            for file in sorted(files, key=attrgetter('discnumber', 'tracknumber', 'base_filename')):
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
        super().setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor))

    def restore_cursor(self):
        """Restores the cursor set by ``set_wait_cursor``."""
        super().restoreOverrideCursor()

    def refresh(self, objs):
        for obj in objs:
            if obj.can_refresh():
                obj.load(priority=True, refresh=True)

    def bring_tagger_front(self):
        self.window.setWindowState(self.window.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        self.window.raise_()
        self.window.activateWindow()

    @classmethod
    def instance(cls):
        return cls.__instance

    def signal(self, signum, frame):
        log.debug("signal %i received", signum)
        # Send a notification about a received signal from the signal handler
        # to Qt.
        self.signalfd[0].sendall(b"a")

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
    parser.add_argument("-c", "--config-file", action='store',
                        default=None,
                        help="location of the configuration file")
    parser.add_argument("-d", "--debug", action='store_true',
                        help="enable debug-level logging")
    parser.add_argument("-N", "--no-restore", action='store_true',
                        help="do not restore positions and/or sizes")
    parser.add_argument('-v', '--version', action='store_true',
                        help="display version information and exit")
    parser.add_argument("-V", "--long-version", action='store_true',
                        help="display long version information and exit")
    parser.add_argument('FILE', nargs='*')
    picard_args, unparsed_args = parser.parse_known_args()
    return picard_args, unparsed_args


def main(localedir=None, autoupdate=True):
    # Some libs (ie. Phonon) require those to be set
    QtWidgets.QApplication.setApplicationName(PICARD_APP_NAME)
    QtWidgets.QApplication.setOrganizationName(PICARD_ORG_NAME)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    picard_args, unparsed_args = process_picard_args()
    if picard_args.version:
        return version()
    if picard_args.long_version:
        return longversion()

    tagger = Tagger(picard_args, unparsed_args, localedir, autoupdate)
    tagger.startTimer(1000)
    sys.exit(tagger.run())
