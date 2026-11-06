# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2014, 2017 Lukáš Lalinský
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 amckinle
# Copyright (C) 2008-2010, 2014-2015, 2018-2026 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2010 Andrew Barnert
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2011-2014, 2017-2019 Wieland Hoffmann
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013 Ionuț Ciocîrlan
# Copyright (C) 2013 brainz34
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2013-2015, 2017-2026 Laurent Monin
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017-2018 Vishal Choudhary
# Copyright (C) 2018 virusMac
# Copyright (C) 2018, 2022-2023, 2025-2026 Bob Swift
# Copyright (C) 2019 Joel Lintunen
# Copyright (C) 2020 Julius Michaelis
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2022 Kamil
# Copyright (C) 2022 skelly37
# Copyright (C) 2025 Khoa Nguyen
# Copyright (C) 2026 leo60228
# Copyright (C) 2026 metaisfacil
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


import argparse
from collections import namedtuple
import contextlib
from functools import partial
from hashlib import blake2b
from io import StringIO
import logging
import os
from pathlib import Path
import platform
import shutil
import signal
import sys
import time
from typing import ClassVar
from urllib.parse import urlparse
from uuid import uuid4

import yaml

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import (
    PICARD_APP_ID,
    PICARD_APP_NAME,
    PICARD_FANCY_VERSION_STR,
    PICARD_ORG_NAME,
    acoustid,
    log,
)
from picard.acoustid.manager import AcoustIDManager
from picard.album import (
    Album,
)
from picard.audit import setup_audit
from picard.browser.filelookup import FileLookup
from picard.browser.server import BrowserIntegration
from picard.cli import get_subcommands_help
from picard.cluster import (
    Cluster,
)
from picard.collection import load_user_collections
from picard.config import (
    get_config,
    setup_config,
)
from picard.config_upgrade import run_config_upgrades
from picard.const import (
    BROWSER_INTEGRATION_LOCALHOST,
    METABRAINZ_OAUTH_SCOPES,
    USER_DIR,
)
from picard.const.appdirs import (
    plugin_folder,
    sessions_folder,
)
from picard.const.sys import (
    FROZEN_TEMP_PATH,
    IS_FROZEN,
    IS_HAIKU,
    IS_MACOS,
    IS_WIN,
)
from picard.debug_opts import DebugOpt
from picard.disc import (
    Disc,
)
from picard.disc.presentation import set_disc_presentation_sink
from picard.extension_points.event_hooks import register_file_post_save_processor
from picard.file import File
from picard.formats import DEFAULT_FORMATS
from picard.formats.registry import FormatRegistry
from picard.i18n import (
    N_,
    gettext as _,
    setup_i18n,
)
from picard.i18n.qt import Translators
from picard.isrcsubmit import ISRCSubmitManager
from picard.options import init_options


try:
    from picard.git.factory import has_git_backend

    if has_git_backend():
        from picard.plugin3.manager import PluginManager

        HAS_PLUGIN3 = True
    else:
        HAS_PLUGIN3 = False
        PluginCLI = None
        PluginManager = None
except ImportError:
    HAS_PLUGIN3 = False
    PluginCLI = None
    PluginManager = None

from picard.notification import (
    notifier,
    set_notifier_sink,
)
from picard.remotecommands import RemoteCommands
from picard.session.constants import SessionConstants
from picard.session.session_manager import (
    load_session_from_path,
    save_session_to_path,
)
from picard.track import (
    Track,
)
from picard.util import (
    check_io_encoding,
    cli,
    periodictouch,
    pipe,
    scan_paths_recursive,
    system_supports_long_paths,
    thread,
    unset_env_vars,
    versions,
    webbrowser2,
)
from picard.util.checkupdate import UpdateCheckManager
from picard.util.datahash import DataHash
from picard.util.qt import (
    install_qt_message_handler,
    process_events_iter,
)
from picard.util.readthedocs import ReadTheDocs
from picard.util.toc import (
    parse_toc_itunes_cddb,
)
from picard.view_presentation import set_view_presentation_sink
from picard.view_sync import set_view_sync_sink
from picard.view_updates import (
    set_view_updates_sink,
    view_updates,
)
from picard.webservice import WebService
from picard.webservice.api_helpers import (
    AcoustIdAPIHelper,
    MBAPIHelper,
)
from picard.workspace import (
    Workspace,
    WorkspaceHost,
    set_workspace_provider,
    workspace,
)
from picard.workspace_events import (
    workspace_events,
)

import picard.resources  # noqa: F401 # pylint: disable=unused-import

from picard.ui import (
    FONT_FAMILY_MONOSPACE,
    theme,
)
from picard.ui.mainwindow import MainWindow
from picard.ui.searchdialog.album import AlbumSearchDialog
from picard.ui.searchdialog.artist import ArtistSearchDialog
from picard.ui.searchdialog.track import TrackSearchDialog
from picard.ui.util import (
    FileDialog,
    busy_cursor_start,
    busy_cursor_stop,
    show_session_not_found_dialog,
)


# A "fix" for https://bugs.python.org/issue1438480
def _patched_shutil_copystat(src, dst, *, follow_symlinks=True):
    try:
        _orig_shutil_copystat(src, dst, follow_symlinks=follow_symlinks)
    except OSError:
        pass


_orig_shutil_copystat = shutil.copystat
shutil.copystat = _patched_shutil_copystat


