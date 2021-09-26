# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2014, 2017 Lukáš Lalinský
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 amckinle
# Copyright (C) 2008-2010, 2014-2015, 2018-2021 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2010 Andrew Barnert
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2011-2014, 2017-2019 Wieland Hoffmann
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013 Ionuț Ciocîrlan
# Copyright (C) 2013 brainz34
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2013-2015, 2017-2020 Laurent Monin
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017-2018 Vishal Choudhary
# Copyright (C) 2018 Bob Swift
# Copyright (C) 2018 virusMac
# Copyright (C) 2019 Joel Lintunen
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2020 Julius Michaelis
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


import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import logging
import os.path
import platform
import re
import shutil
import signal
import sys

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import (
    PICARD_APP_ID,
    PICARD_APP_NAME,
    PICARD_DESKTOP_NAME,
    PICARD_FANCY_VERSION_STR,
    PICARD_ORG_NAME,
    acoustid,
    log,
)
from picard.acousticbrainz import (
    ab_available,
    ab_extractor_callback,
    ab_feature_extraction,
    ab_setup_extractor,
)
from picard.acoustid.manager import AcoustIDManager
from picard.album import (
    Album,
    NatAlbum,
    run_album_post_removal_processors,
)
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import (
    Cluster,
    ClusterList,
    UnclusteredFiles,
)
from picard.collection import load_user_collections
from picard.config import (
    get_config,
    setup_config,
)
from picard.config_upgrade import upgrade_config
from picard.const import (
    USER_DIR,
    USER_PLUGIN_DIR,
)
from picard.const.sys import (
    IS_FROZEN,
    IS_HAIKU,
    IS_MACOS,
    IS_WIN,
)
from picard.dataobj import DataObject
from picard.disc import Disc
from picard.file import File
from picard.formats import open_ as open_file
from picard.i18n import setup_gettext
from picard.pluginmanager import PluginManager
from picard.releasegroup import ReleaseGroup
from picard.track import (
    NonAlbumTrack,
    Track,
)
from picard.util import (
    check_io_encoding,
    decode_filename,
    encode_filename,
    is_hidden,
    iter_files_from_objects,
    mbid_validate,
    normpath,
    process_events_iter,
    thread,
    versions,
    webbrowser2,
)
from picard.util.checkupdate import UpdateCheckManager
from picard.webservice import WebService
from picard.webservice.api_helpers import (
    AcoustIdAPIHelper,
    MBAPIHelper,
)

import picard.resources  # noqa: F401 # pylint: disable=unused-import

from picard.ui import theme
from picard.ui.itemviews import BaseTreeView
from picard.ui.mainwindow import MainWindow
from picard.ui.searchdialog.album import AlbumSearchDialog
from picard.ui.searchdialog.artist import ArtistSearchDialog
from picard.ui.searchdialog.track import TrackSearchDialog


# A "fix" for https://bugs.python.org/issue1438480
def _patched_shutil_copystat(src, dst, *, follow_symlinks=True):
    try:
        _orig_shutil_copystat(src, dst, follow_symlinks=follow_symlinks)
    except OSError:
        pass


