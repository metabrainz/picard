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
import urllib2
import imp

import picard.resources
import picard.plugins
import picard.tagz

from picard import musicdns
from picard.album import Album
from picard.api import IFileOpener, ITaggerScript
from picard.browser.browser import BrowserIntegration
from picard.browser.filelookup import FileLookup
from picard.cluster import Cluster, FileClusterEngine
from picard.component import ComponentManager, ExtensionPoint, Component
from picard.config import Config
from picard.file import File
from picard.metadata import Metadata
from picard.track import Track
from picard.ui.mainwindow import MainWindow
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
from picard.util.thread import ThreadAssist

from musicbrainz2.utils import extractUuid
from musicbrainz2.webservice import Query, TrackFilter, ReleaseFilter

# Install gettext "noop" function.
import __builtin__
__builtin__.__dict__['N_'] = lambda a: a

class ClusterList(list):

    def __hash__(self):
        return id(self)


class Tagger(QtGui.QApplication, ComponentManager, Component):

    file_openers = ExtensionPoint(IFileOpener)
    scripting = ExtensionPoint(ITaggerScript)

    def __init__(self, localeDir):
        QtGui.QApplication.__init__(self, sys.argv)
        ComponentManager.__init__(self)

        self.config = Config()

        self.setup_logging()

        QtCore.QObject.tagger = self
        QtCore.QObject.config = self.config
        QtCore.QObject.log = self.log

        musicdns.init(self)
        self.thread_assist = ThreadAssist(self)

        self.setup_gettext(localeDir)

        if sys.platform == "win32":
            self.user_dir = "~\\Local Settings\\Application Data\\MusicBrainz Picard"
        else:
            self.user_dir = "~/.picard"
        self.user_dir = os.path.expanduser(self.user_dir)

        self.plugins_dir = os.path.join(self.user_dir, "plugins")
        self.cache_dir = os.path.join(self.user_dir, "cache")

        self.__load_plugins(os.path.join(os.path.dirname(sys.argv[0]), "plugins"))
        self.__load_plugins(self.plugins_dir)

        self._move_to_album = []

        self.browser_integration = BrowserIntegration()

        self.files = []
        self.clusters = ClusterList()
        self.albums = []

        self.unmatched_files = Cluster(_(u"Unmatched Files"))

        self.window = MainWindow()
        self.connect(self.window, QtCore.SIGNAL("file_updated(int)"), QtCore.SIGNAL("file_updated(int)"))

        self.browser_integration.start()

    def setup_logging(self):
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter(u"%(thread)s %(asctime)s %(message)s",
                                               u"%H:%M:%S"))
        self.log = logging.getLogger()