class Tagger(WorkspaceHost, QtWidgets.QApplication):
    tagger_stats_changed = QtCore.pyqtSignal()
    listen_port_changed = QtCore.pyqtSignal(int)
    cluster_added = QtCore.pyqtSignal(Cluster)
    cluster_removed = QtCore.pyqtSignal(Cluster)
    album_added = QtCore.pyqtSignal(Album)
    album_removed = QtCore.pyqtSignal(Album)
    file_loaded = QtCore.pyqtSignal(File)
    _qt_translators_updated = QtCore.pyqtSignal()

    __instance: 'Tagger'

    def __init__(self, cmdline_args, localedir, autoupdate, pipe_handler=None):
        self._bootstrap()
        # On macOS the LANG environment variable set to a full country locale causes UI issues
        # if set when QApplication is being initialized, see PICARD-2509 and PICARD-3411.
        # As on macOS we read the locale using system libraries later on, unset LANG here.
        with unset_env_vars(*(('LANG',) if IS_MACOS else ())):
            super().__init__(sys.argv)
        self.__class__.__instance = self
        self._setup_app_icon()
        self._init_properties_from_args_or_env(cmdline_args)
        init_options()
        setup_config(app=self, filename=self._config_file)
        config = get_config()

        self.autoupdate_enabled = autoupdate

        self._init_logging(config)
        self._init_threads()
        self._init_pipe_server(pipe_handler)
        self._init_remote_commands()
        self._init_signal_handling()

        self._log_startup(config)

        theme.setup(self)
        check_io_encoding()

        # Must be before config upgrade because upgrade dialogs need to be translated.
        self._init_gettext(config, localedir)

        run_config_upgrades(config)

        self._qt_translators = Translators(self)

        self._init_workspace_events()
        self._init_webservice()
        self._init_readthedocs()
        self._init_format_registry()
        self._init_fingerprinting()
        self._init_plugins()
        self._init_browser_integration()
        self._init_entities()

        self._init_ui(config)

        register_file_post_save_processor(self._workspace.remove_album_if_complete)

    def _bootstrap(self):
        """Bootstraping"""
        # Initialize these variables early as they are needed for a clean
        # shutdown.
        self.exit_cleanup = []
        self.stopping = False

    def _setup_app_icon(self):
        icon = QtGui.QIcon()
        if IS_MACOS:
            sizes = (16, 32, 128, 256, 512)
            icon_name = 'macos_icon'
        else:
            sizes = (16, 24, 32, 48, 128, 256, 512)
            icon_name = PICARD_APP_ID
        for size in sizes:
            icon.addFile(
                f":/images/{size}x{size}/{icon_name}.png",
                QtCore.QSize(size, size),
            )
        self.setWindowIcon(icon)

    def _init_properties_from_args_or_env(self, cmdline_args):
        """Initialize properties from command line arguments or environment"""
        self._audit = cmdline_args.audit
        self._config_file = cmdline_args.config_file
        self._debug_opts = cmdline_args.debug_opts
        self._debug = cmdline_args.debug or 'PICARD_DEBUG' in os.environ
        self._no_player = cmdline_args.no_player
        self._no_plugins = cmdline_args.no_plugins
        self._no_restore = cmdline_args.no_restore
        self._to_load = cmdline_args.processable

    def _init_logging(self, config):
        """Initialize logging & audit"""
        # Enabling any debug option implies debug-level logging, otherwise its
        # log.debug() output would be silently discarded at the default
        # verbosity. This mirrors the CLI behaviour (see picard/cli/_bootstrap.py).
        if self._debug_opts:
            DebugOpt.from_string(self._debug_opts)
        debug = self._debug or DebugOpt.any_enabled()
        log.set_verbosity(logging.DEBUG if debug else config.setting['log_verbosity'])

        # Route Qt's own log messages through Picard's logging as soon as the
        # log is configured, so Qt diagnostics emitted during the rest of
        # startup are captured. Also drops the known-benign Qt-internal
        # warnings (e.g. the spurious QSslSocket "device not open" read warning
        # on HTTP/2 error replies).
        install_qt_message_handler()

        setup_audit(self._audit)

    def _init_threads(self):
        """Initialize threads"""
        # Main thread pool used for most background tasks
        self.thread_pool = QtCore.QThreadPool(self)
        self.register_cleanup(self.thread_pool.waitForDone)
        # Two threads are needed for the pipe handler and command processing.
        # At least one thread is required to run other Picard background tasks.
        self.thread_pool.setMaxThreadCount(max(3, QtCore.QThread.idealThreadCount()))

        # Provide a separate thread pool for operations that should not be
        # delayed by longer background processing tasks, e.g. because the user
        # expects instant feedback instead of waiting for a long list of
        # operations to finish.
        self.priority_thread_pool = QtCore.QThreadPool(self)
        self.register_cleanup(self.priority_thread_pool.waitForDone)
        self.priority_thread_pool.setMaxThreadCount(1)

        # Use a separate thread pool for file saving, with a thread count of 1,
        # to avoid race conditions in File._save_and_rename.
        self.save_thread_pool = QtCore.QThreadPool(self)
        self.register_cleanup(self.save_thread_pool.waitForDone)
        self.save_thread_pool.setMaxThreadCount(1)

    def _init_pipe_server(self, pipe_handler):
        """Setup pipe handler for managing single app instance and commands."""
        self.pipe_handler = pipe_handler

        if self.pipe_handler:
            self.register_cleanup(self.pipe_handler.stop)
            self._command_thread_running = False
            self.pipe_handler.pipe_running = True
            thread.run_task(self.pipe_server, self._pipe_server_finished)

    def _init_signal_handling(self):
        """Set up signal handling"""
        if IS_WIN:
            return

        # It's not possible to call all available functions from signal
        # handlers, therefore we need to set up a QSocketNotifier to listen
        # on a socket. Sending data through a socket can be done in a
        # signal handler, so we use the socket to notify the application of
        # the signal.
        # This code is adopted from
        # https://doc.qt.io/qt-6/unix-signals.html

        # To not make the socket module a requirement for the Windows
        # installer, import it here and not globally
        import socket

        self.signalfd = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM, 0)

        self.signalnotifier = QtCore.QSocketNotifier(self.signalfd[1].fileno(), QtCore.QSocketNotifier.Type.Read, self)
        self.signalnotifier.activated.connect(self.sighandler)

        signal.signal(signal.SIGHUP, self.signal)
        signal.signal(signal.SIGINT, self.signal)
        signal.signal(signal.SIGTERM, self.signal)

    def _log_startup(self, config):
        """Log interesting infos at startup"""
        log.debug("Starting Picard from %r", os.path.abspath(__file__))
        log.debug(
            "Platform: %s %s %s", platform.platform(), platform.python_implementation(), platform.python_version()
        )
        log.debug("Versions: %s", versions.as_string())
        log.debug("Configuration file path: %r", config.fileName())

        log.debug("User directory: %r", os.path.abspath(USER_DIR))
        log.debug("System long path support: %r", system_supports_long_paths())

        # log interesting environment variables
        log.debug("Qt Env.: %s", " ".join("%s=%r" % (k, v) for k, v in os.environ.items() if k.startswith('QT_')))
        desktop_env_vars = (
            'XDG_CURRENT_DESKTOP',
            'XDG_SESSION_DESKTOP',
            'XDG_SESSION_TYPE',
            'DESKTOP_SESSION',
            'KDE_FULL_SESSION',
        )
        log.debug(
            "Desktop Env.: %s",
            " ".join("%s=%r" % (k, os.environ[k]) for k in desktop_env_vars if k in os.environ),
        )

    def _init_gettext(self, config, localedir):
        """Initialize gettext"""
        if not localedir:
            # Unfortunately we cannot use importlib.resources to access the data
            # files, as gettext expects a path to a directory for localedir.
            basedir = FROZEN_TEMP_PATH if IS_FROZEN else os.path.dirname(__file__)
            localedir = os.path.join(basedir, 'locale')
        setup_i18n(localedir, config.setting['ui_language'], log.debug)

    def _init_webservice(self):
        """Initialize web service/API"""
        self.webservice = WebService()
        self.register_cleanup(self.webservice.stop)
        self.webservice.pending_requests_changed.connect(workspace_events().tagger_stats_changed)
        self.mb_api = MBAPIHelper(self.webservice)
        load_user_collections()

    def _init_format_registry(self):
        """Initialize the file formats registry and register default formats"""
        self.format_registry = FormatRegistry(self)
        for format in DEFAULT_FORMATS:
            self.format_registry.register(format)

    def _init_fingerprinting(self):
        """Initialize fingerprinting"""
        acoustid_api = AcoustIdAPIHelper(self.webservice)
        self.acoustid_client = acoustid.AcoustIDClient(acoustid_api)
        self.acoustid_client.init()
        self.register_cleanup(self.acoustid_client.done)
        self.acoustid_manager = AcoustIDManager(acoustid_api)
        self.isrc_submit_manager = ISRCSubmitManager(self.mb_api)

    def _init_plugins(self):
        """Initialize and load plugins"""
        if HAS_PLUGIN3 and not self._no_plugins:
            self._pluginmanager3 = PluginManager(self)
            self._pluginmanager3.plugin_state_changed.connect(self._on_plugin_status_changed)
            self._pluginmanager3.add_directory(plugin_folder(), primary=True)
        else:
            self._pluginmanager3 = None
            log.warning('Plugin3 system not available (git backend not available)')

    def get_plugin_manager(self):
        """Get the plugin manager instance.

        Returns:
            PluginManager or None: The plugin manager instance if available, None otherwise.
        """
        return getattr(self, '_pluginmanager3', None)

    def get_plugins_available(self) -> tuple[bool, str]:
        """Returns whether the plugin system is available.

        Returns a tuple, where the first element is a boolean indicating the
        availability and the second element is a string with a reason if the
        plugin system is unavailable.
        """
        if not HAS_PLUGIN3:
            return False, _('Git backend not available')
        elif self._no_plugins:
            return False, _('Disabled by command line parameter')
        return True, ""

    def _on_plugin_status_changed(self):
        self.format_registry.rebuild_extension_map()

    def _init_browser_integration(self):
        """Initialize browser integration"""
        self.browser_integration = BrowserIntegration()
        self.register_cleanup(self.browser_integration.stop)
        self.browser_integration.listen_port_changed.connect(self.on_listen_port_changed)

    def _init_readthedocs(self):
        """Initialize the ReadTheDocs information"""
        ReadTheDocs.initialize(self.webservice)

    def _init_entities(self):
        """Initialize tagger objects/entities"""
        # The entity registries and batch-save/restore bookkeeping now live on
        # a Workspace. Tagger subclasses WorkspaceHost, which exposes each field
        # as a delegating property, so existing self.tagger.<field> access is
        # unchanged. The Workspace is also installed as the process-wide
        # workspace provider so core code reaching the working set via
        # workspace() sees the same object. See picard.workspace.
        self._workspace = Workspace()
        set_workspace_provider(self._workspace)

    def _init_workspace_events(self):
        """Forward the shared WorkspaceEvents signals onto Tagger's own signals.

        The working-set-changed signals (album_added/removed,
        cluster_added/removed, file_loaded, tagger_stats_changed) live on the
        process-wide WorkspaceEvents facade; core emitters and GUI connectors
        use workspace_events() directly.

        Tagger keeps declaring the same signals and re-emits each facade signal
        on its own, as a BACKWARD-COMPATIBILITY surface: plugins reach the
        application object via PluginApi.tagger and may connect to
        ``tagger.album_added`` / ``tagger.file_loaded`` etc. Forwarding
        facade -> Tagger keeps those connections working even though nothing
        emits on the Tagger signals directly anymore. (Headless has no Tagger,
        so this forwarding simply does not exist there.)
        """
        events = workspace_events()
        # Re-emit facade signals on the matching Tagger signal for plugin
        # backward compatibility (see docstring).
        #
        # The facade signals carry ``object`` (PyQt_PyObject) to stay free of
        # core-entity imports, while the Tagger signals are typed
        # (Album/Cluster/File, i.e. QObject*). A direct signal -> signal
        # connect is rejected by Qt as "Incompatible sender/receiver arguments"
        # because those C++ signatures differ, so we forward through Python
        # slots that re-emit on the typed Tagger signal instead.
        events.album_added.connect(lambda obj: self.album_added.emit(obj))
        events.album_removed.connect(lambda obj: self.album_removed.emit(obj))
        events.cluster_added.connect(lambda obj: self.cluster_added.emit(obj))
        events.cluster_removed.connect(lambda obj: self.cluster_removed.emit(obj))
        events.file_loaded.connect(lambda obj: self.file_loaded.emit(obj))
        events.tagger_stats_changed.connect(self.tagger_stats_changed)

    def _init_ui(self, config):
        """Initialize User Interface / Main Window"""
        self.enable_menu_icons(config.setting['show_menu_icons'])
        self.window = MainWindow(disable_player=self._no_player)
        # Route core status/progress/action notifications to the main window.
        # In headless mode no sink is installed and the facade only logs.
        set_notifier_sink(self.window)
        # Route core view-update suspensions (e.g. batch file moves) to the
        # main window. In headless mode no sink is installed and they no-op.
        set_view_updates_sink(self.window)
        # Route core view-refresh requests (metadata box / cover-art box after
        # load/edit) to the main window. In headless mode they no-op.
        set_view_sync_sink(self.window)
        # Route core presentation actions (bring the window to front for an
        # externally triggered load) to this application object. In headless
        # mode no sink is installed and they no-op.
        set_view_presentation_sink(self)
        # Route CD/disc lookup result presentation (the release picker dialog +
        # the lookup busy cursor) to the main window. In headless mode no sink
        # is installed and the single unambiguous match is auto-loaded.
        set_disc_presentation_sink(self.window)

        # On macOS temporary files get deleted after 3 days not being accessed.
        # Touch these files regularly to keep them alive if Picard
        # is left running for a long time.
        if IS_MACOS:
            periodictouch.enable_timer()

        # Load release version information
        if self.autoupdate_enabled:
            self.updatecheckmanager = UpdateCheckManager(self)

    @property
    def is_wayland(self):
        return self.platformName() == 'wayland'

    def pipe_server(self):
        IGNORED = {pipe.Pipe.MESSAGE_TO_IGNORE, pipe.Pipe.NO_RESPONSE_MESSAGE}
        while self.pipe_handler.pipe_running:
            messages = [x for x in self.pipe_handler.read_from_pipe() if x not in IGNORED]
            if messages:
                log.debug("pipe messages: %r", messages)
                self.load_to_picard(messages)

    def _pipe_server_finished(self, result=None, error=None):
        if error:
            log.error("pipe server failed: %r", error)
        else:
            log.debug("pipe server stopped")

    def start_process_commands(self):
        if not self._command_thread_running:
            self._command_thread_running = True
            thread.run_task(self.run_commands, self._run_commands_finished)

    def run_commands(self):
        while not self.stopping:
            if not RemoteCommands.command_queue.empty() and not RemoteCommands.get_running():
                (cmd, arg) = RemoteCommands.command_queue.get()
                if cmd in self.commands:
                    arg = arg.strip()
                    log.info("Executing command: %s %r", cmd, arg)
                    if cmd == 'QUIT':
                        thread.to_main(self.commands[cmd], arg)
                    else:
                        RemoteCommands.set_running(True)
                        original_priority_thread_count = self.priority_thread_pool.activeThreadCount()
                        original_main_thread_count = self.thread_pool.activeThreadCount()
                        original_save_thread_count = self.save_thread_pool.activeThreadCount()
                        thread.to_main_with_blocking(self.commands[cmd], arg)

                        # Continue to show the task as running until all of the following
                        # conditions are met:
                        #
                        #   - main thread pool active tasks count is less than or equal to the
                        #     count at the start of task execution
                        #
                        #   - priority thread pool active tasks count is less than or equal to
                        #     the count at the start of task execution
                        #
                        #   - save thread pool active tasks count is less than or equal to the
                        #     count at the start of task execution
                        #
                        #   - there are no pending webservice requests
                        #
                        #   - there are no acoustid fingerprinting tasks running

                        while True:
                            time.sleep(0.1)
                            if (
                                self.priority_thread_pool.activeThreadCount() > original_priority_thread_count
                                or self.thread_pool.activeThreadCount() > original_main_thread_count
                                or self.save_thread_pool.activeThreadCount() > original_save_thread_count
                                or self.webservice.num_pending_web_requests
                                or self.acoustid_client.is_fingerprinting
                            ):
                                continue
                            break

                        log.info("Completed command: %s %r", cmd, arg)
                        RemoteCommands.set_running(False)

                else:
                    log.error("Unknown command: %r", cmd)
                RemoteCommands.command_queue.task_done()
            elif RemoteCommands.command_queue.empty():
                # All commands finished, stop processing
                self._command_thread_running = False
                break
            time.sleep(0.01)

    def _run_commands_finished(self, result=None, error=None):
        if error:
            log.error("command executor failed: %r", error)
        else:
            log.debug("command executor stopped")

    def load_to_picard(self, items):
        commands = []
        for item in items:
            parts = str(item).split(maxsplit=1)
            commands.append((parts[0], parts[1:] or ['']))
        RemoteCommands.parse_commands_to_queue(commands)
        self.start_process_commands()

    def _init_remote_commands(self):
        self.commands = RemoteCommands.commands()

    def enable_menu_icons(self, enabled):
        self.setAttribute(QtCore.Qt.ApplicationAttribute.AA_DontShowIconsInMenus, not enabled)

    def register_cleanup(self, func):
        self.exit_cleanup.append(func)

    def run_cleanup(self):
        for f in reversed(self.exit_cleanup):
            f()

    def on_listen_port_changed(self, port):
        self.webservice.oauth_manager.redirect_uri = self._mb_login_redirect_uri()
        self.listen_port_changed.emit(port)

    def _mb_login_dialog(self, parent):
        if not parent:
            parent = self.window
        dialog = QtWidgets.QInputDialog(parent)
        dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        dialog.setWindowTitle(_("MusicBrainz Account"))
        dialog.setLabelText(_("Authorization code:"))
        status = dialog.exec()
        if status == QtWidgets.QDialog.DialogCode.Accepted:
            return dialog.textValue()
        else:
            return None

    def _mb_login_redirect_uri(self):
        if self.browser_integration and self.browser_integration.is_running:
            return f'http://{BROWSER_INTEGRATION_LOCALHOST}:{self.browser_integration.port}/auth'
        else:
            # If browser integration is disabled or not running on the standard
            # port use out-of-band flow (with manual copying of the token).
            return None

    def mb_login(self, callback, parent=None):
        oauth_manager = self.webservice.oauth_manager
        scopes = METABRAINZ_OAUTH_SCOPES
        authorization_url = oauth_manager.get_authorization_url(
            scopes, partial(self.on_mb_authorization_finished, callback)
        )
        webbrowser2.open(authorization_url)
        if oauth_manager.is_oob:
            authorization_code = self._mb_login_dialog(parent)
            if authorization_code is not None:
                self.webservice.oauth_manager.exchange_authorization_code(
                    authorization_code, scopes, partial(self.on_mb_authorization_finished, callback)
                )
            else:
                callback(False, None)

    def on_mb_authorization_finished(self, callback, successful=False, error_msg=None):
        if successful:
            self.webservice.oauth_manager.fetch_username(partial(self.on_mb_login_finished, callback))
        else:
            callback(False, error_msg)

    def on_mb_login_finished(self, callback, successful, error_msg):
        if successful:
            load_user_collections()
        callback(successful, error_msg)

    def mb_logout(self, callback):
        self.webservice.oauth_manager.revoke_tokens(partial(self.on_mb_logout_finished, callback))

    def on_mb_logout_finished(self, callback, successful, error_msg):
        if successful:
            load_user_collections()
        callback(successful, error_msg)

    def quit(self):
        self.exit()
        super().quit()

    def exit(self):
        if self.stopping:
            return
        self.stopping = True

        # Best-effort crash/exit backup if enabled
        # Only attempt if tagger is fully initialized
        if hasattr(self, 'unclustered_files'):
            config = get_config()
            with contextlib.suppress(OSError, PermissionError, FileNotFoundError, ValueError, OverflowError):
                if config.setting['session_backup_on_crash']:
                    path = Path(sessions_folder()) / ("autosave" + SessionConstants.SESSION_FILE_EXTENSION)
                    save_session_to_path(self, path)

        log.debug("Picard stopping")
        with DebugOpt.TIMINGS.timing("run_cleanup"):
            self.run_cleanup()
        with DebugOpt.TIMINGS.timing("DataHash.remove_all_files"):
            DataHash.remove_all_files()
        QtCore.QCoreApplication.processEvents()
        if sys.stdout:
            sys.stdout.flush()
        if sys.stderr:
            sys.stderr.flush()

    def _run_init(self):
        config = get_config()
        # Load last session if configured
        if config.setting['session_load_last_on_startup']:
            last_path = config.persist['last_session_path']
            if last_path:
                try:
                    load_session_from_path(self, last_path)
                except FileNotFoundError:
                    show_session_not_found_dialog(self.window, last_path)
                except (OSError, PermissionError, yaml.YAMLError, KeyError) as e:
                    # Surface startup load errors to user similar to interactive load
                    log.debug(f"Error loading session from {last_path}: {e}")
                    QtWidgets.QMessageBox.critical(
                        self.window,
                        _("Failed to load session"),
                        _('Could not load session from "%(path)s":\n\n%(error)s')
                        % {"path": str(last_path), "error": str(e)},
                    )

        if self._to_load:
            self.load_to_picard(self._to_load)
        del self._to_load

    def run(self):
        # Setup autosave if configured
        config = get_config()
        interval_min = int(config.setting['session_autosave_interval_min'])
        if interval_min > 0:
            self._session_autosave_timer = QtCore.QTimer(self)
            self._session_autosave_timer.setInterval(max(1, interval_min) * 60 * 1000)

            def _autosave():
                path = config.persist['session_autosave_path'] or None
                if not path:
                    path = config.persist['last_session_path'] or None
                if not path:
                    path = str(Path(sessions_folder()) / ("autosave" + SessionConstants.SESSION_FILE_EXTENSION))
                    config.persist['session_autosave_path'] = path

                with contextlib.suppress(OSError, PermissionError, FileNotFoundError, ValueError, OverflowError):
                    # Best effort autosave; do not crash programme
                    save_session_to_path(self, path)

            self._session_autosave_timer.timeout.connect(_autosave)
            self._session_autosave_timer.start()

        self.update_browser_integration()
        self.window.show()

        blacklisted_plugins = []
        plugin_manager = self.get_plugin_manager()
        if plugin_manager:
            blacklisted_plugins = plugin_manager.init_plugins()

        # Show warning if any plugins were blacklisted
        if blacklisted_plugins:
            plugin_list = '\n'.join(f'• {name}: {reason}' for name, reason in blacklisted_plugins)
            message = _(
                'The following plugins have been blacklisted and disabled:\n\n'
                '{plugin_list}\n\n'
                'These plugins may contain security vulnerabilities or malicious code. '
                'They have been automatically disabled for your protection.'
            ).format(plugin_list=plugin_list)
            QtWidgets.QMessageBox.warning(self.window, _('Blacklisted Plugins Detected'), message)

        # Show warning if any plugins failed to initialize
        if plugin_manager and plugin_manager._init_failed_plugins:
            plugin_list = '\n'.join(f'• {pid}: {err}' for pid, err in plugin_manager._init_failed_plugins)
            QtWidgets.QMessageBox.warning(
                self.window,
                _('Plugin Initialization Failed'),
                _('The following plugins failed to load and have been disabled:\n\n{plugin_list}').format(
                    plugin_list=plugin_list
                ),
            )

        QtCore.QTimer.singleShot(0, self._run_init)
        self._qt_translators_updated.emit()
        res = self.exec()
        self.exit()
        return res

    def update_browser_integration(self):
        config = get_config()
        if config.setting['browser_integration']:
            self.browser_integration.start()
        else:
            self.browser_integration.stop()

    _BATCH_TIME_BUDGET = 0.050  # 50ms per batch (~20 yields/sec)
    _callback_queue: ClassVar[list] = []
    _callback_timer_running: bool = False

    def _process_in_batches(
        self, items: list, process_func, label: str, time_budget: float | None = None, on_complete=None
    ) -> None:
        """Process items with a time budget, yielding to the event loop between batches.

        Thin wrapper around :func:`picard.util.thread.process_in_batches` (the
        frontend-agnostic batch helper); kept as a method for the existing call
        sites.
        """
        thread.process_in_batches(items, process_func, label, time_budget=time_budget, on_complete=on_complete)

    def event(self, event):
        if isinstance(event, thread.ProxyToMainEvent):
            self._callback_queue.append(event)
            if not self._callback_timer_running:
                self._callback_timer_running = True
                QtCore.QTimer.singleShot(0, self._process_callback_batch)
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

    def _process_callback_batch(self) -> None:
        """Process queued callbacks until the time budget is exhausted, then yield."""
        deadline = time.perf_counter() + self._BATCH_TIME_BUDGET
        count = 0
        while self._callback_queue and time.perf_counter() < deadline:
            self._callback_queue.pop(0).run()
            count += 1
        log.debug_if(DebugOpt.TIMINGS, "Callback batch: %d items, %d queued", count, len(self._callback_queue))
        if self._callback_queue:
            QtCore.QTimer.singleShot(0, self._process_callback_batch)
        else:
            self._callback_timer_running = False

    def _file_loaded(self, file, target=None, remove_file=False, unmatched_files=None):
        config = get_config()
        wks = workspace()
        if wks.file_pending_done() == 0:
            with DebugOpt.TIMINGS.timing("suspend_while_loading_exit"):
                view_updates().suspend_while_loading_exit()

        if remove_file:
            file.remove()
            return

        if file is None:
            return

        if file.has_error():
            self.unclustered_files.add_file(file)
            return

        # Place the file (MBID auto-move / move_file / analyze fallback); the
        # UI-agnostic policy lives on the Workspace.
        wks.place_loaded_file(file, target=target, unmatched_files=unmatched_files)

        # Auto cluster newly added files if they are not explicitly moved elsewhere
        if wks.pending_files_count == 0 and unmatched_files and config.setting['cluster_new_files']:
            self.cluster(unmatched_files)

    def add_files(self, filenames, target=None):
        """Add files to the tagger."""
        # Keep the UI responsive while a large number of paths are checked.
        opened = workspace().open_files(process_events_iter(filenames))
        new_files = opened.opened
        if new_files:
            log.debug("Adding %d files", len(new_files))
            view_updates().suspend_while_loading_enter()
            workspace().add_pending_files(len(new_files))
            unmatched_files = []
            self._load_files_batch(new_files, target, unmatched_files)

    def _load_files_batch(self, files: list, target: object, unmatched_files: list) -> None:
        """Dispatch file loads using time-budgeted batching."""
        callback = partial(self._file_loaded, target=target, unmatched_files=unmatched_files)
        self._process_in_batches(files, lambda f: f.load(callback), "File load dispatch")

    def add_paths(self, paths, target=None):
        config = get_config()
        files = scan_paths_recursive(
            paths, config.setting['recursively_add_files'], config.setting["ignore_hidden_files"]
        )
        self.add_files(files, target=target)

    def get_file_lookup(self):
        """Return a FileLookup object."""
        config = get_config()
        return FileLookup(
            self, config.setting['server_host'], config.setting['server_port'], self.browser_integration.port
        )

    def search(self, text, search_type, adv=False, mbid_matched_callback=None, force_browser=False):
        """Search on the MusicBrainz website."""
        search_types = {
            'track': {'entity': 'recording', 'dialog': TrackSearchDialog},
            'album': {'entity': 'release', 'dialog': AlbumSearchDialog},
            'artist': {'entity': 'artist', 'dialog': ArtistSearchDialog},
        }
        if search_type not in search_types:
            return
        search = search_types[search_type]
        lookup = self.get_file_lookup()
        config = get_config()
        if config.setting["builtin_search"] and not force_browser:
            # mbid_lookup dispatches an async load only when the text is a
            # known MBID/URL (it returns True in that case). Flash only then;
            # the fallback below opens a modal dialog, which is its own
            # immediate feedback and needs no cursor flash.
            if lookup.mbid_lookup(text, search['entity'], mbid_matched_callback=mbid_matched_callback):
                notifier().flash_busy()
            else:
                dialog = search['dialog'](self.window)
                dialog.search(text)
                dialog.exec()
        else:
            # Opens the browser / dispatches an entity search asynchronously.
            notifier().flash_busy()
            lookup.search_entity(
                search['entity'], text, adv, mbid_matched_callback=mbid_matched_callback, force_browser=force_browser
            )

    def collection_lookup(self):
        """Lookup the users collections on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        config = get_config()
        # Result appears asynchronously; acknowledge the action immediately.
        notifier().flash_busy()
        lookup.collection_lookup(config.persist['oauth_username'])

    def browser_lookup(self, item):
        """Lookup the object's metadata on the MusicBrainz website."""
        lookup = self.get_file_lookup()
        metadata = item.metadata
        # Result appears asynchronously (browser opens / network lookup);
        # acknowledge the action immediately.
        notifier().flash_busy()
        # Only lookup via MB IDs if matched to a Track or Album;
        # otherwise ignore and search by metadata details
        is_track = isinstance(item, Track)
        is_album = isinstance(item, Album)
        if is_track or is_album:
            itemid = item.id
            if is_track:
                lookup.recording_lookup(itemid)
            elif is_album:
                lookup.album_lookup(itemid)
        else:
            lookup.tag_lookup(
                metadata['albumartist'] if item.is_album_like else metadata['artist'],
                metadata['album'],
                metadata['title'],
                metadata['tracknumber'],
                '' if item.is_album_like else str(metadata.length),
                item.filename if isinstance(item, File) else '',
            )

    def _lookup_disc(self, disc, result=None, error=None):
        busy_cursor_stop()
        if error is not None:
            QtWidgets.QMessageBox.critical(
                self.window, _("CD Lookup Error"), _("Error while reading CD:\n\n%s") % error
            )
        else:
            disc.lookup()

    def lookup_cd(self, device=None):
        """Reads CD from the selected drive and tries to lookup the DiscID on MusicBrainz."""
        if not device:
            config = get_config()
            if device := config.setting['cd_lookup_device']:
                device = device.split(',', 1)[0]
            else:
                # rely on python-discid auto detection
                device = None

        self.run_lookup_cd(device)

    def run_lookup_cd(self, device):
        disc = Disc()
        busy_cursor_start()
        thread.run_task(partial(disc.read, device), partial(self._lookup_disc, disc), traceback=log.is_debug())

    def lookup_discid_from_logfile(self):
        file_chooser = FileDialog(parent=self.window)
        file_chooser.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        file_chooser.setNameFilters(
            [
                _("All supported log files") + " (*.log *.txt *.toc)",
                _("EAC / XLD / Whipper / fre:ac log files") + " (*.log)",
                _("dBpoweramp log files") + " (*.txt)",
                _("SCSI TOC file") + " (*.toc)",
                _("All files") + " (*)",
            ]
        )
        if file_chooser.exec():
            filepath = Path(file_chooser.selectedFiles()[0])
            self.run_lookup_discid_from_logfile(filepath)

    def run_lookup_discid_from_logfile(self, filepath):
        disc = Disc()
        busy_cursor_start()
        thread.run_task(
            partial(disc.read_log, filepath),
            partial(self._lookup_disc, disc),
            traceback=log.is_debug(),
        )

    def lookup_discid_from_tags(self, files):
        """Perform a CD lookup using table of contents from tags (iTunes CDDB 1)."""
        # Try to find TOC data in tags from all files
        toc_data = None
        toc_source = None

        for file in files:
            # Check for itunes_cddb_1 format
            itunes_tag = file.metadata.get('itunes_cddb_1')
            if itunes_tag:
                toc_data = itunes_tag
                toc_source = 'itunes_cddb_1'
                break

        if not toc_data:
            msg = _('Disc information could not be found')
            self.window.set_statusbar_message(msg)
            QtWidgets.QMessageBox.warning(self.window, _('Lookup Error'), msg)
            return

        # Gather tag from all files that have it
        tags = []
        for file in files:
            if toc_source == 'itunes_cddb_1':
                tag = file.metadata.get('itunes_cddb_1')
            if tag:
                tags.append(tag)

        # Abort if no files have the tag
        if not tags:
            msg = _('Disc information could not be found')
            self.window.set_statusbar_message(msg)
            QtWidgets.QMessageBox.warning(self.window, _('Lookup Error'), msg)
            return

        # Ensure all tags found are identical
        unique_tags = set(tags)
        if len(unique_tags) != 1:
            msg = _('Selected files contain tags with conflicting disc information')
            self.window.set_statusbar_message(msg)
            QtWidgets.QMessageBox.warning(self.window, _('Lookup Error'), msg)
            return

        # Parse the TOC data using the appropriate parser
        try:
            if toc_source == 'itunes_cddb_1':
                num_tracks, leadout_lba, track_lbas = parse_toc_itunes_cddb(toc_data)

            # Validate track count matches number of files
            if len(files) != num_tracks:
                raise ValueError(
                    f"Number of tracks ({num_tracks}) does not match number of selected files ({len(files)})"
                )

        except Exception as e:
            self.window.set_statusbar_message(_('Failed to parse disc information from tags: %s') % str(e))
            return

        # Reconstruct TOC in MusicBrainz format
        # e.g. first_track last_track leadout_lba track_lba_1 track_lba_2 ...
        toc_string = f"1+{num_tracks}+{leadout_lba}"
        for offset in track_lbas:
            toc_string += f"+{offset}"

        self.window.set_statusbar_message(N_('Looking up disc from tags…'))
        busy_cursor_start()

        # Skip dialog if exactly one match, and match files to album
        disc = Disc()
        disc.lookup_by_toc(toc_string, skip_dialog=True, files_to_match=list(files))

    # =======================================================================
    #  Clusters
    # =======================================================================

    # Clustering (sync cluster_files + async cluster + the apply/finish steps)
    # lives on the Workspace; Tagger inherits the cluster() delegator from
    # WorkspaceHost. It is kept as a delegator because api.tagger.cluster(objs)
    # is documented plugin API.

    # =======================================================================
    #  Utils
    # =======================================================================

    def refresh(self, objs):
        for obj in objs:
            if obj.can_refresh:
                obj.load(priority=True, refresh=True)

    def bring_tagger_front(self):
        self.window.setWindowState(
            self.window.windowState() & ~QtCore.Qt.WindowState.WindowMinimized | QtCore.Qt.WindowState.WindowActive
        )
        self.window.raise_()
        self.window.activateWindow()

    def remove_with_selection(self, objects):
        """Remove ``objects`` keeping the tree view's selection consistent.

        Sink method for :mod:`picard.view_presentation`: the main panel suspends
        its own selection-change handling around the removal and then fixes up
        the current selection.
        """
        self.window.panel.remove(objects)

    @staticmethod
    def instance() -> 'Tagger':
        return Tagger.__instance

    def signal(self, signum, frame):
        log.debug("signal %i received", signum)
        # Send a notification about a received signal from the signal handler
        # to Qt.
        self.signalfd[0].sendall(b"a")

    def sighandler(self):
        self.signalnotifier.setEnabled(False)
        self.quit()
        self.signalnotifier.setEnabled(True)


