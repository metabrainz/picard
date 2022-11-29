# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2014, 2017 Lukáš Lalinský
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 amckinle
# Copyright (C) 2008-2010, 2014-2015, 2018-2022 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2010 Andrew Barnert
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2011-2014, 2017-2019 Wieland Hoffmann
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013 Ionuț Ciocîrlan
# Copyright (C) 2013 brainz34
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2013-2015, 2017-2022 Laurent Monin
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017-2018 Vishal Choudhary
# Copyright (C) 2018, 2022 Bob Swift
# Copyright (C) 2018 virusMac
# Copyright (C) 2019 Joel Lintunen
# Copyright (C) 2020 Julius Michaelis
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (c) 2022 skelly37
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
from functools import partial
from hashlib import md5
import logging
import os
import platform
import re
import shlex
import shutil
import signal
import sys
from textwrap import fill
from urllib.parse import urlparse
from uuid import uuid4

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
from picard.disc import (
    Disc,
    dbpoweramplog,
    eaclog,
    whipperlog,
)
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
    encode_filename,
    is_hidden,
    iter_files_from_objects,
    mbid_validate,
    normpath,
    periodictouch,
    pipe,
    process_events_iter,
    system_supports_long_paths,
    thread,
    versions,
    webbrowser2,
)
from picard.util.cdrom import (
    DISCID_NOT_LOADED_MESSAGE,
    discid as _discid,
    get_cdrom_drives,
)
from picard.util.checkupdate import UpdateCheckManager
from picard.webservice import WebService
from picard.webservice.api_helpers import (
    AcoustIdAPIHelper,
    MBAPIHelper,
)

import picard.resources  # noqa: F401 # pylint: disable=unused-import

from picard.ui import theme
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


def plugin_dirs():
    if IS_FROZEN:
        toppath = sys.argv[0]
    else:
        toppath = os.path.abspath(__file__)

    topdir = os.path.dirname(toppath)
    plugin_dir = os.path.join(topdir, "plugins")
    yield plugin_dir

    if not os.path.exists(USER_PLUGIN_DIR):
        os.makedirs(USER_PLUGIN_DIR)
    yield USER_PLUGIN_DIR


class ParseItemsToLoad:

    WINDOWS_DRIVE_TEST = re.compile(r"^[a-z]\:", re.IGNORECASE)

    def __init__(self, items):
        self.commands = []
        self.files = set()
        self.mbids = set()
        self.urls = set()

        for item in items:
            parsed = urlparse(item)
            if not parsed.scheme:
                self.files.add(item)
            elif parsed.scheme == "command":
                for x in item[10:].split(';'):
                    self.commands.append(x.strip())
            elif parsed.scheme == "file":
                # remove file:// prefix safely
                self.files.add(item[7:])
            elif parsed.scheme == "mbid":
                self.mbids.add(parsed.netloc + parsed.path)
            elif parsed.scheme in {"http", "https"}:
                # .path returns / before actual link
                self.urls.add(parsed.path[1:])
            elif IS_WIN and self.WINDOWS_DRIVE_TEST.match(item):
                # Treat all single-character schemes as part of the file spec to allow
                # specifying a drive identifier on Windows systems.
                self.files.add(item)

    # needed to indicate whether Picard should be brought to the front
    def non_executable_items(self):
        return bool(self.files or self.mbids or self.urls)

    def __bool__(self):
        return bool(self.commands or self.files or self.mbids or self.urls)

    def __str__(self):
        return f"files: {repr(self.files)}  mbids: f{repr(self.mbids)}  urls: {repr(self.urls)}  commands: {repr(self.commands)}"


class RemoteCommand:
    def __init__(self, method_name, help_text=None, help_args=None):
        self.method_name = method_name
        self.help_text = help_text or ""
        self.help_args = help_args or ""