_orig_shutil_copystat = shutil.copystat
shutil.copystat = _patched_shutil_copystat


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

        super().__init__(sys.argv)
        self.__class__.__instance = self
        setup_config(self, picard_args.config_file)
        config = get_config()
        theme.setup(self)

        self._cmdline_files = picard_args.FILE
        self.autoupdate_enabled = autoupdate
        self._no_restore = picard_args.no_restore
        self._no_plugins = picard_args.no_plugins

        self.set_log_level(config.setting['log_verbosity'])

        if picard_args.debug or "PICARD_DEBUG" in os.environ:
            self.set_log_level(logging.DEBUG)

        # Default thread pool
        self.thread_pool = ThreadPoolExecutor()

        # Provide a separate thread pool for operations that should not be
        # delayed by longer background processing tasks, e.g. because the user
        # expects instant feedback instead of waiting for a long list of
        # operations to finish.
        self.priority_thread_pool = ThreadPoolExecutor(max_workers=1)

        # Use a separate thread pool for file saving, with a thread count of 1,
        # to avoid race conditions in File._save_and_rename.
        self.save_thread_pool = ThreadPoolExecutor(max_workers=1)

        if not IS_WIN:
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

        if IS_MACOS:
            # On macOS it is not common that the global menu shows icons
            self.setAttribute(QtCore.Qt.AA_DontShowIconsInMenus)

        # Setup logging
        log.debug("Starting Picard from %r", os.path.abspath(__file__))
        log.debug("Platform: %s %s %s", platform.platform(),
                  platform.python_implementation(), platform.python_version())
        log.debug("Versions: %s", versions.as_string())
        log.debug("Configuration file path: %r", config.fileName())

        log.debug("User directory: %r", os.path.abspath(USER_DIR))

        # for compatibility with pre-1.3 plugins
        QtCore.QObject.tagger = self
        QtCore.QObject.config = config
        QtCore.QObject.log = log

        check_io_encoding()

        # Must be before config upgrade because upgrade dialogs need to be
        # translated
        setup_gettext(localedir, config.setting["ui_language"], log.debug)

        upgrade_config(config)

        self.webservice = WebService()
        self.mb_api = MBAPIHelper(self.webservice)

        load_user_collections()

        # Initialize fingerprinting
        acoustid_api = AcoustIdAPIHelper(self.webservice)
        self._acoustid = acoustid.AcoustIDClient(acoustid_api)
        self._acoustid.init()
        self.acoustidmanager = AcoustIDManager(acoustid_api)

        # Setup AcousticBrainz extraction
        if config.setting["use_acousticbrainz"]:
            ab_setup_extractor()

        # Load plugins
        self.pluginmanager = PluginManager()
        if not self._no_plugins:
            if IS_FROZEN:
                self.pluginmanager.load_plugins_from_directory(os.path.join(os.path.dirname(sys.argv[0]), "plugins"))
            else:
                mydir = os.path.dirname(os.path.abspath(__file__))
                self.pluginmanager.load_plugins_from_directory(os.path.join(mydir, "plugins"))

            if not os.path.exists(USER_PLUGIN_DIR):
                os.makedirs(USER_PLUGIN_DIR)
            self.pluginmanager.load_plugins_from_directory(USER_PLUGIN_DIR)

        self.browser_integration = BrowserIntegration()
        self.browser_integration.listen_port_changed.connect(self.listen_port_changed)

        self._pending_files_count = 0
        self.files = {}
        self.clusters = ClusterList()
        self.albums = {}
        self.release_groups = {}
        self.mbid_redirects = {}
        self.unclustered_files = UnclusteredFiles()
        self.nats = None
        self.window = MainWindow(disable_player=picard_args.no_player)
        self.exit_cleanup = []
        self.stopping = False

        # Load release version information
        if self.autoupdate_enabled:
            self.updatecheckmanager = UpdateCheckManager(parent=self.window)

    def register_cleanup(self, func):
        self.exit_cleanup.append(func)

    def run_cleanup(self):
        for f in self.exit_cleanup:
            f()

    def set_log_level(self, level):
        self._debug = level == logging.DEBUG
        log.set_level(level)

    def mb_login(self, callback, parent=None):
        scopes = "profile tag rating collection submit_isrc submit_barcode"
        authorization_url = self.webservice.oauth_manager.get_authorization_url(scopes)
        webbrowser2.open(authorization_url)
        if not parent:
            parent = self.window
        dialog = QtWidgets.QInputDialog(parent)
        dialog.setWindowModality(QtCore.Qt.WindowModal)
        dialog.setWindowTitle(_("MusicBrainz Account"))
        dialog.setLabelText(_("Authorization code:"))
        status = dialog.exec_()
        if status == QtWidgets.QDialog.Accepted:
            authorization_code = dialog.textValue()
            self.webservice.oauth_manager.exchange_authorization_code(
                authorization_code, scopes,
                partial(self.on_mb_authorization_finished, callback))
        else:
            callback(False)

    def on_mb_authorization_finished(self, callback, successful=False):
        if successful:
            self.webservice.oauth_manager.fetch_username(
                partial(self.on_mb_login_finished, callback))
        else:
            callback(False)

    @classmethod
    def on_mb_login_finished(self, callback, successful):
        if successful:
            load_user_collections()
        callback(successful)

    def mb_logout(self):
        self.webservice.oauth_manager.revoke_tokens()
        load_user_collections()

    def move_files_to_album(self, files, albumid=None, album=None):
        """Move `files` to tracks on album `albumid`."""
        if album is None:
            album = self.load_album(albumid)
        album.match_files(files)

    def move_file_to_album(self, file, albumid):
        """Move `file` to a track on album `albumid`."""
        self.move_files_to_album([file], albumid)

    def move_file_to_track(self, file, albumid, recordingid):
        """Move `file` to recording `recordingid` on album `albumid`."""
        album = self.load_album(albumid)
        file.match_recordingid = recordingid
        album.match_files([file])

    def create_nats(self):
        if self.nats is None:
            self.nats = NatAlbum()
            self.albums["NATS"] = self.nats
            self.album_added.emit(self.nats)
            self.nats.item.setExpanded(True)
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
        self.thread_pool.shutdown()
        self.save_thread_pool.shutdown()
        self.priority_thread_pool.shutdown()
        self.browser_integration.stop()
        self.webservice.stop()
        self.run_cleanup()
        QtCore.QCoreApplication.processEvents()

    def _run_init(self):
        if self._cmdline_files:
            files = [decode_filename(f) for f in self._cmdline_files]
            self.add_paths(files)
            del self._cmdline_files

    def run(self):
        self.update_browser_integration()
        self.window.show()
        QtCore.QTimer.singleShot(0, self._run_init)
        res = self.exec_()
        self.exit()
        return res

    def update_browser_integration(self):
        config = get_config()
        if config.setting["browser_integration"]:
            self.browser_integration.start()
        else:
            self.browser_integration.stop()

    def event(self, event):
        if isinstance(event, thread.ProxyToMainEvent):
            event.run()
        elif event.type() == QtCore.QEvent.FileOpen:
            file = event.file()
            self.add_paths([file])
            if IS_HAIKU:
                self.bring_tagger_front()
            # We should just return True here, except that seems to
            # cause the event's sender to get a -9874 error, so
            # apparently there's some magic inside QFileOpenEvent...
            return 1
        return super().event(event)

    def _file_loaded(self, file, target=None, remove_file=False, new_files=None):
        config = get_config()
        self._pending_files_count -= 1
        if self._pending_files_count == 0:
            self.window.set_sorting(True)

        if remove_file:
            file.remove()
            return

        if file is None:
            return

        if file.has_error():
            self.unclustered_files.add_file(file)
            return

        file_moved = False
        if not config.setting["ignore_file_mbids"]:
            recordingid = file.metadata.getall('musicbrainz_recordingid')
            recordingid = recordingid[0] if recordingid else ''
            is_valid_recordingid = mbid_validate(recordingid)

            albumid = file.metadata.getall('musicbrainz_albumid')
            albumid = albumid[0] if albumid else ''
            is_valid_albumid = mbid_validate(albumid)

            if is_valid_albumid and is_valid_recordingid:
                log.debug("%r has release (%s) and recording (%s) MBIDs, moving to track...",
                          file, albumid, recordingid)
                self.move_file_to_track(file, albumid, recordingid)
                file_moved = True
            elif is_valid_albumid:
                log.debug("%r has only release MBID (%s), moving to album...",
                          file, albumid)
                self.move_file_to_album(file, albumid)
                file_moved = True
            elif is_valid_recordingid:
                log.debug("%r has only recording MBID (%s), moving to non-album track...",
                          file, recordingid)
                self.move_file_to_nat(file, recordingid)
                file_moved = True

        if not file_moved:
            self.move_file(file, target)
            if target != self.unclustered_files:
                file_moved = True

        if file_moved:
            new_files.remove(file)

        # fallback on analyze if nothing else worked
        if not file_moved and config.setting['analyze_new_files'] and file.can_analyze():
            log.debug("Trying to analyze %r ...", file)
            self.analyze([file])

        # Auto cluster newly added files if they are not explicitly moved elsewhere
        if self._pending_files_count == 0 and new_files and config.setting["cluster_new_files"]:
            self.cluster(new_files)

    def move_file(self, file, target):
        if target is None:
            if not file.parent:
                target = self.unclustered_files
            else:
                log.debug("Aborting move since target is invalid and file already has a parent")
        if isinstance(target, Album):
            self.move_files_to_album([file], album=target)
        elif isinstance(target, File) and target.parent:
            file.move(target.parent)
        # To be able to move a file to it target must implement add_file(file)
        elif hasattr(target, 'add_file'):
            file.move(target)
        # Ensure a file always has a parent so it shows up in UI
        elif not file.parent:
            file.move(self.unclustered_files)

    def move_files(self, files, target, move_to_multi_tracks=True):
        if target is None:
            log.debug("Aborting move since target is invalid")
            return
        self.window.set_sorting(False)
        if isinstance(target, Cluster):
            for file in process_events_iter(files):
                file.move(target)
        elif isinstance(target, Track):
            album = target.album
            for file in process_events_iter(files):
                file.move(target)
                if move_to_multi_tracks:  # Assign next file to following track
                    target = album.get_next_track(target) or album.unmatched_files
        elif isinstance(target, File):
            for file in process_events_iter(files):
                file.move(target.parent)
        elif isinstance(target, Album):
            self.move_files_to_album(files, album=target)
        elif isinstance(target, ClusterList):
            for file in process_events_iter(files):
                if isinstance(file.parent, Track):
                    file.parent.remove_file(file)
            self.cluster(files)
        self.window.set_sorting(True)

    def add_files(self, filenames, target=None):
        """Add files to the tagger."""
        ignoreregex = None
        config = get_config()
        pattern = config.setting['ignore_regex']
        if pattern:
            try:
                ignoreregex = re.compile(pattern)
            except re.error as e:
                log.error("Failed evaluating regular expression for ignore_regex: %s", e)
        ignore_hidden = config.setting["ignore_hidden_files"]
        new_files = []
        for filename in filenames:
            filename = normpath(filename)
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
                QtCore.QCoreApplication.processEvents()
        if new_files:
            log.debug("Adding files %r", new_files)
            new_files.sort(key=lambda x: x.filename)
            self.window.set_sorting(False)
            self._pending_files_count += len(new_files)
            for i, file in enumerate(new_files):
                file.load(partial(self._file_loaded, target=target, new_files=new_files))
                # Calling processEvents helps processing the _file_loaded
                # callbacks in between, which keeps the UI more responsive.
                # Avoid calling it to often to not slow down the loading to much
                # Using an uneven number to have the unclustered file counter
                # not look stuck in certain digits.
                if i % 17 == 0:
                    QtCore.QCoreApplication.processEvents()

    @staticmethod
    def _scan_paths_recursive(paths, recursive, ignore_hidden):
        local_paths = list(paths)
        while local_paths:
            current_path = local_paths.pop(0)
            try:
                if os.path.isdir(current_path):
                    for entry in os.scandir(current_path):
                        if ignore_hidden and is_hidden(entry.path):
                            continue
                        if recursive and entry.is_dir():
                            local_paths.append(entry.path)
                        else:
                            yield entry.path
                else:
                    yield current_path
            except OSError as err:
                log.warning(err)

    def add_paths(self, paths, target=None):
        config = get_config()
        files = self._scan_paths_recursive(paths,
                            config.setting['recursively_add_files'],
                            config.setting["ignore_hidden_files"])
        self.add_files(files, target=target)

    def get_file_lookup(self):
        """Return a FileLookup object."""
        config = get_config()
        return FileLookup(self, config.setting["server_host"],
                          config.setting["server_port"],
                          self.browser_integration.port)

    def copy_files(self, objects):
        mimeData = QtCore.QMimeData()
        mimeData.setUrls([QtCore.QUrl.fromLocalFile(f.filename) for f in iter_files_from_objects(objects)])
        self.clipboard().setMimeData(mimeData)

    def paste_files(self, target):
        mimeData = self.clipboard().mimeData()
        if mimeData.hasUrls():
            BaseTreeView.drop_urls(mimeData.urls(), target)

    def search(self, text, search_type, adv=False, mbid_matched_callback=None, force_browser=False):
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
        config = get_config()
        if config.setting["builtin_search"] and not force_browser:
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
        config = get_config()
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
                '' if item.is_album_like() else str(metadata.length),
                item.filename if isinstance(item, File) else '')

    def get_files_from_objects(self, objects, save=False):
        """Return list of unique files from list of albums, clusters, tracks or files.

        Note: Consider using picard.util.iter_files_from_objects instead, which returns an iterator.
        """
        return list(iter_files_from_objects(objects, save=save))

    def save(self, objects):
        """Save the specified objects."""
        for file in iter_files_from_objects(objects, save=True):
            file.save()

    def load_mbid(self, type, mbid):
        self.bring_tagger_front()
        if type == 'album':
            self.load_album(mbid)
        elif type == 'nat':
            self.load_nat(mbid)
        else:
            log.warning('Unknown type to load: %s', type)

    def load_album(self, album_id, discid=None):
        album_id = self.mbid_redirects.get(album_id, album_id)
        album = self.albums.get(album_id)
        if album:
            log.debug("Album %s already loaded.", album_id)
            album.add_discid(discid)
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
        self.tagger_stats_changed.emit()

    def remove_album(self, album):
        """Remove the specified album."""
        log.debug("Removing %r", album)
        if album.id not in self.albums:
            return
        album.stop_loading()
        self.remove_files(list(album.iterfiles()))
        del self.albums[album.id]
        if album.release_group:
            album.release_group.remove_album(album.id)
        if album == self.nats:
            self.nats = None
        self.album_removed.emit(album)
        run_album_post_removal_processors(album)
        self.tagger_stats_changed.emit()

    def remove_nat(self, track):
        """Remove the specified non-album track."""
        log.debug("Removing %r", track)
        self.remove_files(list(track.iterfiles()))
        if not self.nats:
            return
        self.nats.tracks.remove(track)
        if not self.nats.tracks:
            self.remove_album(self.nats)
        else:
            self.nats.update(True)

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
        with self.window.ignore_selection_changes:
            for obj in objects:
                if isinstance(obj, File):
                    files.append(obj)
                elif isinstance(obj, NonAlbumTrack):
                    self.remove_nat(obj)
                elif isinstance(obj, Track):
                    files.extend(obj.files)
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
        config = get_config()
        if isinstance(action, QtWidgets.QAction):
            device = action.data()
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
        config = get_config()
        return config.setting["fingerprinting_system"] == "acoustid"

    def analyze(self, objs):
        """Analyze the file(s)."""
        if not self.use_acoustid:
            return
        for file in iter_files_from_objects(objs):
            if file.can_analyze():
                file.set_pending()
                self._acoustid.analyze(file, partial(file._lookup_finished, File.LOOKUP_ACOUSTID))

    def generate_fingerprints(self, objs):
        """Generate the fingerprints without matching the files."""
        if not self.use_acoustid:
            return

        def finished(file, result):
            file.clear_pending()

        for file in iter_files_from_objects(objs):
            file.set_pending()
            self._acoustid.fingerprint(file, partial(finished, file))

    def extract_and_submit_acousticbrainz_features(self, objs):
        """Extract AcousticBrainz features and submit them."""
        if not ab_available():
            return

        for file in iter_files_from_objects(objs):
            # Skip unmatched files
            if not file.can_extract():
                log.warning("AcousticBrainz requires a MusicBrainz Recording ID, but file does not have it: %s" % file.filename)
            # And process matched ones
            else:
                file.set_pending()

                # Check if file was either already processed or sent to the AcousticBrainz server
                if file.acousticbrainz_features_file:
                    results = (file.acousticbrainz_features_file, 0, "Writing results")
                    ab_extractor_callback(self, file, results, False)
                elif file.acousticbrainz_is_duplicate:
                    results = (None, 0, "Duplicate")
                    ab_extractor_callback(self, file, results, False)
                else:
                    file.acousticbrainz_error = False
                    # Launch the acousticbrainz on a separate process
                    log.debug("Extracting AcousticBrainz features from %s" % file.filename)
                    ab_feature_extraction(
                        self,
                        file.metadata["musicbrainz_recordingid"],
                        file.filename,
                        partial(ab_extractor_callback, self, file)
                    )

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

        with self.window.ignore_selection_changes:
            self.window.set_sorting(False)
            cluster_files = defaultdict(list)
            for name, artist, files in Cluster.cluster(files, 1.0, self):
                cluster = self.load_cluster(name, artist)
                cluster_files[cluster].extend(files)
            for cluster, files in process_events_iter(cluster_files.items()):
                cluster.add_files(files)
            self.window.set_sorting(True)

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
    # Qt default arguments. Parse them so Picard does not interpret the
    # arguments as file names to load.
    parser.add_argument("-style", nargs=1, help=argparse.SUPPRESS)
    parser.add_argument("-stylesheet", nargs=1, help=argparse.SUPPRESS)
    # Same for default X arguments
    parser.add_argument("-display", nargs=1, help=argparse.SUPPRESS)

    # Picard specific arguments
    parser.add_argument("-c", "--config-file", action='store',
                        default=None,
                        help="location of the configuration file")
    parser.add_argument("-d", "--debug", action='store_true',
                        help="enable debug-level logging")
    parser.add_argument("-M", "--no-player", action='store_true',
                        help="disable built-in media player")
    parser.add_argument("-N", "--no-restore", action='store_true',
                        help="do not restore positions and/or sizes")
    parser.add_argument("-P", "--no-plugins", action='store_true',
                        help="do not load any plugins")
    parser.add_argument("--no-crash-dialog", action='store_true',
                        help="disable the crash dialog")
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
    QtWidgets.QApplication.setDesktopFileName(PICARD_DESKTOP_NAME)

    # Allow High DPI Support
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    # HighDpiScaleFactorRoundingPolicy is available since Qt 5.14. This is
    # required to support fractional scaling on Windows properly.
    # It causes issues without scaling on Linux, see https://tickets.metabrainz.org/browse/PICARD-1948
    if IS_WIN and hasattr(QtGui.QGuiApplication, 'setHighDpiScaleFactorRoundingPolicy'):
        QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # Enable mnemonics on all platforms, even macOS
    QtGui.qt_set_sequence_auto_mnemonic(True)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    picard_args, unparsed_args = process_picard_args()
    if picard_args.version:
        return version()
    if picard_args.long_version:
        return longversion()

    try:
        from PyQt5.QtDBus import QDBusConnection
        dbus = QDBusConnection.sessionBus()
        dbus.registerService(PICARD_APP_ID)
    except ImportError:
        pass

    tagger = Tagger(picard_args, unparsed_args, localedir, autoupdate)

    # Initialize Qt default translations
    translator = QtCore.QTranslator()
    locale = QtCore.QLocale()
    translation_path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)
    log.debug("Looking for Qt locale %s in %s", locale.name(), translation_path)
    if translator.load(locale, "qtbase_", directory=translation_path):
        tagger.installTranslator(translator)
    else:
        log.debug('Qt locale %s not available', locale.name())

    tagger.startTimer(1000)
    sys.exit(tagger.run())