class CmdlineArgsParser(argparse.ArgumentParser):
    def exit(self, status=0, message=None):
        if is_windowed_app():
            if message:
                show_standalone_messagebox(message)
            super().exit(status)
        else:
            super().exit(status, message)

    def error(self, message):
        if is_windowed_app():
            if message:
                show_standalone_messagebox(message)
            super().exit(2)
        else:
            super().error(message)

    def print_help(self, file=None):
        if is_windowed_app() and file is None:
            file = StringIO()
            super().print_help(file=file)
            file.seek(0)
            show_standalone_messagebox(file.read())
        else:
            return super().print_help(file)


def is_windowed_app():
    # Return True if this is a Windows windowed application without attached console
    return IS_WIN and not sys.stdout


def show_standalone_messagebox(message, informative_text=None):
    app = QtCore.QCoreApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    msgbox = QtWidgets.QMessageBox()
    msgbox.setIcon(QtWidgets.QMessageBox.Icon.Information)
    msgbox.setWindowTitle(f"{PICARD_ORG_NAME} {PICARD_APP_NAME}")
    msgbox.setTextFormat(QtCore.Qt.TextFormat.PlainText)
    font = msgbox.font()
    font.setFamily(FONT_FAMILY_MONOSPACE)
    msgbox.setFont(font)
    msgbox.setText(message)
    if informative_text:
        msgbox.setInformativeText(informative_text)
    msgbox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    msgbox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Ok)
    msgbox.exec()
    app.quit()