REMOTE_COMMANDS = {
    "CLEAR_LOGS": RemoteCommand(
        "handle_command_clear_logs",
        help_text="Clear the Picard logs",
    ),
    "CLUSTER": RemoteCommand(
        "handle_command_cluster",
        help_text="Cluster all files in the cluster pane.",
    ),
    "FINGERPRINT": RemoteCommand(
        "handle_command_fingerprint",
        help_text="Calculate acoustic fingerprints for all (matched) files in the album pane.",
    ),
    "FROM_FILE": RemoteCommand(
        "handle_command_from_file",
        help_text="Load command pipeline from a file.",
        help_args="[Absolute path to a file containing command pipeline]",
    ),
    "LOAD": RemoteCommand(
        "handle_command_load",
        help_text="Load 1 or more files/MBIDs/URLs to Picard.",
        help_args="[supported MBID/URL or absolute path to a file]",
    ),
    "LOOKUP": RemoteCommand(
        "handle_command_lookup",
        help_text="Lookup files in the clustering pane. Defaults to all files.",
        help_args="[clustered|unclustered|all]"
    ),
    "LOOKUP_CD": RemoteCommand(
        "handle_command_lookup_cd",
        help_text="Read CD from the selected drive and lookup on MusicBrainz. "
        "Without argument, it defaults to the first (alphabetically) available disc drive",
        help_args="[device/log file]",
    ),
    "QUIT": RemoteCommand(
        "handle_command_quit",
        help_text="Exit the running instance of Picard.",
    ),
    "REMOVE": RemoteCommand(
        "handle_command_remove",
        help_text="Remove the file from Picard. Do nothing if no arguments provided.",
        help_args="[absolute path to 1 or more files]",
    ),
    "REMOVE_ALL": RemoteCommand(
        "handle_command_remove_all",
        help_text="Remove all files from Picard.",
    ),
    "REMOVE_EMPTY": RemoteCommand(
        "handle_command_remove_empty",
        help_text="Remove all empty clusters and albums.",
    ),
    "REMOVE_SAVED": RemoteCommand(
        "handle_command_remove_saved",
        help_text="Remove all saved releases from the album pane.",
    ),
    "REMOVE_UNCLUSTERED": RemoteCommand(
        "handle_command_remove_unclustered",
        help_text="Remove all unclustered files from the cluster pane.",
    ),
    "SAVE_MATCHED": RemoteCommand(
        "handle_command_save_matched",
        help_text="Save all matched releases from the album pane."
    ),
    "SAVE_MODIFIED": RemoteCommand(
        "handle_command_save_modified",
        help_text="Save all modified files from the album pane.",
    ),
    "SCAN": RemoteCommand(
        "handle_command_scan",
        help_text="Scan all files in the cluster pane.",
    ),
    "SHOW": RemoteCommand(
        "handle_command_show",
        help_text="Make the running instance the currently active window.",
    ),
    "SUBMIT_FINGERPRINTS": RemoteCommand(
        "handle_command_submit_fingerprints",
        help_text="Submit outstanding acoustic fingerprints for all (matched) files in the album pane.",
    ),
    "WRITE_LOGS": RemoteCommand(
        "handle_command_write_logs",
        help_text="Write Picard logs to a given path.",
        help_args="[absolute path to 1 file]",
    ),
}


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

    def __init__(self, picard_args, localedir, autoupdate, pipe_handler=None):

        super().__init__(sys.argv)
        self.__class__.__instance = self
        setup_config(self, picard_args.config_file)
        config = get_config()
        theme.setup(self)

        self._to_load = picard_args.processable

        self.autoupdate_enabled = autoupdate
        self._no_restore = picard_args.no_restore
        self._no_plugins = picard_args.no_plugins

        self.set_log_level(config.setting['log_verbosity'])

        if picard_args.debug or "PICARD_DEBUG" in os.environ:
            self.set_log_level(logging.DEBUG)

        # FIXME: Figure out what's wrong with QThreadPool.globalInstance().
        # It's a valid reference, but its start() method doesn't work.
        self.thread_pool = QtCore.QThreadPool(self)

        self.pipe_handler = pipe_handler

        if self.pipe_handler:
            self.pipe_handler.pipe_running = True
            thread.run_task(self.pipe_server, self._pipe_server_finished)

        self._init_remote_commands()

        # Provide a separate thread pool for operations that should not be
        # delayed by longer background processing tasks, e.g. because the user
        # expects instant feedback instead of waiting for a long list of
        # operations to finish.
        self.priority_thread_pool = QtCore.QThreadPool(self)
        self.priority_thread_pool.setMaxThreadCount(1)

        # Use a separate thread pool for file saving, with a thread count of 1,
        # to avoid race conditions in File._save_and_rename.
        self.save_thread_pool = QtCore.QThreadPool(self)
        self.save_thread_pool.setMaxThreadCount(1)

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
                                                         QtCore.QSocketNotifier.Type.Read, self)
            self.signalnotifier.activated.connect(self.sighandler)

            signal.signal(signal.SIGHUP, self.signal)
            signal.signal(signal.SIGINT, self.signal)
            signal.signal(signal.SIGTERM, self.signal)

        # Setup logging
        log.debug("Starting Picard from %r", os.path.abspath(__file__))
        log.debug("Platform: %s %s %s", platform.platform(),
                  platform.python_implementation(), platform.python_version())
        log.debug("Versions: %s", versions.as_string())
        log.debug("Configuration file path: %r", config.fileName())

        log.debug("User directory: %r", os.path.abspath(USER_DIR))
        log.debug("System long path support: %r", system_supports_long_paths())

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

        self.enable_menu_icons(config.setting['show_menu_icons'])

        # Load plugins
        self.pluginmanager = PluginManager()
        if not self._no_plugins:
            for plugin_dir in plugin_dirs():
                self.pluginmanager.load_plugins_from_directory(plugin_dir)

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

        # On macOS temporary files get deleted after 3 days not being accessed.
        # Touch these files regularly to keep them alive if Picard
        # is left running for a long time.
        if IS_MACOS:
            periodictouch.enable_timer()

        # Load release version information
        if self.autoupdate_enabled:
            self.updatecheckmanager = UpdateCheckManager(parent=self.window)

    @property
    def is_wayland(self):
        return self.platformName() == 'wayland'

    def pipe_server(self):
        IGNORED = {pipe.Pipe.MESSAGE_TO_IGNORE, pipe.Pipe.NO_RESPONSE_MESSAGE}
        while self.pipe_handler.pipe_running:
            messages = [x for x in self.pipe_handler.read_from_pipe() if x not in IGNORED]
            if messages:
                log.debug("pipe messages: %r", messages)
                thread.to_main(self.load_to_picard, messages)

    def _pipe_server_finished(self, result=None, error=None):
        if error:
            log.error('pipe server failed: %r', error)
        else:
            log.debug('pipe server stopped')

    def load_to_picard(self, items):
        parsed_items = ParseItemsToLoad(items)
        log.debug(str(parsed_items))

        if parsed_items.files:
            self.add_paths(parsed_items.files)

        if parsed_items.urls or parsed_items.mbids:
            file_lookup = self.get_file_lookup()
            for item in parsed_items.mbids | parsed_items.urls:
                thread.to_main(file_lookup.mbid_lookup, item, None, None, False)

        for command in parsed_items.commands:
            self.handle_command(command)

        if parsed_items.non_executable_items():
            self.bring_tagger_front()

    def iter_album_files(self):
        for album in self.albums.values():
            yield from album.iterfiles()

    def iter_all_files(self):
        yield from self.unclustered_files.files
        yield from self.iter_album_files()
        yield from self.clusters.iterfiles()

    def _init_remote_commands(self):
        self.commands = {name: getattr(self, remcmd.method_name) for name, remcmd in REMOTE_COMMANDS.items()}

    def handle_command(self, command):
        cmd, *args = command.split(' ', 1)
        argstring = next(iter(args), "")
        cmd = cmd.upper()
        log.debug("Executing command: %r", cmd)
        try:
            thread.to_main(self.commands[cmd], argstring.strip())
        except KeyError:
            log.error("Unknown command: %r", cmd)

    def handle_command_clear_logs(self, argstring):
        self.window.log_dialog.clear()
        self.window.history_dialog.clear()

    def handle_command_cluster(self, argstring):
        self.cluster(self.unclustered_files.files)

    def handle_command_fingerprint(self, argstring):
        for album_name in self.albums:
            self.analyze(self.albums[album_name].iterfiles())

    @staticmethod
    def _read_lines_from_file(filepath):
        try:
            yield from (line.strip() for line in open(filepath).readlines())
        except Exception as e:
            log.error("Error reading command file '%s': %s" % (filepath, e))

    @staticmethod
    def _parse_commands_from_lines(lines):
        for line in lines:
            if not line or line.startswith('#'):
                continue
            elements = shlex.split(line)
            if not elements:
                continue
            command_args = elements[1:] or ['']
            for element in command_args:
                yield f"command://{elements[0]} {element}"

    def handle_command_from_file(self, argstring):
        for command in self._parse_commands_from_lines(self._read_lines_from_file(argstring)):
            self.load_to_picard((command,))

    def handle_command_load(self, argstring):
        if argstring.startswith("command://"):
            log.error("Cannot LOAD a command: %s", argstring)
            return

        self.load_to_picard((argstring,))

    def handle_command_lookup(self, argstring):
        if argstring:
            argstring = argstring.upper()
        if not argstring or argstring == 'ALL':
            self.autotag(self.clusters)
            self.autotag(self.unclustered_files.files)
        elif argstring == 'CLUSTERED':
            self.autotag(self.clusters)
        elif argstring == 'UNCLUSTERED':
            self.autotag(self.unclustered_files.files)
        else:
            log.error("Invalid LOOKUP command argument: '%s'", argstring)

    def handle_command_lookup_cd(self, argstring):
        if not _discid:
            log.error(DISCID_NOT_LOADED_MESSAGE)
            return
        disc = Disc()
        devices = get_cdrom_drives()

        if not argstring:
            if devices:
                device = devices[0]
            else:
                device = None
        elif argstring in devices:
            device = argstring
        else:
            thread.run_task(
                partial(self._parse_disc_ripping_log, disc, argstring),
                partial(self._lookup_disc, disc),
                traceback=self._debug)
            return

        thread.run_task(
            partial(disc.read, encode_filename(device)),
            partial(self._lookup_disc, disc),
            traceback=self._debug)

    def handle_command_quit(self, argstring):
        self.exit()
        self.quit()

    def handle_command_remove(self, argstring):
        for file in self.iter_all_files():
            if file.filename == argstring:
                self.remove([file])
                return

    def handle_command_remove_all(self, argstring):
        for file in self.iter_all_files():
            self.remove([file])

    def handle_command_remove_empty(self, argstring):
        for album in self.albums:
            if not any(album.iterfiles()):
                self.remove_album(album)

        for cluster in self.clusters:
            if not any(cluster.iterfiles()):
                self.remove_cluster(cluster)

    def handle_command_remove_saved(self, argstring):
        for track in self.iter_album_files():
            if track.state == File.NORMAL:
                self.remove([track])

    def handle_command_remove_unclustered(self, argstring):
        self.remove(self.unclustered_files.files)

    def handle_command_save_matched(self, argstring):
        for album in self.albums.values():
            for track in album.iter_correctly_matched_tracks():
                track.files[0].save()

    def handle_command_save_modified(self, argstring):
        for track in self.iter_album_files():
            if track.state == File.CHANGED:
                track.save()

    def handle_command_scan(self, argstring):
        self.analyze(self.unclustered_files.files)

    def handle_command_show(self, argstring):
        self.bring_tagger_front()

    def handle_command_submit_fingerprints(self, argstring):
        self.acoustidmanager.submit()

    def handle_command_write_logs(self, argstring):
        try:
            with open(argstring, 'w') as f:
                for x in self.window.log_dialog.log_tail.contents():
                    f.write(f"{x.message}\n")
        except Exception as e:
            log.error("Error writing logs to a file: %s", e)

    def enable_menu_icons(self, enabled):
        self.setAttribute(QtCore.Qt.ApplicationAttribute.AA_DontShowIconsInMenus, not enabled)

    def register_cleanup(self, func):
        self.exit_cleanup.append(func)

    def run_cleanup(self):
        for f in self.exit_cleanup:
            f()

    def set_log_level(self, level):
        self._debug = level == logging.DEBUG
        log.set_level(level)

    def _mb_login_dialog(self, parent):
        if not parent:
            parent = self.window
        dialog = QtWidgets.QInputDialog(parent)
        dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        dialog.setWindowTitle(_("MusicBrainz Account"))
        dialog.setLabelText(_("Authorization code:"))
        status = dialog.exec_()
        if status == QtWidgets.QDialog.DialogCode.Accepted:
            return dialog.textValue()
        else:
            return None

    def mb_login(self, callback, parent=None):
        scopes = "profile tag rating collection submit_isrc submit_barcode"
        authorization_url = self.webservice.oauth_manager.get_authorization_url(scopes)
        webbrowser2.open(authorization_url)
        authorization_code = self._mb_login_dialog(parent)
        if authorization_code is not None:
            self.webservice.oauth_manager.exchange_authorization_code(
                authorization_code, scopes,
                partial(self.on_mb_authorization_finished, callback))
        else:
            callback(False, None)

    def on_mb_authorization_finished(self, callback, successful=False, error_msg=None):
        if successful:
            self.webservice.oauth_manager.fetch_username(
                partial(self.on_mb_login_finished, callback))
        else:
            callback(False, error_msg)

    @classmethod
    def on_mb_login_finished(self, callback, successful, error_msg):
        if successful:
            load_user_collections()
        callback(successful, error_msg)

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
        if self.pipe_handler:
            self.pipe_handler.pipe_running = False
        self.thread_pool.waitForDone()
        self.save_thread_pool.waitForDone()
        self.priority_thread_pool.waitForDone()
        self.browser_integration.stop()
        self.webservice.stop()
        self.run_cleanup()
        QtCore.QCoreApplication.processEvents()

    def _run_init(self):
        if self._to_load:
            self.load_to_picard(self._to_load)
        del self._to_load

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
        elif event.type() == QtCore.QEvent.Type.FileOpen:
            file = event.file()
            self.add_paths([file])
            if IS_HAIKU:
                self.bring_tagger_front()
            # We should just return True here, except that seems to
            # cause the event's sender to get a -9874 error, so
            # apparently there's some magic inside QFileOpenEvent...
            return 1
        return super().event(event)

    def _file_loaded(self, file, target=None, remove_file=False, unmatched_files=None):
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
            target = self.move_file(file, target)
            if target and target != self.unclustered_files:
                file_moved = True

        if not file_moved and unmatched_files is not None:
            unmatched_files.append(file)

        # fallback on analyze if nothing else worked
        if not file_moved and config.setting['analyze_new_files'] and file.can_analyze():
            log.debug("Trying to analyze %r ...", file)
            self.analyze([file])

        # Auto cluster newly added files if they are not explicitly moved elsewhere
        if self._pending_files_count == 0 and unmatched_files and config.setting["cluster_new_files"]:
            self.cluster(unmatched_files)

    def move_file(self, file, target):
        """Moves a file to target, if possible

        Returns the actual target the files has been moved to or None
        """
        if isinstance(target, Album):
            self.move_files_to_album([file], album=target)
        else:
            if isinstance(target, File) and target.parent:
                target = target.parent
            if not file.move(target):
                # Ensure a file always has a parent so it shows up in UI
                if not file.parent:
                    target = self.unclustered_files
                    file.move(target)
                # Unsupported target, do not move the file
                else:
                    target = None
        return target

    def move_files(self, files, target, move_to_multi_tracks=True):
        if target is None:
            log.debug("Aborting move since target is invalid")
            return
        self.window.set_sorting(False)
        with self.window.metadata_box.ignore_updates:
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
                log.debug("File ignored (hidden): %r", filename)
                continue
            # Ignore .smbdelete* files which Applie iOS SMB creates by renaming a file when it cannot delete it
            if os.path.basename(filename).startswith(".smbdelete"):
                log.debug("File ignored (.smbdelete): %r", filename)
                continue
            if ignoreregex is not None and ignoreregex.search(filename):
                log.info("File ignored (matching %r): %r", pattern, filename)
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
            unmatched_files = []
            for i, file in enumerate(new_files):
                file.load(partial(self._file_loaded, target=target, unmatched_files=unmatched_files))
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
            current_path = normpath(local_paths.pop(0))
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
            lookup.search_entity(search['entity'], text, adv,
                                 mbid_matched_callback=mbid_matched_callback,
                                 force_browser=force_browser)

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
            data = action.data()
            if data == 'logfile:eac':
                return self.lookup_discid_from_logfile()
            else:
                device = data
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

    def lookup_discid_from_logfile(self):
        file_chooser = QtWidgets.QFileDialog(self.window)
        file_chooser.setNameFilters([
            _("All supported log files") + " (*.log, *.txt)",
            _("EAC / XLD / Whipper / fre:ac log files") + " (*.log)",
            _("dBpoweramp log files") + " (*.txt)",
            _("All files") + " (*)",
        ])
        if file_chooser.exec_():
            files = file_chooser.selectedFiles()
            disc = Disc()
            self.set_wait_cursor()
            thread.run_task(
                partial(self._parse_disc_ripping_log, disc, files[0]),
                partial(self._lookup_disc, disc),
                traceback=self._debug)

    def _parse_disc_ripping_log(self, disc, path):
        log_readers = (
            eaclog.toc_from_file,
            whipperlog.toc_from_file,
            dbpoweramplog.toc_from_file,
        )
        for reader in log_readers:
            module_name = reader.__module__
            try:
                log.debug('Trying to parse "%s" with %s...', path, module_name)
                toc = reader(path)
                break
            except Exception:
                log.debug('Failed parsing ripping log "%s" with %s', path, module_name, exc_info=True)
        else:
            msg = N_('Failed parsing ripping log "%s"')
            log.warning(msg, path)
            raise Exception(_(msg) % path)
        disc.put(toc)

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

    def cluster(self, objs, callback=None):
        """Group files with similar metadata to 'clusters'."""
        log.debug("Clustering %r", objs)
        files = iter_files_from_objects(objs)
        thread.run_task(
            partial(self._do_clustering, list(files)),
            partial(self._clustering_finished, callback))

    def _do_clustering(self, files):
        # The clustering algorithm should completely run in the thread,
        # hence do not return the iterator.
        return list(Cluster.cluster(files))

    def _clustering_finished(self, callback, result=None, error=None):
        if error:
            log.error('Error while clustering: %r', error)
            return

        with self.window.ignore_selection_changes:
            self.window.set_sorting(False)
            for file_cluster in process_events_iter(result):
                files = set(file_cluster.files)
                if len(files) > 1:
                    cluster = self.load_cluster(file_cluster.title, file_cluster.artist)
                else:
                    cluster = self.unclustered_files
                cluster.add_files(files)
            self.window.set_sorting(True)

        if callback:
            callback()

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
            QtGui.QCursor(QtCore.Qt.CursorShape.WaitCursor))

    def restore_cursor(self):
        """Restores the cursor set by ``set_wait_cursor``."""
        super().restoreOverrideCursor()

    def refresh(self, objs):
        for obj in objs:
            if obj.can_refresh():
                obj.load(priority=True, refresh=True)

    def bring_tagger_front(self):
        self.window.setWindowState(self.window.windowState() & ~QtCore.Qt.WindowState.WindowMinimized | QtCore.Qt.WindowState.WindowActive)
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


