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

import picard.resources
import picard.plugins

import picard.formats
from picard import musicdns
from picard.album import Album
from picard.api import IFileOpener
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster, ClusterList, UnmatchedFiles
from picard.component import ComponentManager, ExtensionPoint, Component
from picard.config import Config
from picard.file import File
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
    )
from picard.util.cachedws import CachedWebService
from picard.util.search import LuceneQueryFilter
from picard.util.thread import ThreadAssist

from musicbrainz2.utils import extractUuid
from musicbrainz2.webservice import (
     WebService,
     Query,
     TrackFilter,
     ReleaseFilter,
     WebServiceError
     )

MUSICDNS_KEY = "80eaa76658f99dbac1c58cc06aa44779"


class Tagger(QtGui.QApplication, ComponentManager, Component):

    file_openers = ExtensionPoint(IFileOpener)

    def __init__(self, localedir):
        QtGui.QApplication.__init__(self, sys.argv)
        ComponentManager.__init__(self)

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

        self.thread_assist = ThreadAssist(self)
        self.load_thread = self.thread_assist.allocate()

        # Initialize fingerprinting
        self._ofa = musicdns.OFA()
        self._analyze_thread = self.thread_assist.allocate()
        self.thread_assist.spawn(self._ofa.init, thread=self._analyze_thread)

        # Load plugins
        self.pluginmanager = PluginManager()
        self.pluginmanager.load(os.path.join(os.path.dirname(sys.argv[0]), "plugins"))
        self.pluginmanager.load(os.path.join(self.userdir, "plugins"))

        self.puidmanager = PUIDManager()

        self.__files_to_be_moved = []

        self.browser_integration = BrowserIntegration()

        self.files = []
        self.clusters = ClusterList()
        self.albums = []

        self.unmatched_files = UnmatchedFiles()

        self.window = MainWindow()
        self.connect(self.window, QtCore.SIGNAL("file_updated(int)"), QtCore.SIGNAL("file_updated(int)"))

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
            for file in files:
                self.__files_to_be_moved.append((file, album))

    def move_file_to_album(self, file, albumid=None, album=None):
        """Move `file` to a track on album `albumid`."""
        self.move_files_to_album([file], albumid)

    def move_file_to_track(self, file, albumid, trackid):
        """Move `file` to track `trackid` on album `albumid`."""
        album = self.load_album(albumid)
        if album.loaded:
            album.match_file(file, trackid)
        else:
            self.__files_to_be_moved.append((file, album, trackid))

    def exit(self):
        self.thread_assist.spawn(self._ofa.done, thread=self._analyze_thread)
        self.thread_assist.stop()
        self.browser_integration.stop()
        CachedWebService.cleanup(self.cachedir)

    def run(self):
        self.window.show()
        res = self.exec_()
        self.exit()
        return res

    def __set_status_bar_message(self, message, args=(), timeout=0):
        self.window.set_status_bar_message(_(message) % args, timeout)

    def __clear_status_bar_message(self):
        self.window.clear_status_bar_message()

    def get_supported_formats(self):
        """Returns list of supported formats.

        Format:
            [('.mp3', 'MPEG Layer-3 File'), ('.cue', 'Cuesheet'), ...]
        """
        formats = []
        for opener in self.file_openers:
            formats.extend(opener.get_supported_formats())
        return formats

    def add_files(self, filenames):
        """Add files to the tagger."""
        self.log.debug(u"Adding files %r", filenames)
        for filename in filenames:
            filename = os.path.normpath(filename)
            if self.get_file_by_filename(filename):
                continue
            for opener in self.file_openers:
                file = opener.open_file(filename)
                if not file:
                    continue
                file.move(self.unmatched_files)
                self.files.append(file)
                self.thread_assist.spawn(
                    self.__load_file_thread, file, thread=self.load_thread)

    def __load_file_thread(self, file):
        """Load metadata from the file."""
        self.log.debug(u"Loading file %r", file.filename)
        try:
            error = None
            file.load()
        except Exception, e:
            self.log.error(traceback.format_exc())
            error = str(e)
        self.thread_assist.proxy_to_main(self.__load_file_finished, file, error)

    def __load_file_finished(self, file, error):
        """Move loaded file to right album/cluster."""
        if error:
            file.state = File.ERROR
            file.error = error
        file.update()
        puid = file.metadata['musicip_puid']
        trackid = file.metadata['musicbrainz_trackid']
        if puid and trackid:
            self.puidmanager.add(puid, trackid)
        albumid = file.metadata['musicbrainz_albumid']
        if albumid:
            if trackid:
                self.move_file_to_album(file, albumid)
            else:
                self.move_file_to_track(file, albumid, trackid)

    def add_directory(self, directory):
        """Add all files from the directory ``directory`` to the tagger."""
        directory = os.path.normpath(directory)
        self.log.debug(u"Adding directory %r", directory)
        self.thread_assist.spawn(self.__read_directory_thread, directory, thread=self.load_thread)

    def __read_directory_thread(self, directory):
        self.log.debug(u"Reading directory %r", directory)
        self.thread_assist.proxy_to_main(
            self.__set_status_bar_message,
            N_("Reading directory %s ..."), directory)
        directory = encode_filename(directory)
        filenames = []
        for name in os.listdir(directory):
            name = os.path.join(directory, name)
            if os.path.isdir(name):
                self.thread_assist.proxy_to_main(self.add_directory, decode_filename(name))
            else:
                filenames.append(decode_filename(name))
        self.thread_assist.proxy_to_main(self.__clear_status_bar_message)
        if filenames:
            self.thread_assist.proxy_to_main(self.add_files, filenames)

    def get_file_by_id(self, id):
        """Get file by a file ID."""
        for file in self.files:
            if file.id == id:
                return file
        return None

    def get_file_by_filename(self, filename):
        """Get file by a filename."""
        for file in self.files:
            if file.filename == filename:
                return file
        return None

    def remove_files(self, files):
        """Remove files from the tagger."""
        for file in files:
            file.remove()
            del self.files[self.files.index(file)]

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

        return old_filename

    def __save_thread(self, files):
        """Save the files."""
        saved = []
        unsaved = []
        todo = len(files)
        for file in files:
            self.log.debug(u"Saving file %s", file)
            self.thread_assist.proxy_to_main(
                self.__set_status_bar_message, N_("Saving file %s ..."),
                file.filename)
            error = None
            try:
                file.save()
                file.state = File.SAVED
                old_filename = self.__rename_file(file)
                if (self.config.setting["move_files"] and
                    self.config.setting["move_additional_files"]):
                    file.move_additional_files(old_filename)
                # Clear empty directories
                try:
                    os.removedirs(encode_filename(os.path.dirname(old_filename)))
                except OSError:
                    pass
                if self.config.setting["save_images_to_files"]:
                    file.save_images()
            except Exception, e:
                self.log.error(traceback.format_exc())
                error = str(e)
            todo -= 1
            self.thread_assist.proxy_to_main(self.__save_finished, file, error, todo)
        self.thread_assist.proxy_to_main(self.__set_status_bar_message,
                                         N_("Done"))

    def __save_finished(self, file, error, todo):
        """Finalize file saving and notify views."""
        if error is None:
            file.state = File.SAVED
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
        """Load an album specified by MusicBrainz ID."""
        album = self.get_album_by_id(id)
        if album:
            return album
        album = Album(id, _("[loading album information]"))
        self.albums.append(album)
        self.emit(QtCore.SIGNAL("album_added"), album)
        self.thread_assist.spawn(self.__load_album_thread, album)
        return album

    def reload_album(self, album):
        album.name = _("[loading album information]")
        self.emit(QtCore.SIGNAL("album_updated"), album)
        self.thread_assist.spawn(self.__load_album_thread, album, True)

    def __load_album_thread(self, album, force=False):
        try:
            album.load(force)
        except Exception, e:
            self.log.error(traceback.format_exc())
            self.set_statusbar_message('Loading release failed: %s', e, timeout=3000)
            self.thread_assist.proxy_to_main(self.__load_album_failed, album)
        else:
            self.thread_assist.proxy_to_main(self.__load_album_finished, album)

    def __load_album_finished(self, album):
        self.emit(QtCore.SIGNAL("album_updated"), album)
        album.loaded = True
        for item in self.__files_to_be_moved:
            if item[1] == album:
                if len(item) == 3:
                    item[1].match_file(item[0], item[2])
                else:
                    item[1].match_file(item[0])

    def __load_album_failed(self, album):
        album.metadata['album'] = _("[couldn't load release %s]") % album.id
        self.emit(QtCore.SIGNAL("album_updated"), album)

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
        self.set_statusbar_message('Looking up metadata for cluster %s...', cluster.metadata['album'])
        q = Query(ws=self.get_web_service())
        matches = []
        filter = LuceneQueryFilter(
            artist=cluster.metadata['artist'],
            release=cluster.metadata['album'],
            limit=5)
        try:
            results = q.getReleases(filter=filter)
        except Exception, e:
            self.set_statusbar_message('MusicBrainz lookup failed: %s', e, timeout=3000)
            return
        if not results:
            self.set_statusbar_message('No matches found for cluster %s', cluster.metadata['album'], timeout=3000)
        for res in results:
            metadata = Metadata()
            metadata.from_release(res.release)
            score = cluster.metadata.compare(metadata)
            matches.append((score, metadata['musicbrainz_albumid']))
        matches.sort(reverse=True)
        self.log.debug("Matches: %r", matches)
        if matches and matches[0][0] >= self.config.setting['cluster_lookup_threshold']:
            self.set_statusbar_message('Cluster %s identified!', cluster.metadata['album'], timeout=3000)
            self.thread_assist.proxy_to_main(self.move_files_to_album, cluster.files, matches[0][1])

    def __autotag_files_thread(self, files):
        q = Query(ws=self.get_web_service())
        for file in files:
            self.set_statusbar_message('Looking up metadata for file %s...', file.filename)
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
                self.set_statusbar_message('MusicBrainz lookup failed: %s', e, timeout=3000)
                continue
            # no matches
            if not results:
                self.set_statusbar_message('No matches found for file %s', file.filename, timeout=3000)
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
                self.set_statusbar_message('File %s identified!', file.filename, timeout=3000)
                self.thread_assist.proxy_to_main(self.move_file_to_track, file, matches[0][1], matches[0][2])
            else:
                self.set_statusbar_message('No similar matches found for file %s', file.filename, timeout=3000)

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

    def lookup_cd(self):
        self.set_wait_cursor()
        self.thread_assist.spawn(self.__lookup_cd_thread)

    def __lookup_cd_thread(self):
        from musicbrainz2.disc import readDisc, getSubmissionUrl, DiscError
        try:
            disc = readDisc(
                encode_filename(self.config.setting["cd_lookup_device"]))
        except (NotImplementedError, DiscError), e:
            self.thread_assist.proxy_to_main(self.__lookup_cd_error, e)
            return

        try:
            q = Query(ws=self.get_web_service())
            releases = q.getReleases(filter=ReleaseFilter(discId=disc.getId()))
        except Exception, e:
            self.thread_assist.proxy_to_main(self.__lookup_cd_error, e)
            return

        url = getSubmissionUrl(disc, self.config.setting["server_host"],
                               self.config.setting["server_port"])
        self.thread_assist.proxy_to_main(self.__lookup_cd_finished,
                                         releases, url)

    def __lookup_cd_error(self, exception):
        self.restore_cursor()
        if isinstance(exception, NotImplementedError):
            QtGui.QMessageBox.critical(self.window, _(u"CD Lookup Error"),
                _(u"CD lookup not implemented. You need to have ctypes and "
                  u"libdiscid installed."))
        else:
            QtGui.QMessageBox.critical(self.window, _(u"CD Lookup Error"),
                _(u"Error while reading CD. Is there a CD in the drive?"))

    def __lookup_cd_finished(self, releases, url):
        self.restore_cursor()
        from picard.ui.cdlookup import CDLookupDialog
        dialog = CDLookupDialog(releases, url, self.window)
        dialog.exec_()

    def analyze(self, objs):
        """Analyze the selected files."""
        files = self.get_files_from_objects(objs)
        for file in files:
            file.state = File.PENDING
            file.update()
        self.thread_assist.spawn(self.__analyze_thread, files,
                                 thread=self._analyze_thread)

    def __puid_lookup_finished(self, file, puid, match):
        file.set_state(File.NORMAL, update=True)
        albumid = match[1]['musicbrainz_albumid']
        trackid = match[1]['musicbrainz_trackid']
        self.puidmanager.add(puid, trackid)
        self.move_file_to_track(file, albumid, trackid)

    def set_statusbar_message(self, message, *args, **kwargs):
        self.log.debug(message, *args)
        self.thread_assist.proxy_to_main(
            self.__set_status_bar_message, message, args, kwargs.get('timeout', 0))

    def __analyze_thread(self, files):
        """Analyze the specified files

        For each file:
            1. Decode it
            2. Use libofa to calculate the fingprint
            3. Lookup the fingerprint on MusicDNS
            4. Lookup the PUID from MusicDNS on MusicBrainz
            5. Calculate the similarities, move files to the matched tracks
        """
        from picard.musicdns import webservice as musicdns_ws
        ws = self.get_web_service(host="ofa.musicdns.org", pathPrefix="/ofa")

        for file in files:
            if file.state != File.PENDING:
                continue

            # Decode the file and calculate the fingerprint
            filename = file.filename
            self.set_statusbar_message(N_("Creating fingerprint for file '%s'..."), filename)
            fingerprint, length = self._ofa.create_fingerprint(filename)
            if not fingerprint:
                self.set_statusbar_message(N_("Unable to create fingerprint for file '%s'"), filename)
                self.thread_assist.proxy_to_main(file.set_state, File.NORMAL, update=True)
                continue
            self.log.debug("File '%s' analyzed.\nFingerprint: %s", filename, fingerprint)

            # Lookup the fingerprint on MusicDNS
            self.set_statusbar_message(N_("Looking up the fingerprint for file '%s'..."), filename)
            q = musicdns_ws.Query(ws)
            try:
                track = q.getTrack(musicdns_ws.TrackFilter(
                    clientId=MUSICDNS_KEY,
                    clientVersion="picard-%s" % picard.version_string,
                    fingerprint=fingerprint,
                    artist=file.metadata["artist"],
                    title=file.metadata["title"],
                    album=file.metadata["album"],
                    trackNum=file.metadata["tracknumber"],
                    genre=file.metadata["genre"],
                    year=file.metadata["date"][:4],
                    bitrate=str(file.metadata.get("~#bitrate", 0)),
                    format=file.metadata["~format"],
                    length=str(file.metadata.get("~#length", length)),
                    metadata="0", lookupType="1", encoding=""))
            except WebServiceError, e:
                self.set_statusbar_message(N_("Unable to get PUID for file '%s': %s"), filename, e)
                self.thread_assist.proxy_to_main(file.set_state, File.NORMAL, update=True)
                continue
            if not track:
                self.set_statusbar_message(N_("No PUID found for file '%s'"), filename)
                self.thread_assist.proxy_to_main(file.set_state, File.NORMAL, update=True)
                continue

            # Lookup the PUID on MusicBrainz
            if track.artist: artist = track.artist.name or ''
            else: artist = ''
            title = track.title or ''
            puid = track.puids[0]
            self.puidmanager.add(puid, None)
            self.log.debug("Fingerprint looked up.\nPUID: %s\nTitle: %s\nArtist: %s", puid, title, artist)
            if not file.metadata["artist"]:
                file.metadata["artist"] = artist
            if not file.metadata["title"]:
                file.metadata["title"] = title
            file.metadata["musicip_puid"] = puid
            self.set_statusbar_message(N_("Looking up the PUID '%s'..."), puid)
            q = Query(self.get_web_service())
            results = q.getTracks(TrackFilter(puid=puid))
            if not results:
                self.set_statusbar_message(N_("No PUID matches found for file '%s'"), filename)
                self.thread_assist.proxy_to_main(file.set_state, File.NORMAL, update=True)
                continue

            # Find the best match and move the file
            matches = []
            for result in results:
                metadata = Metadata()
                metadata.from_track(result.track)
                sim = file.metadata.compare(metadata)
                matches.append((sim, metadata))
            matches.sort(reverse=True)
            self.log.debug('Matches %r', matches)
            if matches[0][0] >= self.config.setting['puid_lookup_threshold']:
                self.set_statusbar_message(N_("File '%s' identified!"), filename)
                self.thread_assist.proxy_to_main(self.__puid_lookup_finished, file, puid, matches[0])
            else:
                self.set_statusbar_message(N_("PUID conflict for file '%s'"), filename)
                self.thread_assist.proxy_to_main(file.set_state, File.NORMAL, update=True)

    def cluster(self, objs):
        """Group files with similar metadata to 'clusters'."""
        self.log.debug("Clustering %r", objs)
        if len(objs) <= 1:
            objs = [self.unmatched_files]
        files = self.get_files_from_objects(objs)
        for name, artist, files in Cluster.cluster(files, 1.0):
            cluster = Cluster(name, artist)
            self.clusters.append(cluster)
            self.emit(QtCore.SIGNAL("cluster_added"), cluster)
            for file in files:
                file.move(cluster)

    def remove_cluster(self, cluster):
        """Remove the specified cluster."""
        self.log.debug("Removing %r", cluster)
        for file in cluster.files:
            del self.files[self.files.index(file)]
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

def main(localedir=None):
    app = Tagger(localedir)
    sys.exit(app.run())