def print_message_and_exit(message, informative_text=None, status=0):
    if is_windowed_app():
        show_standalone_messagebox(message, informative_text)
        sys.exit(status)
    else:
        cli.print_message_and_exit(message, informative_text, status)


def print_help_for_commands():
    maxwidth = 300 if is_windowed_app() else 80
    message, informative_text = RemoteCommands.help(maxwidth)
    print_message_and_exit(message, informative_text)


def process_cmdline_args():
    epilog = (
        "If one of the filenames begins with a hyphen, use -- to separate the\n"
        "options from the filenames.\n"
        "If a new instance will not be spawned files/directories will be passed\n"
        "to the existing instance\n"
        "\n" + get_subcommands_help()
    )

    parser = CmdlineArgsParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    # Qt default arguments. Parse them so Picard does not interpret the
    # arguments as file names to load.
    parser.add_argument('-style', nargs=1, help=argparse.SUPPRESS)
    parser.add_argument('-stylesheet', nargs=1, help=argparse.SUPPRESS)
    # Same for default X arguments
    parser.add_argument('-display', nargs=1, help=argparse.SUPPRESS)

    # Picard specific arguments
    parser.add_argument(
        '-a',
        '--audit',
        action='store',
        default=None,
        help="audit events passed as a comma-separated list, prefixes supported, "
        "use all to match any (see https://docs.python.org/3/library/audit_events.html#audit-events)",
    )
    parser.add_argument('-c', '--config-file', action='store', default=None, help="location of the configuration file")
    parser.add_argument('-d', '--debug', action='store_true', help="enable debug-level logging")
    parser.add_argument(
        '-e',
        '--exec',
        nargs='+',
        action='append',
        help="send command (arguments can be entered after space) to a running instance "
        "(use `-e help` for a list of the available commands)",
        metavar='COMMAND',
    )
    parser.add_argument('-M', '--no-player', action='store_true', help="disable built-in media player")
    parser.add_argument('-N', '--no-restore', action='store_true', help="do not restore positions and/or sizes")
    parser.add_argument('-P', '--no-plugins', action='store_true', help="do not load any plugins")
    parser.add_argument('--no-crash-dialog', action='store_true', help="disable the crash dialog")
    parser.add_argument(
        '--debug-opts',
        action='store',
        default=None,
        nargs='?',
        const='',
        metavar='OPTIONS',
        help="comma-separated list of debug options. Use --debug-opts without value to list available options",
    )
    parser.add_argument(
        '-s', '--stand-alone-instance', action='store_true', help="force Picard to create a new, stand-alone instance"
    )
    parser.add_argument('-v', '--version', action='store_true', help="display version information and exit")
    parser.add_argument('-V', '--long-version', action='store_true', help="display long version information and exit")
    parser.add_argument('FILE_OR_URL', nargs='*', help="the file(s), URL(s) and MBID(s) to load")

    args = parser.parse_args()
    args.remote_commands_help = False

    # Handle debug-opts help request
    if args.debug_opts is not None and not args.debug_opts.strip():
        DebugOpt.print_help_and_exit()

    args.processable = []
    for path in args.FILE_OR_URL:
        if not urlparse(path).netloc:
            try:
                path = os.path.abspath(path)
            except FileNotFoundError:
                # os.path.abspath raises if path is relative and cwd doesn't
                # exist anymore. Just pass the path as it is and leave
                # the error handling to Picard's file loading.
                pass
        args.processable.append(f"LOAD {path}")

    if args.exec:
        for e in args.exec:
            args.remote_commands_help = args.remote_commands_help or 'HELP' in {x.upper().strip() for x in e}
            remote_command_args = e[1:] or ['']
            for arg in remote_command_args:
                args.processable.append(f"{e[0]} {arg}")

    return args