def print_help_for_commands():
    maxwidth = 80
    helpcmd = []
    for name in sorted(REMOTE_COMMANDS):
        remcmd = REMOTE_COMMANDS[name]
        s = "  - %-34s %s" % (name + " " + remcmd.help_args, remcmd.help_text)
        helpcmd.append(fill(s, width=maxwidth, subsequent_indent=' '*39))

    print("""usage: picard -e [command] [arguments ...]
    or picard -e [command 1] [arguments ...] -e [command 2] [arguments ...]

List of the commands available to execute in Picard from the command-line:
""")
    print("\n".join(helpcmd))

    def fmt(s):
        print(fill(s, width=maxwidth, initial_indent=' '*2))

    fmt("Commands are case insensitive.")
    fmt("Picard will try to load all the positional arguments before processing commands.")
    fmt("If there is no instance to pass the arguments to, Picard will start and process the commands after the "
        "positional arguments are loaded, as mentioned above. Otherwise they will be handled by the running "
        "Picard instance")
    fmt("Arguments are optional, but some commands may require one or more arguments to actually do something.")


def process_picard_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""If one of the filenames begins with a hyphen, use -- to separate the options from the filenames.
If a new instance will not be spawned files/directories will be passed to the existing instance"""
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
    parser.add_argument("-e", "--exec", nargs="+", action='append',
                        help="send command (arguments can be entered after space) to a running instance "
                        "(use `-e help` for a list of the available commands)",
                        metavar="COMMAND")
    parser.add_argument("-M", "--no-player", action='store_true',
                        help="disable built-in media player")
    parser.add_argument("-N", "--no-restore", action='store_true',
                        help="do not restore positions and/or sizes")
    parser.add_argument("-P", "--no-plugins", action='store_true',
                        help="do not load any plugins")
    parser.add_argument("--no-crash-dialog", action='store_true',
                        help="disable the crash dialog")
    parser.add_argument("-s", "--stand-alone-instance", action='store_true',
                        help="force Picard to create a new, stand-alone instance")
    parser.add_argument('-v', '--version', action='store_true',
                        help="display version information and exit")
    parser.add_argument("-V", "--long-version", action='store_true',
                        help="display long version information and exit")
    parser.add_argument('FILE_OR_URL', nargs='*',
                        help="the file(s), URL(s) and MBID(s) to load")

    args = parser.parse_args()
    args.remote_commands_help = False

    args.processable = []
    for x in args.FILE_OR_URL:
        if not urlparse(x).netloc:
            x = os.path.abspath(x)
        args.processable.append(x)

    if args.exec:
        for e in args.exec:
            args.remote_commands_help = args.remote_commands_help or "HELP" in {x.upper().strip() for x in e}
            remote_command_args = e[1:] or ['']
            for arg in remote_command_args:
                args.processable.append(f"command://{e[0]} {arg}")

    return args


def main(localedir=None, autoupdate=True):
    EXIT_NO_NEW_INSTANCE = 30403

    # Some libs (ie. Phonon) require those to be set
    QtWidgets.QApplication.setApplicationName(PICARD_APP_NAME)
    QtWidgets.QApplication.setOrganizationName(PICARD_ORG_NAME)
    QtWidgets.QApplication.setDesktopFileName(PICARD_DESKTOP_NAME)

    # Allow High DPI Support
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    # HighDpiScaleFactorRoundingPolicy is available since Qt 5.14. This is
    # required to support fractional scaling on Windows properly.
    # It causes issues without scaling on Linux, see https://tickets.metabrainz.org/browse/PICARD-1948
    if IS_WIN and hasattr(QtGui.QGuiApplication, 'setHighDpiScaleFactorRoundingPolicy'):
        QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # Enable mnemonics on all platforms, even macOS
    QtGui.qt_set_sequence_auto_mnemonic(True)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    picard_args = process_picard_args()

    if picard_args.long_version:
        return print(versions.as_string())
    if picard_args.version:
        return print(f"{PICARD_ORG_NAME} {PICARD_APP_NAME} {PICARD_FANCY_VERSION_STR}")
    if picard_args.remote_commands_help:
        return print_help_for_commands()

    # any of the flags that change Picard's workflow significantly should trigger creation of a new instance
    if picard_args.stand_alone_instance:
        identifier = uuid4().hex
    else:
        identifier = md5(picard_args.config_file.encode('utf8')).hexdigest() if picard_args.config_file else 'main'  # nosec: B303
        identifier += '_NP' if picard_args.no_plugins else ''

    if picard_args.processable:
        log.info("Sending messages to main instance: %r", picard_args.processable)

    try:
        pipe_handler = pipe.Pipe(app_name=PICARD_APP_NAME, app_version=PICARD_FANCY_VERSION_STR,
                                    identifier=identifier, args=picard_args.processable)
        should_start = pipe_handler.is_pipe_owner
    except pipe.PipeErrorNoPermission as err:
        log.error(err)
        pipe_handler = None
        should_start = True

    # pipe has sent its args to existing one, doesn't need to start
    if not should_start:
        log.debug("No need for spawning a new instance, exiting...")
        # just a custom exit code to show that picard instance wasn't created
        sys.exit(EXIT_NO_NEW_INSTANCE)

    try:
        from PyQt5.QtDBus import QDBusConnection
        dbus = QDBusConnection.sessionBus()
        dbus.registerService(PICARD_APP_ID)
    except ImportError:
        pass

    tagger = Tagger(picard_args, localedir, autoupdate, pipe_handler=pipe_handler)

    # Initialize Qt default translations
    translator = QtCore.QTranslator()
    locale = QtCore.QLocale()
    translation_path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.LibraryLocation.TranslationsPath)
    log.debug("Looking for Qt locale %s in %s", locale.name(), translation_path)
    if translator.load(locale, "qtbase_", directory=translation_path):
        tagger.installTranslator(translator)
    else:
        log.debug('Qt locale %s not available', locale.name())

    tagger.startTimer(1000)
    exit_code = tagger.run()

    if tagger.pipe_handler.unexpected_removal:
        os._exit(exit_code)

    sys.exit(exit_code)
