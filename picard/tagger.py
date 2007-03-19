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

import picard.resources
import picard.plugins

from picard import musicdns, version_string
from picard.album import Album
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster, ClusterList, UnmatchedFiles
from picard.config import Config
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
    )
from picard.util.thread import ThreadAssist
from picard.webservice import XmlWebService
from picard.disc import Disc, DiscError


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

    def __init__(self, localedir):
        QtGui.QApplication.__init__(self, sys.argv)
        self.__class__.__instance = self

        self.config = Config()

        if sys.platform == "win32":
            self.userdir = "~\\Local Settings\\Application Data\\MusicBrainz Picard"
        else:
            self.userdir = "~/.picard"
        self.userdir = os.path.expanduser(self.userdir)
        self.cachedir = os.path.join(self.userdir, "cache")

        self.setup_logging()
        self.log.debug("Starting Picard %s from %r", picard.__version__, os.path.abspath(__file__))

        QtCore.QObject.tagger = self
        QtCore.QObject.config = self.config
        QtCore.QObject.log = self.log

        self.setup_gettext(localedir)

        self.stopping = False
        self.thread_assist = ThreadAssist(self)

        self.xmlws = XmlWebService(self.cachedir)

        # Initialize fingerprinting
        self._analyze_queue = []
        self._ofa = musicdns.OFA()
        self.load_thread = self._analyze_thread = self.thread_assist.allocate()
        self.thread_assist.spawn(self._ofa.init, thread=self._analyze_thread)

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
        self.connect(self.window, QtCore.SIGNAL("file_updated(int)"), QtCore.SIGNAL("file_updated(int)"))

        if hasattr(QtGui.QStyle, 'SP_DirIcon'):
            self.dir_icon = self.style().standardIcon(QtGui.QStyle.SP_DirIcon)
        else:
            self.dir_icon = icontheme.lookup('folder', icontheme.ICON_SIZE_MENU)
        self.file_icon = QtGui.QIcon(":/images/file.png")
        self.cd_icon = icontheme.lookup('media-optical', icontheme.ICON_SIZE_MENU)
        self.note_icon = QtGui.QIcon(":/images/note.png")
        self.error_icon = icontheme.lookup('dialog-error', icontheme.ICON_SIZE_MENU)
        self.match_icons = [
            QtGui.QIcon(":/images/match-50.png"),
            QtGui.QIcon(":/images/match-60.png"),
            QtGui.QIcon(":/images/match-70.png"),
            QtGui.QIcon(":/images/match-80.png"),
            QtGui.QIcon(":/images/match-90.png"),
            QtGui.QIcon(":/images/match-100.png"),
        ]
        self.saved_icon = QtGui.QIcon(":/images/track-saved.png")

    def setup_logging(self):
        """Setup loggers."""
        self.log = logging.getLogger()
        if picard.version_info[3] != 'final':
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.WARNING)
        formatter = logging.Formatter(u"%(thread)s %(asctime)s %(message)s", u"%H:%M:%S")
        # Logging to console
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        self.log.addHandler(console)
        # Logging to file
        try:
            logdir = os.path.join(self.userdir, "logs")
            if not os.path.isdir(logdir):
                os.makedirs(logdir)
            logfile = logging.FileHandler(os.path.join(logdir, time.strftime('%Y-%m-%d.log')))
            logfile.setFormatter(formatter)
            self.log.addHandler(logfile)
        except EnvironmentError:
            pass

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
        except IOError:
            __builtin__.__dict__['_'] = lambda a: a

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
        self.thread_assist.spawn(self._ofa.done, thread=self._analyze_thread)
        self.thread_assist.stop()
        self.browser_integration.stop()
        self.xmlws.cleanup()

    def _check_version_request_finished(self, data, http, error):
        if not error:
            new_version_string = data.strip()
            if new_version_string > version_string:
                res = QtGui.QMessageBox.information(
                    self.window, _("New Version"), _("New version of Picard is available (%s). Would you like to download it now?") % new_version_string,
                    QtGui.QMessageBox.StandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No))
                if res == QtGui.QMessageBox.Yes:
                    webbrowser2.open("http://musicbrainz.org/doc/PicardQt")

    def check_version(self):
        now = int(time.time())
        if self.config.persist['last_version_check'] < now - 60 * 60 * 24:
            self.config.persist['last_version_check'] = now
            self.xmlws.download('ftp.musicbrainz.org', 80, '/pub/musicbrainz/users/luks/picard-qt/version.txt', self._check_version_request_finished)

    def run(self):
        self.browser_integration.start()
        self.window.show()
        self.check_version()
        self.add_files(map(decode_filename, sys.argv[1:]))
        res = self.exec_()
        self.exit()
        return res

    def add_files(self, filenames):
        """Add files to the tagger."""
        self.log.debug("Adding files %r", filenames)
        for filename in filenames:
            filename = os.path.normpath(filename)
            if filename not in self.files:
                file = open_file(filename)
                if file:
                    self.files[filename] = file
                    file.move(self.unmatched_files)
                    file.load(finished=self._file_loaded)

    def _file_loaded(self, file):
        puid = file.metadata['musicip_puid']
        trackid = file.metadata['musicbrainz_trackid']
        albumid = file.metadata['musicbrainz_albumid']
        if puid and trackid:
            self.puidmanager.add(puid, trackid)
        if albumid:
            if trackid:
                self.move_file_to_album(file, albumid)
            else:
                self.move_file_to_track(file, albumid, trackid)
        elif self.config.setting['analyze_new_files']:
            self.analyze([file])

    def add_directory(self, directory):
        """Add all files from the directory ``directory`` to the tagger."""
        directory = os.path.normpath(directory)
        self.log.debug("Adding directory %r", directory)
        self.thread_assist.spawn(self.__read_directory_thread, directory, thread=self.load_thread)

    def __read_directory_thread(self, directory):
        self.window.set_statusbar_message(N_("Reading directory %s ..."), directory)
        directory = encode_filename(directory)
        filenames = []
        for name in os.listdir(directory):
            name = os.path.join(directory, name)
            if os.path.isdir(name):
                self.thread_assist.proxy_to_main(self.add_directory, decode_filename(name))
            else:
                filenames.append(decode_filename(name))
        self.thread_assist.proxy_to_main(self.window.clear_statusbar_message)
        if filenames:
            self.thread_assist.proxy_to_main(self.add_files, filenames)

    def get_file_by_id(self, id):
        """Get file by a file ID."""
        for file in self.files.values():
            if file.id == id:
                return file
        return None

    def get_file_by_filename(self, filename):
        """Get file by a filename."""
        return self.files.get(filename, None)

    def remove_files(self, files):
        """Remove files from the tagger."""
        for file in files:
            file.remove()
            del self.files[file.filename]

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
        self.thread_assist.spawn(self.__save_thread,
            self.get_files_from_objects(objects))

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
            file.filename = new_filename + ext
            self.log.debug("Moving file %r => %r", old_filename, file.filename)
            shutil.move(encode_filename(old_filename), encode_filename(file.filename))
            del self.files[old_filename]
            self.files[file.filename] = file
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
            length, length2 = file.orig_metadata["~#length"], file.orig_metadata["~length"]
            file.orig_metadata.copy(file.metadata)
            file.orig_metadata["~#length"] = length
            file.orig_metadata["~length"] = length2
            file.metadata.changed = False
        else:
            file.state = File.ERROR
            file.error = error
        file.update()
        if todo == 0:
            self.restore_cursor()

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

    def load_album(self, id):
        album = self.get_album_by_id(id)
        if album:
            return album
        album = Album(id)
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

    def remove_album(self, album):
        """Remove the specified album."""
        self.remove_files(self.get_files_from_objects([album]))
        index = self.albums.index(album)
        del self.albums[index]
        self.emit(QtCore.SIGNAL("album_removed"), album, index)

    def lookup_cd(self, action=None):
        if action is None:
            device = self.config.setting["cd_lookup_device"].split(",", 1)[0]
        else:
            device = unicode(action.text())
        disc = Disc()
        self.set_wait_cursor()
        self.thread_assist.spawn(self._read_disc_thread, disc, device)

    def _read_disc_thread(self, disc, device):
        try:
            disc.read(encode_filename(device))
        except (NotImplementedError, DiscError), e:
            self.thread_assist.proxy_to_main(self._read_disc_error, str(e))
            return
        self.thread_assist.proxy_to_main(disc.lookup)

    def _read_disc_error(self, error):
        self.restore_cursor()
        QtGui.QMessageBox.critical(self.window, _(u"CD Lookup Error"), _("Error while reading CD:\n\n%s") % error)

    # =======================================================================
    #  PUID lookups
    # =======================================================================

    def _lookup_puid(self, file, puid):
        if puid:
            self.puidmanager.add(puid, None)
            file.metadata['musicip_puid'] = puid
            file.lookup_puid(puid)
        else:
            self.window.set_statusbar_message(N_("Couldn't find PUID for file %s"), file.filename)
            file.clear_pending()
        self._analyze_from_queue()

    def _analyze_from_queue(self):
        while self._analyze_queue:
            file = self._analyze_queue.pop()
            if file.state == File.PENDING:
                self._ofa.analyze(file, self._lookup_puid)
                break

    def analyze(self, objs):
        analyzing = len(self._analyze_queue) > 0
        for file in self.get_files_from_objects(objs):
            file.set_pending()
            self._analyze_queue.append(file)
        if not analyzing:
            self._analyze_from_queue()

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
        files = self.get_files_from_objects(objs)
        for name, artist, files in Cluster.cluster(files, 1.0):
            QtCore.QCoreApplication.processEvents()
            cluster = Cluster(name, artist)
            self.clusters.append(cluster)
            self.emit(QtCore.SIGNAL("cluster_added"), cluster)
            for file in files:
                file.move(cluster)

    def remove_cluster(self, cluster):
        """Remove the specified cluster."""
        if not cluster.special:
            self.log.debug("Removing %r", cluster)
            for file in cluster.files:
                del self.files[file.filename]
            index = self.clusters.index(cluster)
            del self.clusters[index]
            self.emit(QtCore.SIGNAL("cluster_removed"), cluster, index)

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


def main(localedir=None):
    tagger = Tagger(localedir)
    sys.exit(tagger.run())
