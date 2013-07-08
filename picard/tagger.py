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

import getopt
import os.path
import shutil
import signal
import sys
from collections import deque
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

from picard import PICARD_VERSION_STR, log, acoustid, config
from picard.album import Album, NatAlbum
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster, ClusterList, UnmatchedFiles
from picard.const import USER_DIR, USER_PLUGIN_DIR
from picard.disc import Disc
from picard.file import File
from picard.formats import open as open_file
from picard.track import Track, NonAlbumTrack
from picard.releasegroup import ReleaseGroup
from picard.collection import load_user_collections
from picard.ui.mainwindow import MainWindow
from picard.ui.itemviews import BaseTreeView
from picard.plugin import PluginManager
from picard.acoustidmanager import AcoustIDManager
from picard.util import (
    decode_filename,
    encode_filename,
    queue,
    thread,
    mbid_validate,
    check_io_encoding,
    uniqify
    )
from picard.webservice import XmlWebService


class Tagger(QtGui.QApplication):

    tagger_stats_changed = QtCore.pyqtSignal()
    listen_port_changed = QtCore.pyqtSignal(int)
    cluster_added = QtCore.pyqtSignal(Cluster)
    cluster_removed = QtCore.pyqtSignal(Cluster)
    album_added = QtCore.pyqtSignal(Album)
    album_removed = QtCore.pyqtSignal(Album)

    __instance = None

    def __init__(self, args, localedir, autoupdate, debug=False):
        QtGui.QApplication.__init__(self, args)
        self.__class__.__instance = self

        self._args = args
        self._autoupdate = autoupdate

        # Initialize threading and allocate threads
        self.thread_pool = thread.ThreadPool(self)

        self.load_queue = queue.Queue()
        self.save_queue = queue.Queue()
        self.analyze_queue = queue.Queue()
        self.other_queue = queue.Queue()

        threads = self.thread_pool.threads
        for i in range(4):
            threads.append(thread.Thread(self.thread_pool, self.load_queue))
        threads.append(thread.Thread(self.thread_pool, self.save_queue))
        threads.append(thread.Thread(self.thread_pool, self.other_queue))
        threads.append(thread.Thread(self.thread_pool, self.other_queue))
        threads.append(thread.Thread(self.thread_pool, self.analyze_queue))

        self.thread_pool.start()
        self.stopping = False

        # Setup logging
        if debug or "PICARD_DEBUG" in os.environ:
            log.log_levels = log.log_levels|log.LOG_DEBUG
        log.debug("Starting Picard %s from %r", picard.__version__, os.path.abspath(__file__))

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

        # for compatibility with pre-1.3 plugins
        QtCore.QObject.tagger = self
        QtCore.QObject.config = config
        QtCore.QObject.log = log

        check_io_encoding()

        self._upgrade_config()

        setup_gettext(localedir, config.setting["ui_language"], log.debug)

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
            self.pluginmanager.load_plugindir(os.path.join(os.path.dirname(__file__), "plugins"))

        if not os.path.exists(USER_PLUGIN_DIR):
            os.makedirs(USER_PLUGIN_DIR)
        self.pluginmanager.load_plugindir(USER_PLUGIN_DIR)

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

    def _upgrade_config(self):
        cfg = config._config

        # In version 1.0, the file naming formats for single and various
        # artist releases were merged.
        def upgrade_to_v1_0():
            def remove_va_file_naming_format(merge=True):
                if merge:
                    config.setting["file_naming_format"] = (
                        "$if($eq(%compilation%,1),\n$noop(Various Artist "
                        "albums)\n%s,\n$noop(Single Artist Albums)\n%s)" % (
                            config.setting["va_file_naming_format"].toString(),
                            config.setting["file_naming_format"]
                        ))
                config.setting.remove("va_file_naming_format")
                config.setting.remove("use_va_format")

            if ("va_file_naming_format" in config.setting and
                "use_va_format" in config.setting):

                if config.setting["use_va_format"].toBool():
                    remove_va_file_naming_format()
                    self.window.show_va_removal_notice()

                elif (config.setting["va_file_naming_format"].toString() !=
                      r"$if2(%albumartist%,%artist%)/%album%/$if($gt(%totaldis"
                      "cs%,1),%discnumber%-,)$num(%tracknumber%,2) %artist% - "
                      "%title%"):

                    if self.window.confirm_va_removal():
                        remove_va_file_naming_format(merge=False)
                    else:
                        remove_va_file_naming_format()
                else:
                    # default format, disabled
                    remove_va_file_naming_format(merge=False)

        def upgrade_windows_compatibility_setting():
            # the setting `windows_compatible_filenames` has been renamed
            # to `windows_compatibility`
            _s = config.setting
            if "windows_compatible_filenames" in _s:
                _s["windows_compatibility"] = _s["windows_compatible_filenames"]
                _s.remove("windows_compatible_filenames")


        cfg.register_upgrade_hook("1.0.0final0", upgrade_to_v1_0)
        # TODO: uncomment this and replace with proper version before release
        #cfg.register_upgrade_hook("1.3.0dev1", upgrade_windows_compatibility_setting)

        cfg.run_upgrade_hooks()

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

    def move_file_to_track(self, file, albumid, trackid):
        """Move `file` to track `trackid` on album `albumid`."""
        album = self.load_album(albumid)
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
            self.nats.update()

    def exit(self):
        self.stopping = True
        self._acoustid.done()
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

    def _file_loaded(self, target, result=None, error=None):
        file = result
        if file is not None and error is None and not file.has_error():
            trackid = file.metadata['musicbrainz_trackid']
            if target is not None:
                self.move_files([file], target)
            elif not config.setting["ignore_file_mbids"]:
                albumid = file.metadata['musicbrainz_albumid']
                if mbid_validate(albumid):
                    if mbid_validate(trackid):
                        self.move_file_to_track(file, albumid, trackid)
                    else:
                        self.move_file_to_album(file, albumid)
                elif mbid_validate(trackid):
                    self.move_file_to_nat(file, trackid)
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
        log.debug("Adding files %r", filenames)
        new_files = []
        for filename in filenames:
            filename = os.path.normpath(os.path.realpath(filename))
            if filename not in self.files:
                file = open_file(filename)
                if file:
                    self.files[filename] = file
                    new_files.append(file)
        if new_files:
            if target is None or target is self.unmatched_files:
                self.unmatched_files.add_files(new_files)
                target = None
            for file in new_files:
                file.load(partial(self._file_loaded, target))

    def add_directory(self, path):
        walk = os.walk(unicode(path))

        def get_files():
            try:
                root, dirs, files = walk.next()
            except StopIteration:
                return None
            else:
                self.window.set_statusbar_message(N_("Loading directory %s"), root)
                return (os.path.join(root, f) for f in files)

        def process(result=None, error=None):
            if result:
                if error is None:
                    self.add_files(result)
                self.other_queue.put((get_files, process, QtCore.Qt.LowEventPriority))

        process(True, False)

    def get_file_lookup(self):
        """Return a FileLookup object."""
        return FileLookup(self, config.setting["server_host"],
                          config.setting["server_port"],
                          self.browser_integration.port)

    def search(self, text, type, adv=False):
        """Search on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        getattr(lookup, type + "Search")(text, adv)

    def browser_lookup(self, item):
        """Lookup the object's metadata on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        metadata = item.metadata
        albumid = metadata["musicbrainz_albumid"]
        trackid = metadata["musicbrainz_trackid"]
        # Only lookup via MB IDs if matched to a DataObject; otherwise ignore and use metadata details
        if isinstance(item, Track) and trackid:
            lookup.trackLookup(trackid)
        elif isinstance(item, Album) and albumid:
            lookup.albumLookup(albumid)
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

    def _file_saved(self, result=None, error=None):
        if error is None:
            file, old_filename, new_filename = result
            del self.files[old_filename]
            self.files[new_filename] = file

    def save(self, objects):
        """Save the specified objects."""
        files = self.get_files_from_objects(objects, save=True)
        for file in files:
            file.save(self._file_saved)

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
            #rely on python-discid auto detection
            device = None

        disc = Disc()
        self.set_wait_cursor()
        self.other_queue.put((
            partial(disc.read, encode_filename(device)),
            partial(self._lookup_disc, disc),
            QtCore.Qt.LowEventPriority))

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
            obj.load()

    @classmethod
    def instance(cls):
        return cls.__instance


def help():
    print """Usage: %s [OPTIONS] [FILE] [FILE] ...

Options:
    -d, --debug             enable debug-level logging
    -h, --help              display this help and exit
    -v, --version           display version information and exit
""" % (sys.argv[0],)


def version():
    print """MusicBrainz Picard %s""" % (PICARD_VERSION_STR)


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
