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
import getopt
import os.path
import shutil
import sys
import traceback
import time

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

from picard import musicdns, version_string
from picard.album import Album
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster, ClusterList, UnmatchedFiles
from picard.config import Config
from picard.disc import Disc, DiscError
from picard.file import File
from picard.formats import open as open_file
from picard.metadata import Metadata
from picard.track import Track
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
    )
from picard.util.thread import ThreadAssist
from picard.webservice import XmlWebService


class Log(object):

    def _message(self, prefix, message, args, kwargs):
        if args:
            message = message % args
        if isinstance(message, unicode):
            message = message.encode("utf-8", "replace")
        print prefix, QtCore.QThread.currentThreadId(), QtCore.QTime.currentTime().toString(), message

    def debug(self, message, *args, **kwargs):
        pass

    def info(self, message, *args, **kwargs):
        self._message("I:", message, args, kwargs)

    def warning(self, message, *args, **kwargs):
        self._message("W:", message, args, kwargs)

    def error(self, message, *args, **kwargs):
        self._message("E:", message, args, kwargs)


class DebugLog(Log):

    def debug(self, message, *args, **kwargs):
        self._message("D:", message, args, kwargs)


class Tagger(QtGui.QApplication):

    """

    Signals:
      - file_state_changed
      - file_updated(file)
      - file_added_to_cluster(cluster, file)
      - file_removed_from_cluster(cluster, file)

      - cluster_added(cluster)
      - cluster_removed(album, index)

      - album_added(album)
      - album_updated(album, update_tracks)
      - album_removed(album, index)

      - track_updated(track)

    """

    options = [
        IntOption("persist", "last_version_check", 0),
    ]

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
        self.cachedir = os.path.join(self.userdir, "cache")

        # Setup logging
        if debug or "PICARD_DEBUG" in os.environ:
            self.log = DebugLog()
        else:
            self.log = Log()
        self.log.debug("Starting Picard %s from %r", picard.__version__, os.path.abspath(__file__))

        # TODO remove this before the final release
        if sys.platform == "win32":
            olduserdir = "~\\Local Settings\\Application Data\\MusicBrainz Picard"
        else:
            olduserdir = "~/.picard"
        olduserdir = os.path.expanduser(olduserdir)
        if os.path.isdir(olduserdir):
            self.log.info("Moving %s to %s", olduserdir, self.userdir)
            shutil.move(olduserdir, self.userdir)

        QtCore.QObject.tagger = self
        QtCore.QObject.config = self.config
        QtCore.QObject.log = self.log

        self.setup_gettext(localedir)

        # Initialize threading and allocate threads
        self.stopping = False
        self.thread_assist = ThreadAssist(self)
        self.load_thread = self.thread_assist.allocate()
        self.save_thread = self.thread_assist.allocate()
        self.util_thread = self.thread_assist.allocate()
        self.analyze_thread = self.thread_assist.allocate()

        self.xmlws = XmlWebService(self.cachedir)

        # Initialize fingerprinting
        self._ofa = musicdns.OFA()
        self.analyze_thread.add_task(self._ofa.init)

        # Load plugins
        self.pluginmanager = PluginManager()
        self.pluginmanager.load(os.path.join(os.path.dirname(sys.argv[0]), "plugins"))
        self.pluginmanager.load(os.path.join(self.userdir, "plugins"))

        self.puidmanager = PUIDManager()

        self.browser_integration = BrowserIntegration()

        self.files = {}

        self.clusters = ClusterList()
        self.albums = []

        self.unmatched_files = UnmatchedFiles()
        self.window = MainWindow()

    def setup_gettext(self, localedir):
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
            self.log.debug("Loading gettext translation, localedir=%r", localedir)
            self.translation = gettext.translation("picard", localedir)
            self.translation.install(True)
            ngettext = self.translation.ngettext
        except IOError:
            __builtin__.__dict__['_'] = lambda a: a
            def ngettext(a, b, c):
                if c == 1: return a
                else: return b
        __builtin__.__dict__['ngettext'] = ngettext

    def move_files_to_album(self, files, albumid=None, album=None):
        """Move `files` to tracks on album `albumid`."""
        if album is None:
            album = self.load_album(albumid)
        if album.loaded:
            album.match_files(files)
        else:
            for file in [file for file in files]:
                file.move(album.unmatched_files)

    def move_file_to_album(self, file, albumid=None, album=None):
        """Move `file` to a track on album `albumid`."""
        self.move_files_to_album([file], albumid)

    def move_file_to_track(self, file, albumid, trackid):
        """Move `file` to track `trackid` on album `albumid`."""
        album = self.load_album(albumid)
        if album.loaded:
            album.match_file(file, trackid)
        else:
            file.move(album.unmatched_files)

    def exit(self):
        self.stopping = True
        self.analyze_thread.add_task(self._ofa.done)
        self.thread_assist.stop()
        self.browser_integration.stop()
        self.xmlws.cleanup()

    def _download_new_version(self):
        res = QtGui.QMessageBox.information(
            self.window, _("New Version"), _("New version of Picard is available (%s). Would you like to download it now?") % self._new_version,
            QtGui.QMessageBox.StandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No))
        del self._new_version
        if res == QtGui.QMessageBox.Yes:
            webbrowser2.open("http://musicbrainz.org/doc/PicardQt")

    def _check_version_request_finished(self, data, http, error):
        if not error:
            new_version_string = data.strip()
            if new_version_string > version_string:
                self._new_version = new_version_string
                QtCore.QTimer.singleShot(0, self._download_new_version)

    def _check_version(self):
        now = int(time.time())
        if self.config.persist['last_version_check'] < now - 60 * 60 * 24:
            self.config.persist['last_version_check'] = now
            self.xmlws.download('ftp.musicbrainz.org', 80, '/pub/musicbrainz/users/luks/picard-qt/version.txt', self._check_version_request_finished)

    def _run_init(self):
        if self._autoupdate:
            self._check_version()
        if self._args:
            self.add_files(map(decode_filename, files))
            del self._args

    def run(self):
        self.browser_integration.start()
        self.window.show()
        QtCore.QTimer.singleShot(0, self._run_init)
        res = self.exec_()
        self.exit()
        return res

    def add_files(self, filenames):
        """Add files to the tagger."""
        def file_loaded(file):
            if not file.has_error():
                puid = file.metadata['musicip_puid']
                trackid = file.metadata['musicbrainz_trackid']
                albumid = file.metadata['musicbrainz_albumid']
                self.puidmanager.add(puid, trackid)
                if albumid:
                    if trackid:
                        self.move_file_to_album(file, albumid)
                    else:
                        self.move_file_to_track(file, albumid, trackid)
                elif self.config.setting['analyze_new_files']:
                    self.analyze([file])
        self.log.debug("Adding files %r", filenames)
        new_files = []
        for filename in filenames:
            filename = os.path.normpath(filename)
            if filename not in self.files:
                file = open_file(filename)
                if file:
                    self.files[filename] = file
                    new_files.append(file)
        if new_files:
            self.unmatched_files.add_files(new_files)
            for file in new_files:
                file.load(finished=file_loaded)

    def add_directory(self, directory):
        """Add all files from the directory ``directory`` to the tagger."""
        directory = os.path.normpath(directory)
        self.log.debug("Adding directory %r", directory)
        def read_directory(path):
            directories = [path]
            while directories and not self.util_thread.stopping:
                path = directories.pop()
                self.window.set_statusbar_message(N_("Reading directory %s ..."), path)
                files = []
                for info in QtCore.QDir(path).entryInfoList(QtCore.QDir.AllEntries | QtCore.QDir.NoDotAndDotDot):
                    path = info.absoluteFilePath()
                    if info.isDir():
                        directories.append(path)
                    else:
                        files.append(unicode(path))
                if files:
                    self.thread_assist.proxy_to_main(self.add_files, files)
            self.thread_assist.proxy_to_main(self.window.clear_statusbar_message)
        self.util_thread.add_task(read_directory, directory)

    def get_file_by_id(self, id):
        """Get file by a file ID."""
        for file in self.files.values():
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

    def search(self, text, type):
        """Search on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        getattr(lookup, type + "Search")(text)

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

    def get_files_from_objects(self, objects):
        """Return list of files from list of albums, clusters, tracks or files."""
        files = []
        for obj in objects:
            if isinstance(obj, Album):
                for track in obj.tracks:
                    if track.linked_file and track.linked_file not in files:
                        files.append(track.linked_file)
                for file in obj.unmatched_files.files:
                    if file not in files:
                        files.append(file)
            elif isinstance(obj, Track):
                if obj.linked_file and obj.linked_file not in files:
                    files.append(obj.linked_file)
            elif isinstance(obj, Cluster):
                for file in obj.files:
                    if file not in files:
                        files.append(file)
            elif isinstance(obj, ClusterList):
                for cluster in obj:
                    for file in cluster.files:
                        if file not in files:
                            files.append(file)
            elif isinstance(obj, File):
                if obj not in files:
                    files.append(obj)
        return files

    def save(self, objects):
        """Save the specified objects."""
        self.set_wait_cursor()
        self.save_thread.add_task(self.__save_thread, self.get_files_from_objects(objects))

    def __rename_file(self, file):
        old_filename = file.filename
        new_filename, ext = os.path.splitext(file.make_filename())
        if old_filename != new_filename + ext:
            new_dirname = os.path.dirname(new_filename)
            if not os.path.isdir(encode_filename(new_dirname)):
                os.makedirs(new_dirname)
            tmp_filename = new_filename
            i = 1
            while (not pathcmp(old_filename, new_filename + ext) and
                   os.path.exists(encode_filename(new_filename + ext))):
                new_filename = "%s (%d)" % (tmp_filename, i)
                i += 1
            new_filename = new_filename + ext
            self.log.debug("Moving file %r => %r", old_filename, new_filename)
            shutil.move(encode_filename(old_filename), encode_filename(new_filename))
            file.filename = new_filename
            del self.files[old_filename]
            self.files[new_filename] = file
        return old_filename

    def __save_thread(self, files):
        """Save the files."""
        # FIXME: move most of this to file.py
        saved = []
        unsaved = []
        todo = len(files)
        for file in files:
            self.window.set_statusbar_message(N_("Saving file %s ..."), file.filename)
            error = None
            try:
                # Write tags to files
                if not self.config.setting["dont_write_tags"]:
                    file.save()
                # Rename files
                old_filename = self.__rename_file(file)
                # Move extra files (images, playlists, etc.)
                if (self.config.setting["move_files"] and
                    self.config.setting["move_additional_files"]):
                    file.move_additional_files(old_filename)
                # Delete empty directories
                if self.config.setting["delete_empty_dirs"]:
                    try: os.removedirs(encode_filename(os.path.dirname(old_filename)))
                    except EnvironmentError: pass
                # Save cover art images
                if self.config.setting["save_images_to_files"]:
                    file.save_images()
            except Exception, e:
                self.log.error(traceback.format_exc())
                error = str(e)
            todo -= 1
            self.thread_assist.proxy_to_main(self.__save_finished, file, error, todo)
        self.thread_assist.proxy_to_main(self.window.clear_statusbar_message)

    def __save_finished(self, file, error, todo):
        """Finalize file saving and notify views."""
        # FIXME: move this to file.py
        if error is None:
            file.state = File.NORMAL
            length = file.orig_metadata.length
            file.orig_metadata.copy(file.metadata)
            file.orig_metadata.length = length
            file.metadata.changed = False
        else:
            file.state = File.ERROR
            file.error = error
        file.update()
        if todo == 0:
            self.restore_cursor()

    def load_album(self, id, catalognumber=None):
        album = self.get_album_by_id(id)
        if album:
            return album
        album = Album(id, catalognumber=catalognumber)
        self.albums.append(album)
        self.emit(QtCore.SIGNAL("album_added"), album)
        album.load()
        return album

    def reload_album(self, album):
        album.load(force=True)

    def get_album_by_id(self, id):
        for album in self.albums:
            if album.id == id:
                return album
        return None


    def remove_files(self, files, from_parent=True):
        """Remove files from the tagger."""
        for file in files:
            del self.files[file.filename]
            file.remove(from_parent)

    def remove_album(self, album):
        """Remove the specified album."""
        self.log.debug("Removing %r", album)
        self.remove_files(self.get_files_from_objects([album]))
        self.albums.remove(album)
        self.emit(QtCore.SIGNAL("album_removed"), album)

    def remove_cluster(self, cluster):
        """Remove the specified cluster."""
        if not cluster.special:
            self.log.debug("Removing %r", cluster)
            self.remove_files(cluster.files, from_parent=False)
            self.clusters.remove(cluster)
            self.emit(QtCore.SIGNAL("cluster_removed"), cluster)

    def remove(self, objects):
        """Remove the specified objects."""
        files = []
        for obj in objects:
            if isinstance(obj, File):
                files.append(obj)
            elif isinstance(obj, Track):
                if obj.linked_file:
                    files.append(obj.linked_file)
            elif isinstance(obj, Album):
                self.remove_album(obj)
            elif isinstance(obj, Cluster):
                self.remove_cluster(obj)
        if files:
            self.remove_files(files)


    def lookup_cd(self, action=None):
        """Reads CD from the selected drive and tries to lookup the DiscID on MusicBrainz."""
        if action is None:
            device = self.config.setting["cd_lookup_device"].split(",", 1)[0]
        else:
            device = unicode(action.text())

        def read_disc_error(self, error):
            self.restore_cursor()
            QtGui.QMessageBox.critical(self.window, _(u"CD Lookup Error"), _(u"Error while reading CD:\n\n%s") % error)

        def read_disc_finished(self, disc):
            self.restore_cursor()
            disc.lookup()

        def read_disc_thread(self, disc, device):
            try:
                disc.read(encode_filename(device))
            except (NotImplementedError, DiscError), e:
                self.thread_assist.proxy_to_main(read_disc_error, self, str(e))
            else:
                self.thread_assist.proxy_to_main(read_disc_finished, self, disc)

        disc = Disc()
        self.set_wait_cursor()
        self.util_thread.add_task(read_disc_thread, self, disc, device)


    def analyze(self, objs):
        """Analyze the file(s)."""
        files = self.get_files_from_objects(objs)
        for file in files:
            file.set_pending()
            def analyze_finished(file, puid):
                if file.state == File.PENDING:
                    if puid:
                        self.puidmanager.add(puid, None)
                        file.metadata['musicip_puid'] = puid
                        file.lookup_puid(puid)
                    else:
                        self.window.set_statusbar_message(N_("Couldn't find PUID for file %s"), file.filename)
                        file.clear_pending()
            self._ofa.analyze(file, analyze_finished)

    # =======================================================================
    #  Metadata-based lookups
    # =======================================================================

    def autotag(self, objects):
        for obj in objects:
            if isinstance(obj, (File, Cluster)):
                obj.lookup_metadata()

    # =======================================================================
    #  Clusters
    # =======================================================================

    def cluster(self, objs):
        """Group files with similar metadata to 'clusters'."""
        self.log.debug("Clustering %r", objs)
        if len(objs) <= 1:
            objs = [self.unmatched_files]
        fcmp = lambda a, b: (
            cmp(a.discnumber, b.discnumber) or
            cmp(a.tracknumber, b.tracknumber) or
            cmp(a.base_filename, b.base_filename))
        files = self.get_files_from_objects(objs)
        for name, artist, files in Cluster.cluster(files, 1.0):
            QtCore.QCoreApplication.processEvents()
            cluster = Cluster(name, artist)
            self.clusters.append(cluster)
            self.emit(QtCore.SIGNAL("cluster_added"), cluster)
            for file in sorted(files, fcmp):
                file.move(cluster)

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
        albums = [obj for obj in objs if isinstance(obj, Album)]
        for album in albums:
            self.reload_album(album)

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
