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
import socket
import sys
import urllib2
import traceback
import time
import imp

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

from picard import musicdns
from picard.album import Album
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster, ClusterList, UnmatchedFiles
from picard.config import Config
from picard.file import File
from picard.formats import open as open_file
from picard.metadata import Metadata
from picard.track import Track
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
    strip_non_alnum,
    icontheme,
    )
from picard.util.cachedws import CachedWebService
from picard.util.search import LuceneQueryFilter
from picard.util.thread import ThreadAssist
from picard.webservice import XmlWebService

from picard.disc import Disc, DiscError

from musicbrainz2.utils import extractUuid
from musicbrainz2.webservice import (
     WebService,
     Query,
     TrackFilter,
     ReleaseFilter,
     WebServiceError
     )

MUSICDNS_KEY = "80eaa76658f99dbac1c58cc06aa44779"


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

    __instance = None

    def __init__(self, localedir):
        QtGui.QApplication.__init__(self, sys.argv)
        self.__class__.__instance = self

        self.config = Config()

        # set default socket timeout to 10 seconds
        socket.setdefaulttimeout(10.0)

        if sys.platform == "win32":
            self.userdir = "~\\Local Settings\\Application Data\\MusicBrainz Picard"
        else:
            self.userdir = "~/.picard"
        self.userdir = os.path.expanduser(self.userdir)
        self.cachedir = os.path.join(self.userdir, "cache")

        self.setup_logging()
        self.log.debug("Starting Picard %s from %s", picard.__version__, os.path.abspath(__file__))

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

        self.browser_integration.start()

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
            self.log.debug(u"Loading gettext translation, localedir=%r", localedir)
            self.translation = gettext.translation("picard", localedir)
            self.translation.install(True)
        except IOError, e:
            __builtin__.__dict__['_'] = lambda a: a
            self.log.info(e)

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
        CachedWebService.cleanup(self.cachedir)

    def run(self):
        self.window.show()
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
                    file.load()

    def add_directory(self, directory):
        """Add all files from the directory ``directory`` to the tagger."""
        directory = os.path.normpath(directory)
        self.log.debug(u"Adding directory %r", directory)
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
        file.lock_for_read()
        try:
            filename = file.filename
            metadata = Metadata()
            metadata.copy(file.metadata)
        finally:
            file.unlock()

        if self.config.setting["move_files"]:
            new_dirname = self.config.setting["move_files_to"]
        else:
            new_dirname = os.path.dirname(filename)
        old_dirname = new_dirname

        new_filename, ext = os.path.splitext(os.path.basename(filename))

        if self.config.setting["rename_files"]:
            # replace incompatible characters
            for name in metadata.keys():
                value = metadata[name]
                if isinstance(value, basestring):
                    value = sanitize_filename(value)
                    if (self.config.setting["windows_compatible_filenames"]
                        or sys.platform == "win32"):
                        value = replace_win32_incompat(value)
                    if self.config.setting["ascii_filenames"]:
                        value = replace_non_ascii(value)
                    metadata[name] = value
            # expand the naming format
            if metadata["compilation"] == "1":
                format = self.config.setting["va_file_naming_format"]
            else:
                format = self.config.setting["file_naming_format"]
            new_filename = ScriptParser().eval(format, metadata)
            if not self.config.setting["move_files"]:
                new_filename = os.path.basename(new_filename)
            new_filename = make_short_filename(new_dirname, new_filename)
            # win32 compatibility fixes
            if self.config.setting['windows_compatible_filenames'] or sys.platform == 'win32':
                new_filename = new_filename.replace('./', '_/').replace('.\\', '_\\')

        old_filename = filename
        new_filename = os.path.join(new_dirname, new_filename)

        if filename != new_filename + ext:
            new_dirname = os.path.dirname(new_filename)
            if not os.path.isdir(encode_filename(new_dirname)):
                os.makedirs(new_dirname)
            filename = new_filename
            i = 1
            while os.path.exists(encode_filename(new_filename + ext)):
                new_filename = u"%s (%d)" % (filename, i)
                i += 1
            self.log.debug(u"Moving file %r => %r", old_filename, new_filename + ext)
            shutil.move(encode_filename(old_filename),
                        encode_filename(new_filename + ext))
            file.lock_for_write()
            file.filename = new_filename + ext
            file.unlock()

        del self.files[old_filename]
        self.files[file.filename] = file

        return old_filename

    def __save_thread(self, files):
        """Save the files."""
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
        if error is None:
            file.state = File.NORMAL
            file.orig_metadata.copy(file.metadata)
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

    # Auto-tagging

    def autotag(self, objects):
        files = []
        for obj in objects:
            if isinstance(obj, Cluster):
                self.thread_assist.spawn(self.__autotag_cluster_thread, obj)
            elif isinstance(obj, File):
                files.append(obj)
        if files:
            self.thread_assist.spawn(self.__autotag_files_thread, files)

    def __autotag_cluster_thread(self, cluster):
        self.window.set_statusbar_message('Looking up metadata for cluster %s...', cluster.metadata['album'])
        q = Query(ws=self.get_web_service())
        matches = []
        filter = LuceneQueryFilter(
            artist=cluster.metadata['artist'],
            release=cluster.metadata['album'],
            limit=5)
        try:
            results = q.getReleases(filter=filter)
        except Exception, e:
            self.window.set_statusbar_message('MusicBrainz lookup failed: %s', e, timeout=3000)
            return
        if not results:
            self.window.set_statusbar_message('No matches found for cluster %s', cluster.metadata['album'], timeout=3000)
        for res in results:
            metadata = Metadata()
            metadata.from_release(res.release)
            score = cluster.metadata.compare(metadata)
            matches.append((score, metadata['musicbrainz_albumid']))
        matches.sort(reverse=True)
        self.log.debug("Matches: %r", matches)
        if matches and matches[0][0] >= self.config.setting['cluster_lookup_threshold']:
            self.window.set_statusbar_message('Cluster %s identified!', cluster.metadata['album'], timeout=3000)
            self.thread_assist.proxy_to_main(self.move_files_to_album, cluster.files, matches[0][1])

    def __autotag_files_thread(self, files):
        q = Query(ws=self.get_web_service())
        for file in files:
            self.window.set_statusbar_message('Looking up metadata for file %s...', file.filename)
            matches = []
            filter = LuceneQueryFilter(
                track=file.metadata['title'],
                artist=file.metadata['artist'],
                release=file.metadata['album'],
                tnum=file.metadata['tracknumber'],
                limit=5)
            try:
                results = q.getTracks(filter=filter)
            except Exception, e:
                self.window.set_statusbar_message('MusicBrainz lookup failed: %s', e, timeout=3000)
                continue
            # no matches
            if not results:
                self.window.set_statusbar_message('No matches found for file %s', file.filename, timeout=3000)
                continue
            # multiple matches
            for res in results:
                metadata = Metadata()
                metadata.from_track(res.track)
                score = file.orig_metadata.compare(metadata)
                matches.append((score, metadata['musicbrainz_albumid'], metadata['musicbrainz_trackid']))
            matches.sort(reverse=True)
            self.log.debug("Matches: %r", matches)
            if matches[0][0] >= self.config.setting['file_lookup_threshold']:
                self.window.set_statusbar_message('File %s identified!', file.filename, timeout=3000)
                self.thread_assist.proxy_to_main(self.move_file_to_track, file, matches[0][1], matches[0][2])
            else:
                self.window.set_statusbar_message('No similar matches found for file %s', file.filename, timeout=3000)

    def autotag_(self, objects):
        self.set_wait_cursor()
        try:
            # TODO: move to a separate thread
            import math

            files = self.get_files_from_objects(objects)
            self.log.debug(u"Auto-tagging started... %r", files)

            # Do metadata lookups for all files
            q = Query(ws=self.get_web_service())
            for file in files:
                flt = TrackFilter(title=file.metadata["title"],
                    artistName=strip_non_alnum(file.metadata["artist"]),
                    releaseTitle=strip_non_alnum(file.metadata["album"]),
                    duration=file.metadata.get("~#length", 0),
                    limit=5)
                tracks = q.getTracks(filter=flt)
                file.matches = []
                for result in tracks:
                    metadata = Metadata()
                    metadata.from_track(result.track)
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
        finally:
            self.restore_cursor()

    def get_web_service(self, cached=True, **kwargs):
        if "host" not in kwargs:
            kwargs["host"] = self.config.setting["server_host"]
        if "port" not in kwargs:
            kwargs["port"] = self.config.setting["server_port"]
        if "username" not in kwargs:
            kwargs["username"] = self.config.setting["username"]
        if "password" not in kwargs:
            kwargs["password"] = self.config.setting["password"]
        if self.config.setting["use_proxy"]:
            http = "http://"
            if self.config.setting["proxy_username"]:
                http += self.config.setting["proxy_username"]
                if self.config.setting["proxy_password"]:
                    http += ":" + self.config.setting["proxy_password"]
                http += "@"
            http += "%s:%d" % (self.config.setting["proxy_server_host"],
                               self.config.setting["proxy_server_port"])
            kwargs['opener'] = urllib2.build_opener(
                urllib2.ProxyHandler({'http': http}))
        return CachedWebService(cachedir=self.cachedir, force=not cached,
                                **kwargs)

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
    #  Text-based lookups
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
        self.log.debug("Removing %r", cluster)
        for file in cluster.files:
            del self.files[file.filename]
        index = self.clusters.index(cluster)
        del self.clusters[index]
        self.emit(QtCore.SIGNAL("cluster_removed"), cluster, index)

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