#        self.log = logging.getLogger("picard")
        self.log.addHandler(console)
        self.log.setLevel(logging.DEBUG)

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
        self.browser_integration.stop()

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
            self.log.debug(u"Loading gettext translation, localeDir=%r", localeDir)
            self.translation = gettext.translation("picard", localeDir)
            self.translation.install(True)
        except IOError, e:
            __builtin__.__dict__['_'] = lambda a: a
            self.log.warning(e)

    def __set_status_bar_message(self, message, args=()):
        self.window.set_status_bar_message(_(message) % args)

    def __load_plugins(self, plugin_dir):
        """Load plugins from the specified directory."""
        if not os.path.isdir(plugin_dir):
            self.log.info("Plugin directory '%s' doesn't exist", plugin_dir)
            return

        plugin_names = set()
        suffixes = [s[0] for s in imp.get_suffixes()]
        package_entries = ["__init__.py", "__init__.pyc", "__init__.pyo"]
        for name in os.listdir(plugin_dir):
            path = os.path.join(plugin_dir, name)
            if os.path.isdir(path):
                for entry in package_entries:
                    if os.path.isfile(os.path.join(path, entry)):
                        break
                else:
                    continue
            else:
                name, suffix = os.path.splitext(name)
                if suffix not in suffixes:
                    continue
            if hasattr(picard.plugins, name):
                self.log.info("Plugin %s already loaded!", name)
            else:
                plugin_names.add(name)

        for name in plugin_names:
            self.log.debug("Loading plugin %s", name)
            info = imp.find_module(name, [plugin_dir])
            try:
                plugin = imp.load_module('picard.plugins.' + name, *info)
                setattr(picard.plugins, name, plugin)
            finally:
                if info[0] is not None:
                    info[0].close()

    def get_supported_formats(self):
        """Returns list of supported formats.

        Format:
            [('.mp3', 'MPEG Layer-3 File'), ('.cue', 'Cuesheet'), ...]
        """
        formats = []
        for opener in self.file_openers:
            formats.extend(opener.get_supported_formats())
        return formats

    def add_files(self, files):
        """Load and add files."""
        files = map(os.path.normpath, files)
        self.log.debug(u"Adding files %r", files)
        filenames = []
        for filename in files:
            not_found = True
            for file in self.files:
                if file.filename == filename:
                    not_found = False
                    break
            if not_found:
                for opener in self.file_openers:
                    if opener.can_open_file(filename):
                        filenames.append((filename, opener.open_file))
        if filenames:
            self.thread_assist.spawn(self.__add_files_thread, (filenames,))

    def __add_files_thread(self, filenames):
        """Load the files."""
        files = []
        for filename, opener in filenames:
            try:
                files.extend(opener(filename))
            except:
                import traceback; traceback.print_exc()
        while files:
            self.thread_assist.proxy_to_main(self.__add_files_finished,
                                             (files[:100],))
            files = files[100:]

    def __add_files_finished(self, files):
        """Add loaded files to the tagger."""
        for file in files:
            self.files.append(file)
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

    def add_directory(self, directory):
        """Add all files from the directory ``directory`` to the tagger."""
        directory = os.path.normpath(directory)
        self.log.debug(u"Adding directory %r", directory)
        self.thread_assist.spawn(self.__read_directory_thread, (directory,))

    def __read_directory_thread(self, directory):
        directories = [encode_filename(directory)]
        while directories:
            files = []
            directory = directories.pop()
            self.log.debug(u"Reading directory %r", directory)
            self.thread_assist.proxy_to_main(self.__set_status_bar_message,
                                             (N_("Reading directory %s ..."),
                                              directory))
            for name in os.listdir(directory):
                name = os.path.join(directory, name)
                if os.path.isdir(name):
                    directories.append(name)
                else:
                    files.append(decode_filename(name))
            while files:
                self.thread_assist.proxy_to_main(self.add_files,
                                                 (files[:100],))
                files = files[100:]
        self.thread_assist.proxy_to_main(self.__set_status_bar_message,
                                         (N_("Done"),))

    def get_file_by_id(self, id):
        """Get file by a file ID."""
        for file in self.files:
            if file.id == id:
                return file
        return None

    def remove_files(self, files):
        """Remove files from the tagger."""
        for file in files:
            file.remove_from_cluster()
            file.remove_from_track()

        for file in files:
            index = self.files.index(file)
            del self.files[index]

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
        files = []
        for file in self.get_files_from_objects(objects):
            file.state = File.TO_BE_SAVED
            files.append(file)
        self.set_wait_cursor()
        self.thread_assist.spawn(self.__save_thread, (files,))

    def __save_thread(self, files):
        """Save the files."""
        saved = []
        unsaved = []
        todo = len(files)
        for file in files:
            self.log.debug(u"Saving file %s", file)
            self.thread_assist.proxy_to_main(self.__set_status_bar_message,
                                             (N_("Saving file %s ..."),
                                              file.filename))
            failed = False
            try:
                file.save()
            except:
                import traceback; traceback.print_exc()
                failed = True

            if not failed:
                file.lock_for_read()
                try:
                    filename = file.filename
                    metadata = Metadata()
                    metadata.copy(file.metadata)
                finally:
                    file.unlock()

                if self.config.setting["move_files"]:
                    new_dirname = os.path.dirname(filename)
                else:
                    new_dirname = os.path.dirname(filename)

                if self.config.setting["rename_files"]:
                    format = self.config.setting["file_naming_format"]
                    # Replace incompatible characters
                    for name in metadata.keys():
                        value = metadata[name]
                        if isinstance(value, unicode):
                            value = sanitize_filename(value)
                            if sys.platform == "win32" or \
                               self.config.setting["windows_compatible_filenames"]:
                                value = replace_win32_incompat(value)
                            if self.config.setting["ascii_filenames"]:
                                value = replace_non_ascii(value)
                            metadata[name] = value
                    # Make the new filename
                    new_filename = self.tagger.evaluate_script(format, metadata)
                    if not self.config.setting["move_files"]:
                        new_filename = os.path.basename(new_filename)
                    new_filename = os.path.join(new_dirname,
                                                make_short_filename(
                                                    new_dirname,
                                                    new_filename)) + \
                                   os.path.splitext(filename)[1]
                else:
                    new_filename = os.path.join(new_dirname,
                                                os.path.basename(filename))

                if filename != new_filename:
                    os.rename(filename, new_filename)
                    file.lock_for_write()
                    try:
                        file.filename = new_filename
                    finally:
                        file.unlock()

            todo -= 1
            self.thread_assist.proxy_to_main(self.__save_finished,
                                             (file, failed, todo))
        self.thread_assist.proxy_to_main(self.__set_status_bar_message,
                                         (N_("Done"),))

    def __save_finished(self, file, failed, todo):
        """Finalize file saving and notify views."""
        if not failed:
            file.state = File.SAVED
            file.orig_metadata.copy(file.metadata)
            file.metadata.changed = False
            file.update()
        if todo == 0:
            self.restore_cursor()

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

    def load_album(self, id):
        """Load an album specified by MusicBrainz ID."""
        album = self.get_album_by_id(id)
        if album:
            return album
        album = Album(id, _("[loading album information]"), None)
        self.albums.append(album)
        self.connect(album, QtCore.SIGNAL("track_updated"), self, QtCore.SIGNAL("track_updated"))
        self.emit(QtCore.SIGNAL("album_added"), album)
        self.thread_assist.spawn(self.__load_album_thread, (album,))
        return album

    def __load_album_thread(self, album):
        self.log.debug(u"Loading album %s", album)
        self.thread_assist.proxy_to_main(self.__set_status_bar_message,
                                         (N_("Loading album %s ..."),
                                          album.id))
        album.load()
        self.thread_assist.proxy_to_main(self.__set_status_bar_message,
                                         (N_("Done"),))
        self.thread_assist.proxy_to_main(self.__load_album_finished, (album,))

    def __load_album_finished(self, album):
        self.emit(QtCore.SIGNAL("album_updated"), album)
        for file, target in self._move_to_album:
            if target == album:
                self.match_files_to_album([file], album)

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

    def autoTag(self, files):
        self.set_wait_cursor()
        try:
            # TODO: move to a separate thread
            import math

            # If the user selected no or only one file, use all unmatched files
            if len(files) < 1:
                self.files.lock_for_read()
                try:
                    files = self.files.values()
                finally:
                    self.files.unlock()

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
        finally:
            self.restore_cursor()

    def evaluate_script(self, script, context={}):
        """Evaluate the script and return the result."""
        if not self.scripting:
            raise Exception, "No tagger script interpreter."

        return self.scripting[0].evaluate_script(script, context)

    def get_web_service(self, **kwargs):
        if "host" not in kwargs:
            kwargs["host"] = self.config.setting["server_host"]
        if "port" not in kwargs:
            kwargs["port"] = self.config.setting["server_port"]
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
        return CachedWebService(cache_dir=self.cache_dir,
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
            self.thread_assist.proxy_to_main(self.__lookup_cd_error, (e,))
            return

        try:
            q = Query(ws=self.get_web_service())
            releases = q.getReleases(filter=ReleaseFilter(discId=disc.getId()))
        except Exception, e:
            self.thread_assist.proxy_to_main(self.__lookup_cd_error, (e,))
            return

        url = getSubmissionUrl(disc, self.config.setting["server_host"],
                               self.config.setting["server_port"])
        self.thread_assist.proxy_to_main(self.__lookup_cd_finished,
                                         (releases, url))

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
        self.thread_assist.spawn(self.__analyze_thread, (files,))

    def __analyze_thread(self, files):
        from picard.musicdns.webservice import TrackFilter, Query
        ws = self.get_web_service(host="ofa.musicdns.org", pathPrefix="/ofa")
        for file in files:
            file.lock_for_read()
            try:
                filename = file.filename
                artist = file.metadata["artist"]
                title = file.metadata["title"]
                album = file.metadata["album"]
                trackNum = file.metadata["tracknumber"]
                genre = file.metadata["genre"]
                year = file.metadata["date"][:4]
                format = file.metadata["~format"]
                bitrate = str(file.metadata.get("~#bitrate", 0))
                length = file.metadata.get("~#length", 0)
            finally:
                file.unlock()
            self.log.debug("Analyzing file %s", filename)
            result = musicdns.create_fingerprint(filename)
            if result:
                fingerprint, duration = result
                self.log.debug("File %s analyzed.\nFingerprint: %s\n"
                               "Duration: %s", filename, fingerprint, duration)
                if not length:
                    length = duration
                q = Query(ws)
                track = q.getTrack(TrackFilter(
                    clientId="80eaa76658f99dbac1c58cc06aa44779",
                    clientVersion="picard-0.9", fingerprint=fingerprint,
                    artist=artist, title=title, album=album, trackNum=trackNum,
                    genre=genre, year=year, bitrate=bitrate, format=format,
                    length=str(length), metadata="1", lookupType="1",
                    encoding=""))
                if track:
                    artist = ""
                    if track.artist:
                        artist = track.artist.name or ""
                    self.log.debug("Fingerprint looked up.\nPUID: %s\nTitle: %s\n"
                                   "Artist: %s", track.puids, track.title or "",
                                    artist)
                    if track.puids:
                        file.lock_for_write()
                        try:
                            file.metadata["musicip_puid"] = track.puids[0]
                        finally:
                            file.unlock()
                else:
                    self.log.debug("Fingerprint looked up, no PUID found.")

    def cluster(self, objs):
        self.log.debug("Clustering %r", objs)
        if len(objs) <= 1:
            objs = [self.unmatched_files]
        files = self.get_files_from_objects(objs)
        engine = FileClusterEngine()
        for name, artist, files in engine.cluster(files, 1.0):
            cluster = Cluster(name, artist)
            self.clusters.append(cluster)
            for file in files:
                file.move_to_cluster(cluster)
            self.emit(QtCore.SIGNAL("cluster_added"), cluster)

    def set_wait_cursor(self):
        """Sets the waiting cursor."""
        QtGui.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor))

    def restore_cursor(self):
        """Restores the cursor set by ``set_wait_cursor``."""
        QtGui.QApplication.restoreOverrideCursor()

def main(localedir=None):
    tagger = Tagger(localedir)
    sys.exit(tagger.run())