PipeStatus = namedtuple('PipeStatus', ('handler', 'is_remote'))


def setup_pipe_handler(cmdline_args):
    """Setup pipe handler, identify if the app is running as standalone or remote instance"""
    # any of the flags that change Picard's workflow significantly should trigger creation of a new instance
    if cmdline_args.stand_alone_instance:
        identifier = uuid4().hex
    else:
        if cmdline_args.config_file:
            identifier = blake2b(cmdline_args.config_file.encode('utf-8'), digest_size=16).hexdigest()
        else:
            identifier = 'main'
        if cmdline_args.no_plugins:
            identifier += '_NP'

    try:
        pipe_handler = pipe.Pipe(
            app_name=PICARD_APP_NAME,
            app_version=PICARD_FANCY_VERSION_STR,
            identifier=identifier,
            args=cmdline_args.processable,
        )
        is_remote = not pipe_handler.is_pipe_owner
    except pipe.PipeErrorNoPermission as err:
        log.error(err)
        pipe_handler = None
        is_remote = False

    return PipeStatus(handler=pipe_handler, is_remote=is_remote)


def setup_application():
    """Setup QApplication"""
    # Some libs (ie. Phonon) require those to be set
    QtWidgets.QApplication.setApplicationName(PICARD_APP_NAME)
    QtWidgets.QApplication.setOrganizationName(PICARD_ORG_NAME)
    QtWidgets.QApplication.setDesktopFileName(PICARD_APP_ID)

    # HighDpiScaleFactorRoundingPolicy is available since Qt 5.14. This is
    # required to support fractional scaling on Windows properly.
    # It causes issues without scaling on Linux, see https://tickets.metabrainz.org/browse/PICARD-1948
    if IS_WIN:
        QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    # Enable mnemonics on all platforms, even macOS
    QtGui.qt_set_sequence_auto_mnemonic(True)


def setup_dbus():
    """Setup DBus if available"""
    try:
        from PyQt6.QtDBus import QDBusConnection

        dbus = QDBusConnection.sessionBus()
        dbus.registerService(PICARD_APP_ID)
    except ImportError:
        pass


def main(localedir=None, autoupdate=True):
    """Main entry point to the program"""
    log.enable_default_handlers()
    setup_application()
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    cmdline_args = process_cmdline_args()

    if cmdline_args.long_version:
        print_message_and_exit(versions.as_string())
    if cmdline_args.version:
        print_message_and_exit(f"{PICARD_ORG_NAME} {PICARD_APP_NAME} {PICARD_FANCY_VERSION_STR}")
    if cmdline_args.remote_commands_help:
        print_help_for_commands()
    if cmdline_args.processable:
        log.info("Sending messages to main instance: %r", cmdline_args.processable)

    pipe_status = setup_pipe_handler(cmdline_args)

    # pipe has sent its args to existing one, doesn't need to start
    if pipe_status.is_remote:
        log.debug("No need for spawning a new instance, exiting...")
        sys.exit(0)

    setup_dbus()

    # GUI mode - full Tagger initialization
    tagger = Tagger(cmdline_args, localedir, autoupdate, pipe_handler=pipe_status.handler)

    tagger.startTimer(1000)
    exit_code = tagger.run()

    if tagger.pipe_handler.unexpected_removal:
        os._exit(exit_code)

    sys.exit(exit_code)
