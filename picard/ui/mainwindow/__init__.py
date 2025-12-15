# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2007 Nikolai Prokoschenko
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2008 Will
# Copyright (C) 2008-2010, 2015, 2018-2025 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 David Hilton
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013, 2015-2017 Wieland Hoffmann
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2013-2024 Laurent Monin
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2015 samithaj
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 Kartik Ohri
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018 virusMac
# Copyright (C) 2018, 2021-2023, 2025 Bob Swift
# Copyright (C) 2019 Timur Enikeev
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Petit Minion
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


from collections import namedtuple
from contextlib import suppress
from copy import deepcopy
import datetime
from functools import partial
import itertools
import os.path
from pathlib import Path

import yaml

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import (
    PICARD_APP_ID,
    log,
)
from picard.album import Album
from picard.browser import addrelease
from picard.cluster import (
    Cluster,
    FileList,
)
from picard.config import (
    SettingConfigSection,
    get_config,
)
from picard.const import PROGRAM_UPDATE_LEVELS
from picard.const.appdirs import sessions_folder
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.extension_points.plugin_tools_menu import (
    ext_point_plugin_tools_items,
    signaler,
)
from picard.file import File
from picard.i18n import (
    N_,
    gettext as _,
    ngettext,
)
from picard.options import (
    Option,
    get_option_title,
)
from picard.script import get_file_naming_script_presets
from picard.session.constants import SessionConstants
from picard.session.session_manager import load_session_from_path, save_session_to_path
from picard.track import Track
from picard.util import (
    IgnoreUpdatesContext,
    icontheme,
    iter_files_from_objects,
    iter_unique,
    open_local_path,
    reconnect,
    restore_method,
    sanitize_filename,
    thread,
    throttle,
    webbrowser2,
)
from picard.util.cdrom import (
    DISCID_NOT_LOADED_MESSAGE,
    discid,
    get_cdrom_drives,
)

from picard.ui import PreserveGeometry
from picard.ui.aboutdialog import AboutDialog
from picard.ui.coverartbox import CoverArtBox
from picard.ui.enums import MainAction
from picard.ui.filebrowser import FileBrowser
from picard.ui.filter import Filter
from picard.ui.infodialog import (
    AlbumInfoDialog,
    ClusterInfoDialog,
    FileInfoDialog,
    TrackInfoDialog,
)
from picard.ui.infostatus import InfoStatus
from picard.ui.itemviews import (
    BaseTreeView,
    MainPanel,
)
from picard.ui.logview import (
    HistoryView,
    LogView,
)
from picard.ui.mainwindow.actions import create_actions
from picard.ui.metadatabox import MetadataBox
from picard.ui.newuserdialog import NewUserDialog
from picard.ui.options.dialog import OptionsDialog
from picard.ui.passworddialog import (
    PasswordDialog,
    ProxyDialog,
)
from picard.ui.savewarningdialog import SaveWarningDialog
from picard.ui.scripteditor import ScriptEditorDialog
from picard.ui.scripteditor.examples import ScriptEditorExamples
from picard.ui.searchdialog.album import AlbumSearchDialog
from picard.ui.searchdialog.track import TrackSearchDialog
from picard.ui.statusindicator import (
    DesktopStatusIndicator,
    ProgressStatus,
)
from picard.ui.tagsfromfilenames import TagsFromFileNamesDialog
from picard.ui.util import (
    FileDialog,
    find_starting_directory,
    menu_builder,
    show_session_not_found_dialog,
)
from picard.ui.widgets.checkboxmenuitem import CheckboxMenuItem


SuspendWhileLoadingFuncs = namedtuple('SuspendWhileLoadingFuncs', ('on_enter', 'on_exit'))


class MainWindow(QtWidgets.QMainWindow, PreserveGeometry):
    defaultsize = QtCore.QSize(780, 560)
    selection_updated = QtCore.pyqtSignal(object)
    ready_for_display = QtCore.pyqtSignal()

    def __init__(self, parent=None, disable_player=False):
        super().__init__(parent=parent)
        self.actions = {}
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NativeWindow)
        self.__shown = False
        self.tagger = QtCore.QCoreApplication.instance()
        self._is_wayland = self.tagger.is_wayland
        self.selected_objects = []
        self.ignore_selection_changes = IgnoreUpdatesContext(on_exit=self.update_selection)

        self._suspend_while_loading_funcs = []
        self.suspend_while_loading = IgnoreUpdatesContext(
            on_first_enter=self.suspend_while_loading_enter,
            on_last_exit=self.suspend_while_loading_exit,
        )
        self.register_suspend_while_loading(
            on_enter=partial(self.set_sorting, sorting=False),
            on_exit=partial(self.set_sorting, sorting=True),
        )
        self.register_suspend_while_loading(
            on_enter=partial(self.set_filters, processing=False),
            on_exit=partial(self.set_filters, processing=True),
        )

        self.toolbar = None
        self.player = None
        self.status_indicators = []
        if DesktopStatusIndicator:
            self.ready_for_display.connect(self._setup_desktop_status_indicator)
        if not disable_player:
            from picard.ui.player import Player

            player = Player(self)
            if player.available:
                self.player = player
                self.player.error.connect(self._on_player_error)

        self.script_editor_dialog = None

        self._check_and_repair_naming_scripts()
        self._check_and_repair_profiles()

        self.setupUi()

        webservice_manager = self.tagger.webservice.manager
        webservice_manager.authenticationRequired.connect(self._show_password_dialog)
        webservice_manager.proxyAuthenticationRequired.connect(self._show_proxy_dialog)

    def register_suspend_while_loading(self, on_enter=None, on_exit=None):
        funcs = SuspendWhileLoadingFuncs(on_enter=on_enter, on_exit=on_exit)
        self._suspend_while_loading_funcs.append(funcs)

    def suspend_while_loading_enter(self):
        for func in self._suspend_while_loading_funcs:
            if func.on_enter:
                log.debug("enter, running: %r", func.on_enter)
                func.on_enter()

    def suspend_while_loading_exit(self):
        for func in self._suspend_while_loading_funcs:
            if func.on_exit:
                log.debug("exit, running: %r", func.on_exit)
                func.on_exit()

    def setupUi(self):
        self.setWindowTitle(_("MusicBrainz Picard"))
        icon = QtGui.QIcon()
        for size in (16, 24, 32, 48, 128, 256):
            icon.addFile(
                ":/images/{size}x{size}/{app_id}.png".format(size=size, app_id=PICARD_APP_ID), QtCore.QSize(size, size)
            )
        self.setWindowIcon(icon)

        self.show_close_window = IS_MACOS

        self._create_actions()
        self._create_statusbar()
        self._create_toolbar()
        self._create_menus()

        if IS_MACOS:
            self.setUnifiedTitleAndToolBarOnMac(True)

        main_layout = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        main_layout.setObjectName('main_window_bottom_splitter')
        main_layout.setChildrenCollapsible(False)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.panel = MainPanel(self, main_layout)
        self.panel.setObjectName('main_panel_splitter')
        self.file_browser = FileBrowser(parent=self.panel)
        if not self.action_is_checked(MainAction.SHOW_FILE_BROWSER):
            self.file_browser.hide()
        self.panel.insertWidget(0, self.file_browser)

        self.log_dialog = LogView(self)
        self.history_dialog = HistoryView(self)

        self.metadata_box = MetadataBox(parent=self)
        self.cover_art_box = CoverArtBox(parent=self)
        metadata_view_layout = QtWidgets.QHBoxLayout()
        metadata_view_layout.setContentsMargins(0, 0, 0, 0)
        metadata_view_layout.setSpacing(0)
        metadata_view_layout.addWidget(self.metadata_box, 1)
        metadata_view_layout.addWidget(self.cover_art_box, 0)
        self.metadata_view = QtWidgets.QWidget()
        self.metadata_view.setLayout(metadata_view_layout)

        self.show_metadata_view()
        self.show_cover_art()
        self.show_filter_bars()

        main_layout.addWidget(self.panel)
        main_layout.addWidget(self.metadata_view)
        self.setCentralWidget(main_layout)

        # accessibility
        self.set_tab_order()

        get_config().setting.setting_changed.connect(self.handle_settings_changed)
        get_config().profiles.setting_changed.connect(self.handle_profiles_changed)

        plugin_manager = self.tagger.get_plugin_manager()
        if plugin_manager:
            signaler.plugin_tools_updated.connect(self._make_plugin_tools_menu)
            plugin_manager.plugin_state_changed.connect(self._make_plugin_tools_menu)

    def handle_settings_changed(self, name, old_value, new_value):
        if name == 'rename_files':
            self.actions[MainAction.ENABLE_RENAMING].setChecked(new_value)
        elif name == 'move_files':
            self.actions[MainAction.ENABLE_MOVING].setChecked(new_value)
        elif name == 'enable_tag_saving':
            self.actions[MainAction.ENABLE_TAG_SAVING].setChecked(new_value)
        elif name in {'file_renaming_scripts', 'selected_file_naming_script_id'}:
            self._make_script_selector_menu()

        # Also update items in quick settings if needed
        config = get_config()
        if name in config.setting['quick_menu_items']:
            self._make_settings_selector_menu()

    def handle_profiles_changed(self, name, old_value, new_value):
        if name == SettingConfigSection.PROFILES_KEY:
            self._make_profile_selector_menu()

    def set_processing(self, processing=True):
        self.panel.set_processing(processing)

    def set_sorting(self, sorting=True):
        self.panel.set_sorting(sorting)

    def set_filters(self, processing=True):
        Filter.suspended = not processing

    def keyPressEvent(self, event):
        # On macOS Command+Backspace triggers the so called "Forward Delete".
        # It should be treated the same as the Delete button.
        is_forward_delete = (
            IS_MACOS
            and event.key() == QtCore.Qt.Key.Key_Backspace
            and event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier
        )
        if event.matches(QtGui.QKeySequence.StandardKey.Delete) or is_forward_delete:
            if self.metadata_box.hasFocus():
                self.metadata_box.remove_selected_tags()
            else:
                self.remove_selected_objects()
        elif event.matches(QtGui.QKeySequence.StandardKey.Find):
            self.search_edit.setFocus(QtCore.Qt.FocusReason.ShortcutFocusReason)
        else:
            super().keyPressEvent(event)

    def show(self):
        self.restoreWindowState()
        super().show()
        self.show_new_user_dialog()
        if self.tagger.autoupdate_enabled:
            self._auto_update_check()
        self.metadata_box.restore_state()

    def showEvent(self, event):
        if not self.__shown:
            self.ready_for_display.emit()
            self.__shown = True
        super().showEvent(event)

    def closeEvent(self, event):
        config = get_config()
        if config.setting['quit_confirmation'] and not self.show_quit_confirmation():
            event.ignore()
            return
        if self.player:
            config.persist['mediaplayer_playback_rate'] = self.player.playback_rate()
            config.persist['mediaplayer_volume'] = self.player.volume()
        self.saveWindowState()
        # Confirm loss of unsaved changes in script editor.
        if self.script_editor_dialog:
            if not self.script_editor_dialog.unsaved_changes_in_profile_confirmation():
                event.ignore()
                return
            else:
                # Silently close the script editor without displaying the confirmation a second time.
                self.script_editor_dialog.loading = True
        event.accept()

    def _setup_desktop_status_indicator(self):
        if DesktopStatusIndicator:
            self._register_status_indicator(DesktopStatusIndicator(self.windowHandle()))

    def _register_status_indicator(self, indicator):
        self.status_indicators.append(indicator)

    def show_quit_confirmation(self):
        unsaved_files = sum(a.get_num_unsaved_files() for a in self.tagger.albums.values())
        QMessageBox = QtWidgets.QMessageBox

        if unsaved_files > 0:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            msg.setWindowTitle(_("Unsaved Changes"))
            msg.setText(_("Are you sure you want to quit Picard?"))
            txt = (
                ngettext(
                    "There is %d unsaved file. Closing Picard will lose all unsaved changes.",
                    "There are %d unsaved files. Closing Picard will lose all unsaved changes.",
                    unsaved_files,
                )
                % unsaved_files
            )
            msg.setInformativeText(txt)
            cancel = msg.addButton(QMessageBox.StandardButton.Cancel)
            msg.setDefaultButton(cancel)
            msg.addButton(_("&Quit Picard"), QMessageBox.ButtonRole.YesRole)
            ret = msg.exec()

            if ret == QMessageBox.StandardButton.Cancel:
                return False

        return True

    def _has_session_content(self):
        """Return True if there is session content to save/close."""
        if self.tagger.files or self.tagger.albums:
            return True

        with suppress(AttributeError, TypeError):
            return bool(self.tagger.clusters and len(self.tagger.clusters) > 0)
        return False

    def show_close_session_confirmation(self):
        """Ask the user whether to save the session before closing.

        Returns
        -------
        bool
            True if closing should proceed, False to cancel.
        """
        # If there is nothing to save, proceed without asking
        if not self._has_session_content():
            return True

        QMessageBox = QtWidgets.QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        msg.setWindowTitle(_("Close Session"))
        msg.setText(_("Do you want to save the current session before continuing?"))
        msg.setInformativeText(_("Closing the session will clear all files, clusters and albums from the view."))
        cancel_btn = msg.addButton(QMessageBox.StandardButton.Cancel)
        save_btn = msg.addButton(_("&Save Session"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(_("Do&n't Save"), QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(save_btn)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == cancel_btn:
            return False
        if clicked == save_btn:
            # If saving fails or is cancelled, abort closing
            return self._save_session_to_known_path_or_prompt()
        # Don't Save
        return True

    def _save_session_to_known_path_or_prompt(self) -> bool:
        """Save session to last known session path if available; otherwise prompt.

        Returns
        -------
        bool
            True if saved successfully, False otherwise.
        """
        config = get_config()
        path = config.persist['last_session_path'] or ''
        if path:
            try:
                save_session_to_path(self.tagger, path)

                # Ensure the known path remains persisted explicitly
                config.persist['last_session_path'] = path
                self.set_statusbar_message(N_("Session saved to '%(path)s'"), {'path': path})
                self._add_to_recent_sessions(path)
            except (OSError, PermissionError, FileNotFoundError, ValueError, OverflowError) as e:
                QtWidgets.QMessageBox.critical(self, _("Failed to save session"), str(e))
                return False
            else:
                return True

        # Fallback to prompting for a path
        return bool(self.save_session_as())

    def saveWindowState(self):
        config = get_config()
        config.persist['window_state'] = self.saveState()
        is_maximized = bool(self.windowState() & QtCore.Qt.WindowState.WindowMaximized)
        self.save_geometry()
        config.persist['window_maximized'] = is_maximized
        config.persist['view_metadata_view'] = self.action_is_checked(MainAction.SHOW_METADATA_VIEW)
        config.persist['view_cover_art'] = self.action_is_checked(MainAction.SHOW_COVER_ART)
        config.persist['view_toolbar'] = self.action_is_checked(MainAction.SHOW_TOOLBAR)
        config.persist['view_filterbar'] = self.action_is_checked(MainAction.SHOW_FILTERBAR)
        config.persist['view_file_browser'] = self.action_is_checked(MainAction.SHOW_FILE_BROWSER)
        self.file_browser.save_state()
        self.panel.save_state()
        self.metadata_box.save_state()

    @restore_method
    def restoreWindowState(self):
        config = get_config()
        self.restoreState(config.persist['window_state'])
        self.restore_geometry()
        if config.persist['window_maximized']:
            self.setWindowState(QtCore.Qt.WindowState.WindowMaximized)
        splitters = config.persist['splitters_MainWindow']
        if splitters is None or 'main_window_bottom_splitter' not in splitters:
            self.centralWidget().setSizes([366, 194])
        self.file_browser.restore_state()

    def _create_statusbar(self):
        """Creates a new status bar."""
        self.statusBar().showMessage(_("Ready"))
        infostatus = InfoStatus(self)
        self._progress = infostatus.get_progress
        self.listening_label = QtWidgets.QLabel()
        self.listening_label.setStyleSheet("QLabel { margin: 0 4px 0 4px; }")
        self.listening_label.setVisible(False)
        self.listening_label.setToolTip(
            "<qt/>"
            + _(
                "Picard listens on this port to integrate with your browser. When "
                "you \"Search\" or \"Open in Browser\" from Picard, clicking the "
                "\"Tagger\" button on the web page loads the release into Picard."
            )
        )
        self.statusBar().addPermanentWidget(infostatus)
        self.statusBar().addPermanentWidget(self.listening_label)
        self.tagger.tagger_stats_changed.connect(self._update_statusbar_stats)
        self.tagger.listen_port_changed.connect(self._update_statusbar_listen_port)
        self._register_status_indicator(infostatus)
        self._update_statusbar_stats()

    @throttle(100)
    def _update_statusbar_stats(self):
        """Updates the status bar information."""
        progress_status = ProgressStatus(
            files=len(self.tagger.files),
            albums=len(self.tagger.albums),
            pending_files=File.num_pending_files,
            pending_requests=self.tagger.webservice.num_pending_web_requests,
            progress=self._progress(),
        )
        for indicator in self.status_indicators:
            indicator.update(progress_status)

    def _update_statusbar_listen_port(self, listen_port):
        if listen_port:
            self.listening_label.setVisible(True)
            self.listening_label.setText(_("Listening on port %(port)d") % {"port": listen_port})
        else:
            self.listening_label.setVisible(False)

    def set_statusbar_message(self, message, *args, **kwargs):
        """Set the status bar message.

        *args are passed to % operator, if args[0] is a mapping it is used for
        named place holders values
        >>> w.set_statusbar_message("File %(filename)s", {'filename': 'x.txt'})

        Keyword arguments:
        `echo` parameter defaults to `log.debug`, called before message is
        translated, it can be disabled passing None or replaced by ie.
        `log.error`. If None, skipped.

        `translate` is a method called on message before it is sent to history
        log and status bar, it defaults to `_()`. If None, skipped.

        `timeout` defines duration of the display in milliseconds

        `history` is a method called with translated message as argument, it
        defaults to `log.history_info`. If None, skipped.

        Empty messages are never passed to echo and history functions but they
        are sent to status bar (ie. to clear it).
        """

        def isdict(obj):
            return hasattr(obj, 'keys') and hasattr(obj, '__getitem__')

        echo = kwargs.get('echo', log.debug)
        translate = kwargs.get('translate', _)
        timeout = kwargs.get('timeout', 0)
        history = kwargs.get('history', log.history_info)
        if len(args) == 1 and isdict(args[0]):
            # named place holders
            mparms = args[0]
        else:
            # simple place holders, ensure compatibility
            mparms = args
        if message:
            if echo:
                echo(message % mparms)
            if translate:
                message = translate(message)
            message = message % mparms
            if history:
                history(message)
        thread.to_main(self.statusBar().showMessage, message, timeout)

    def _on_submit_acoustid(self):
        if self.tagger.use_acoustid:
            config = get_config()
            if not config.setting['acoustid_apikey']:
                msg = QtWidgets.QMessageBox(self)
                msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
                msg.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
                msg.setWindowTitle(_("AcoustID submission not configured"))
                msg.setText(_("You need to configure your AcoustID API key before you can submit fingerprints."))
                open_options = QtWidgets.QPushButton(
                    icontheme.lookup('preferences-desktop'), _("Open AcoustID options")
                )
                msg.addButton(QtWidgets.QMessageBox.StandardButton.Cancel)
                msg.addButton(open_options, QtWidgets.QMessageBox.ButtonRole.YesRole)
                msg.exec()
                if msg.clickedButton() == open_options:
                    self.show_options('fingerprinting')
            else:
                self.tagger.acoustidmanager.submit()

    def _create_actions(self):
        self.actions = dict(create_actions(self))

        self._create_cd_lookup_menu()

    def _create_cd_lookup_menu(self):
        menu = QtWidgets.QMenu(_("Lookup &CD…"))
        menu.setIcon(icontheme.lookup('media-optical'))
        menu.triggered.connect(self.tagger.lookup_cd)
        self.cd_lookup_menu = menu
        self._init_cd_lookup_menu()

    def _create_recent_sessions_menu(self):
        """Create and return the "Recent Sessions" submenu.

        The menu content is populated from the persisted recent sessions list.
        """
        self.recent_sessions_menu = QtWidgets.QMenu(_("Recent Sessions"))
        self.recent_sessions_menu.setIcon(icontheme.lookup('document-open-recent'))
        self._populate_recent_sessions_menu()
        return self.recent_sessions_menu

    def _get_recent_sessions(self):
        """Return the list of recent session paths from persistent config."""
        config = get_config()
        value = config.persist['recent_sessions']
        if isinstance(value, list):
            return [str(p) for p in value]
        return []

    def _set_recent_sessions(self, paths):
        """Persist the given list of recent session paths and refresh the menu."""
        config = get_config()
        config.persist['recent_sessions'] = list(paths)
        if hasattr(self, 'recent_sessions_menu') and isinstance(self.recent_sessions_menu, QtWidgets.QMenu):
            self._populate_recent_sessions_menu()

    def _add_to_recent_sessions(self, path):
        """Insert a path at the front of the recent sessions list, de-duplicated and capped."""
        if not path:
            return
        paths = self._get_recent_sessions()
        # De-duplicate while preserving order by removing existing entry first
        try:
            paths.remove(path)
        except ValueError:
            pass
        paths.insert(0, path)
        # Cap to configured maximum
        pruned = paths[: SessionConstants.RECENT_SESSIONS_MAX]
        self._set_recent_sessions(pruned)

    def clear_recent_sessions(self):
        """Clear all recent session entries from the persistent config."""
        self._set_recent_sessions([])
        self.set_statusbar_message(_("Recent sessions cleared"))

    def _remove_from_recent_sessions(self, path):
        """Remove a specific path from the recent sessions list."""
        if not path:
            return
        paths = self._get_recent_sessions()
        with suppress(ValueError):
            paths.remove(path)
            self._set_recent_sessions(paths)

    def _populate_recent_sessions_menu(self):
        """Populate the recent sessions submenu based on persisted list."""
        menu = self.recent_sessions_menu
        if not menu:
            return
        menu.clear()
        paths = self._get_recent_sessions()
        if not paths:
            empty = menu.addAction(_("Empty"))
            empty.setEnabled(False)
            menu.setEnabled(False)
            return
        menu.setEnabled(True)
        for index, path in enumerate(paths, start=1):
            path_obj = Path(path)
            label = f"{index}. {path_obj.name or path}"
            action = menu.addAction(label)
            action.setData(path)
            action.setToolTip(path)
            action.setStatusTip(path)
            action.triggered.connect(partial(self._load_session_from_recent, path))

        # Add separator and clear action at the bottom
        menu.addSeparator()
        clear_action = menu.addAction(_("Clear Recent Sessions"))
        clear_action.triggered.connect(self.clear_recent_sessions)

    def _init_cd_lookup_menu(self):
        if discid is None:
            log.warning("CDROM: discid library not found - Lookup CD functionality disabled")
            self.enable_action(MainAction.CD_LOOKUP, False)
            self.cd_lookup_menu.setEnabled(False)
        else:
            thread.run_task(get_cdrom_drives, self._update_cd_lookup_actions)

    def _update_cd_lookup_actions(self, result=None, error=None):
        if error:
            log.error("CDROM: Error on CD-ROM drive detection: %r", error)
        else:
            self.update_cd_lookup_drives(result)

    def update_cd_lookup_drives(self, drives):
        self.cd_lookup_menu.clear()
        self.enable_action(MainAction.CD_LOOKUP, discid is not None)
        if not drives:
            log.warning(DISCID_NOT_LOADED_MESSAGE)
        else:
            config = get_config()
            shortcut_drive = config.setting['cd_lookup_device'].split(",")[0] if len(drives) > 1 else ""
            for drive in drives:
                action = self.cd_lookup_menu.addAction(drive)
                action.setData(drive)
                if drive == shortcut_drive:
                    self._update_cd_lookup_default_action(action)
        self._set_cd_lookup_from_file_actions(drives)
        self._update_cd_lookup_button()

    def _set_cd_lookup_from_file_actions(self, drives):
        if self.cd_lookup_menu.actions():
            self.cd_lookup_menu.addSeparator()
        action = self.cd_lookup_menu.addAction(_("From CD ripper &log file…"))
        if not drives:
            self._update_cd_lookup_default_action(action)
        action.setData('logfile:eac')

    def _update_cd_lookup_default_action(self, action):
        if action:
            target = action.trigger
        else:
            target = self.tagger.lookup_cd
        reconnect(self.actions[MainAction.CD_LOOKUP].triggered, target)

    def _update_cd_lookup_button(self):
        button = self.toolbar.widgetForAction(self.actions[MainAction.CD_LOOKUP])
        enabled = bool(self.cd_lookup_menu.actions() and discid)
        self.cd_lookup_menu.setEnabled(enabled)
        if button:
            if enabled:
                button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.MenuButtonPopup)
                button.setMenu(self.cd_lookup_menu)
            else:
                button.setMenu(None)

    def toggle_rename_files(self, checked):
        config = get_config()
        config.setting['rename_files'] = checked
        self._update_script_editor_examples()

    def toggle_move_files(self, checked):
        config = get_config()
        config.setting['move_files'] = checked
        self._update_script_editor_examples()

    def toggle_tag_saving(self, checked):
        config = get_config()
        config.setting['enable_tag_saving'] = checked

    def _reset_option_menu_state(self):
        config = get_config()
        self.actions[MainAction.ENABLE_RENAMING].setChecked(config.setting['rename_files'])
        self.actions[MainAction.ENABLE_MOVING].setChecked(config.setting['move_files'])
        self.actions[MainAction.ENABLE_TAG_SAVING].setChecked(config.setting['enable_tag_saving'])
        self._make_script_selector_menu()
        self._init_cd_lookup_menu()
        self._make_settings_selector_menu()

    def _get_selected_or_unmatched_files(self):
        if self.selected_objects:
            files = list(iter_files_from_objects(self.selected_objects))
            if files:
                return files
        return self.tagger.unclustered_files.files

    def open_tags_from_filenames(self):
        files = self._get_selected_or_unmatched_files()
        if files:
            dialog = TagsFromFileNamesDialog(files, self)
            dialog.exec()

    def open_collection_in_browser(self):
        self.tagger.collection_lookup()

    def _create_menus(self):
        def add_menu(menu_title, *args):
            menu = self.menuBar().addMenu(menu_title)
            menu.setSeparatorsCollapsible(True)
            menu_builder(menu, self.actions, *args)

        add_menu(
            _("&File"),
            MainAction.ADD_DIRECTORY,
            MainAction.ADD_FILES,
            MainAction.CLOSE_WINDOW if self.show_close_window else None,
            '-',
            MainAction.PLAY_FILE,
            MainAction.OPEN_FOLDER,
            '-',
            MainAction.SAVE,
            MainAction.SUBMIT_ACOUSTID,
            '-',
            MainAction.LOAD_SESSION,
            # Recent Sessions submenu
            self._create_recent_sessions_menu(),
            MainAction.SAVE_SESSION,
            MainAction.SAVE_SESSION_AS,
            MainAction.NEW_SESSION,
            '-',
            MainAction.EXIT,
        )

        add_menu(
            _("&Edit"),
            MainAction.CUT,
            MainAction.PASTE,
            '-',
            MainAction.VIEW_INFO,
            MainAction.REMOVE,
        )

        add_menu(
            _("&View"),
            MainAction.SHOW_FILE_BROWSER,
            MainAction.SHOW_METADATA_VIEW,
            MainAction.SHOW_COVER_ART,
            '-',
            MainAction.SHOW_TOOLBAR,
            MainAction.SEARCH_TOOLBAR_TOGGLE,
            MainAction.SHOW_FILTERBAR,
            MainAction.PLAYER_TOOLBAR_TOGGLE if self.player else None,
        )

        self.script_quick_selector_menu = QtWidgets.QMenu(_("&Select file naming script"))
        self.script_quick_selector_menu.setIcon(icontheme.lookup('document-open'))
        self._make_script_selector_menu()

        self.profile_quick_selector_menu = QtWidgets.QMenu(_("&Enable/disable profiles"))
        self._make_profile_selector_menu()

        self.settings_quick_selector_menu = QtWidgets.QMenu(_("&Quick settings"))
        self._make_settings_selector_menu()

        add_menu(
            _("&Options"),
            MainAction.ENABLE_RENAMING,
            MainAction.ENABLE_MOVING,
            MainAction.ENABLE_TAG_SAVING,
            '-',
            self.script_quick_selector_menu,
            MainAction.SHOW_SCRIPT_EDITOR,
            '-',
            self.profile_quick_selector_menu,
            '-',
            self.settings_quick_selector_menu,
            '-',
            MainAction.OPTIONS,
        )

        add_menu(
            _("&Tools"),
            MainAction.REFRESH,
            self.cd_lookup_menu,
            MainAction.AUTOTAG,
            MainAction.ANALYZE,
            MainAction.CLUSTER,
            MainAction.BROWSER_LOOKUP,
            MainAction.SIMILAR_ITEMS_SEARCH,
            MainAction.ALBUM_OTHER_VERSIONS,
            '-',
            MainAction.GENERATE_FINGERPRINTS,
            MainAction.TAGS_FROM_FILENAMES,
            MainAction.OPEN_COLLECTION_IN_BROWSER,
        )

        self.plugin_tools_menu = self.menuBar().addMenu(_("&Plugin Tools"))
        self.plugin_tools_menu.menuAction().setVisible(False)
        self._make_plugin_tools_menu()

        self.menuBar().addSeparator()

        add_menu(
            _("&Help"),
            MainAction.HELP,
            '-',
            MainAction.VIEW_HISTORY,
            '-',
            MainAction.CHECK_UPDATE if self.tagger.autoupdate_enabled else None,
            '-',
            MainAction.SUPPORT_FORUM,
            MainAction.REPORT_BUG,
            MainAction.VIEW_LOG,
            '-',
            MainAction.DONATE,
            MainAction.ABOUT,
        )

    def update_toolbar_style(self):
        config = get_config()
        style = QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly
        if config.setting['toolbar_show_labels']:
            style = QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        self.toolbar.setToolButtonStyle(style)
        if self.player:
            self.player.toolbar.setToolButtonStyle(style)

    def _create_toolbar(self):
        self._create_search_toolbar()
        if self.player:
            self._create_player_toolbar()
        self.create_action_toolbar()
        self.update_toolbar_style()

    def create_action_toolbar(self):
        if self.toolbar:
            self.toolbar.clear()
            self.removeToolBar(self.toolbar)
        self.toolbar = toolbar = QtWidgets.QToolBar(_("Actions"))
        self.insertToolBar(self.search_toolbar, self.toolbar)
        toolbar.setObjectName('main_toolbar')
        if self._is_wayland:
            toolbar.setFloatable(False)  # https://bugreports.qt.io/browse/QTBUG-92191
        if IS_MACOS:
            toolbar.setMovable(False)

        def add_toolbar_action(action_id):
            action = self.actions[action_id]
            toolbar.addAction(action)
            widget = toolbar.widgetForAction(action)
            widget.setFocusPolicy(QtCore.Qt.FocusPolicy.TabFocus)
            widget.setAttribute(QtCore.Qt.WidgetAttribute.WA_MacShowFocusRect)

        config = get_config()
        for action_name in config.setting['toolbar_layout']:
            if action_name in {'-', 'separator'}:
                toolbar.addSeparator()
            else:
                try:
                    action_id = MainAction(action_name)
                    add_toolbar_action(action_id)
                    if action_id == MainAction.CD_LOOKUP:
                        self._update_cd_lookup_button()
                except (ValueError, KeyError) as e:
                    log.warning("Warning: Unknown action name '%s' found in config. Ignored. %s", action_name, e)
        self.show_toolbar()

    def _create_player_toolbar(self):
        """Create a toolbar with internal player control elements"""
        toolbar = self.player.create_toolbar()
        self.addToolBar(QtCore.Qt.ToolBarArea.BottomToolBarArea, toolbar)
        if self._is_wayland:
            toolbar.setFloatable(False)  # https://bugreports.qt.io/browse/QTBUG-92191
        self.actions[MainAction.PLAYER_TOOLBAR_TOGGLE] = toolbar.toggleViewAction()
        toolbar.hide()  # Hide by default

    def _create_search_toolbar(self):
        config = get_config()
        self.search_toolbar = toolbar = self.addToolBar(_("Search"))
        self.actions[MainAction.SEARCH_TOOLBAR_TOGGLE] = self.search_toolbar.toggleViewAction()
        toolbar.setObjectName('search_toolbar')
        if self._is_wayland:
            toolbar.setFloatable(False)  # https://bugreports.qt.io/browse/QTBUG-92191
        if IS_MACOS:
            self.search_toolbar.setMovable(False)

        search_panel = QtWidgets.QWidget(toolbar)
        hbox = QtWidgets.QHBoxLayout(search_panel)
        self.search_combo = QtWidgets.QComboBox(search_panel)
        self.search_combo.addItem(_("Album"), 'album')
        self.search_combo.addItem(_("Artist"), 'artist')
        self.search_combo.addItem(_("Track"), 'track')
        hbox.addWidget(self.search_combo, 0)
        self.search_edit = QtWidgets.QLineEdit(search_panel)
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.returnPressed.connect(self._trigger_search_action)
        self.search_edit.textChanged.connect(self._toggle_search)
        hbox.addWidget(self.search_edit, 0)
        self.search_button = QtWidgets.QToolButton(search_panel)
        self.search_button.setAutoRaise(True)
        self.search_button.setDefaultAction(self.actions[MainAction.SEARCH])
        self.search_button.setIconSize(QtCore.QSize(22, 22))
        self.search_button.setAttribute(QtCore.Qt.WidgetAttribute.WA_MacShowFocusRect)

        # search button contextual menu, shortcut to toggle search options
        def search_button_menu(position):
            menu = QtWidgets.QMenu()
            opts = {
                'use_adv_search_syntax': N_("&Advanced search"),
                'builtin_search': N_("&Builtin search"),
            }

            def toggle_opt(opt, checked):
                config.setting[opt] = checked

            for opt, label in opts.items():
                action = QtGui.QAction(_(label), menu)
                action.setCheckable(True)
                action.setChecked(config.setting[opt])
                action.triggered.connect(partial(toggle_opt, opt))
                menu.addAction(action)
            menu.exec(self.search_button.mapToGlobal(position))

        self.search_button.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_button.customContextMenuRequested.connect(search_button_menu)
        hbox.addWidget(self.search_button)
        toolbar.addWidget(search_panel)

    def set_tab_order(self):
        tab_order = self.setTabOrder
        prev_action = None
        current_action = None
        # Setting toolbar widget tab-orders for accessibility
        config = get_config()
        for action_name in config.setting['toolbar_layout']:
            if action_name not in {'-', 'separator'}:
                try:
                    action_id = MainAction(action_name)
                    action = self.actions[action_id]
                    current_action = self.toolbar.widgetForAction(action)
                except (ValueError, KeyError) as e:
                    log.debug("Warning: Unknown action name '%s' found in config. Ignored. %s", action_name, e)

            if prev_action is not None and prev_action != current_action:
                tab_order(prev_action, current_action)

            prev_action = current_action

        tab_order(prev_action, self.search_combo)
        tab_order(self.search_combo, self.search_edit)
        tab_order(self.search_edit, self.search_button)
        # Panels
        tab_order(self.search_button, self.file_browser)
        self.panel.tab_order(tab_order, self.file_browser, self.metadata_box)

    def _toggle_search(self):
        """Enable/disable the 'Search' action."""
        self.enable_action(MainAction.SEARCH, self.search_edit.text())

    def _trigger_search_action(self):
        action = self.actions[MainAction.SEARCH]
        if action.isEnabled():
            action.trigger()

    def _search_mbid_found(self, entity, mbid):
        self.search_edit.setText('%s:%s' % (entity, mbid))

    def search(self):
        """Search for album, artist or track on the MusicBrainz website."""
        text = self.search_edit.text()
        entity = self.search_combo.itemData(self.search_combo.currentIndex())
        config = get_config()
        self.tagger.search(
            text,
            entity,
            config.setting['use_adv_search_syntax'],
            mbid_matched_callback=self._search_mbid_found,
        )

    def add_files(self):
        """Add files to the tagger."""
        current_directory = find_starting_directory()
        formats = []
        extensions = []
        for exts, name in self.tagger.format_registry.supported_formats():
            exts = ["*" + e.lower() for e in exts]
            if not exts:
                continue
            if not IS_MACOS and not IS_WIN:
                # Also consider upper case extensions
                # macOS and Windows usually support case sensitive file names. Furthermore on both systems
                # the file dialog filters list all extensions we provide, which becomes a bit long when we give the
                # full list twice. Hence only do this trick on other operating systems.
                exts.extend([e.upper() for e in exts])
            exts.sort()
            formats.append("%s (%s)" % (name, " ".join(exts)))
            extensions.extend(exts)
        formats.sort()
        extensions.sort()
        formats.insert(0, _("All supported formats") + " (%s)" % " ".join(extensions))
        formats.insert(1, _("All files") + " (*)")
        files, _filter = FileDialog.getOpenFileNames(
            parent=self,
            directory=current_directory,
            filter=";;".join(formats),
        )
        if files:
            config = get_config()
            config.persist['current_directory'] = os.path.dirname(files[0])
            self.tagger.add_files(files)

    def add_directory(self):
        """Add directory to the tagger."""
        current_directory = find_starting_directory()

        dir_list = []
        config = get_config()
        if not config.setting['allow_multi_dirs_selection']:
            directory = FileDialog.getExistingDirectory(
                parent=self,
                directory=current_directory,
            )
            if directory:
                dir_list.append(directory)
        else:
            dir_list = FileDialog.getMultipleDirectories(
                parent=self,
                directory=current_directory,
            )

        dir_count = len(dir_list)
        if dir_count:
            parent = os.path.dirname(dir_list[0]) if dir_count > 1 else dir_list[0]
            config.persist['current_directory'] = parent
            if dir_count > 1:
                self.set_statusbar_message(
                    N_("Adding multiple directories from '%(directory)s' …"),
                    {'directory': parent},
                )
            else:
                self.set_statusbar_message(
                    N_("Adding directory: '%(directory)s' …"),
                    {'directory': dir_list[0]},
                )

            self.tagger.add_paths(dir_list)

    def close_active_window(self):
        self.tagger.activeWindow().close()

    def show_about(self):
        return AboutDialog.show_instance(self)

    def show_options(self, page=None):
        options_dialog = OptionsDialog.show_instance(page, self)
        options_dialog.finished.connect(self._options_closed)
        if self.script_editor_dialog is not None:
            # Disable signal processing to avoid saving changes not processed with "Make It So!"
            for signal in self.script_editor_signals:
                signal.disconnect()

        return options_dialog

    def _options_closed(self):
        if self.script_editor_dialog is not None:
            self.open_file_naming_script_editor()
            self.script_editor_dialog.show()
        else:
            self.enable_action(MainAction.SHOW_SCRIPT_EDITOR, True)
        self._make_profile_selector_menu()
        self._make_script_selector_menu()
        self._make_settings_selector_menu()

    def show_help(self):
        webbrowser2.open('documentation')

    def _show_log_dialog(self, dialog):
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def show_log(self):
        self._show_log_dialog(self.log_dialog)

    def show_history(self):
        self._show_log_dialog(self.history_dialog)

    def open_bug_report(self):
        webbrowser2.open('troubleshooting')

    def open_support_forum(self):
        webbrowser2.open('forum')

    def open_donation_page(self):
        webbrowser2.open('donate')

    def save(self):
        """Tell the tagger to save the selected objects."""
        config = get_config()
        if config.setting['file_save_warning']:
            count = len(self.tagger.get_files_from_objects(self.selected_objects))
            msg = SaveWarningDialog(self, count)
            proceed_with_save, disable_warning = msg.show()
            config.setting['file_save_warning'] = not disable_warning
        else:
            proceed_with_save = True
        if proceed_with_save:
            self.tagger.save(self.selected_objects)

    def _get_default_session_filename_from_metadata(self) -> str | None:
        """Gets a default session filename based on the first track's artist metadata.

        Returns
        -------
        str | None
            A sanitized artist name to use as a default filename, or None if no artist is found.
        """
        artist_tags = (
            'artist',
            'albumartist',
            'artists',
            'albumartists',
        )

        for file in self.tagger.iter_all_files():
            metadata = file.metadata
            for tag in artist_tags:
                artist_value = metadata.get(tag)

                if artist_value and str(artist_value).strip():
                    artist_name = str(artist_value).split(',')[0].strip()

                    if artist_name:
                        return sanitize_filename(artist_name, repl="_", win_compat=True)

        return None

    def _get_timestamped_session_filename(self) -> str:
        """Generate a timestamped session filename.

        Returns
        -------
        str
            Session filename with format 'sessions_yyyyMMddHHmmss'.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return f"session_{timestamp}"

    def quick_save_session(self) -> bool:
        """Save to known path or delegate to Save As if unknown.

        Returns
        -------
        bool
            True on success, False otherwise.
        """
        return self._save_session_to_known_path_or_prompt()

    def save_session_as(self) -> bool:
        """Always prompt for a session file path and save there.

        When there is no known last session path, suggest a default filename
        based on current content.

        Returns
        -------
        bool
            True on success, False otherwise.
        """
        config = get_config()

        # Use known path's parent directory if available, otherwise fall back to sessions folder
        known_path = config.persist['last_session_path'] or ''
        if known_path:
            start_dir = Path(known_path).parent
        else:
            start_dir = sessions_folder()

        # Use default filename only when path is not known
        default_name = self._get_default_session_filename_from_metadata() or self._get_timestamped_session_filename()
        default_filename = f"{default_name}{SessionConstants.SESSION_FILE_EXTENSION}"
        start_dir = Path(start_dir) / default_filename

        path, _filter = FileDialog.getSaveFileName(
            parent=self,
            directory=str(start_dir),
            filter=(
                _("MusicBrainz Picard Session (%s);;All files (*)") % ("*" + SessionConstants.SESSION_FILE_EXTENSION)
            ),
        )
        if path:
            try:
                save_session_to_path(self.tagger, path)
                config.persist['last_session_path'] = path
            except (OSError, PermissionError, FileNotFoundError, ValueError, OverflowError) as e:
                QtWidgets.QMessageBox.critical(self, _("Failed to save session"), str(e))
                return False
            else:
                self.set_statusbar_message(N_("Session saved to '%(path)s'"), {'path': path})
                self._add_to_recent_sessions(path)
                return True
        return False

    def load_session(self):
        # Ask whether to save/close current session before loading a new one
        if not self.show_close_session_confirmation():
            return

        config = get_config()

        last_session_path = config.persist['last_session_path'] or ''
        if last_session_path:
            start_dir = Path(str(last_session_path)).parent
        else:
            start_dir = sessions_folder()
        path, _filter = FileDialog.getOpenFileName(
            parent=self,
            directory=str(start_dir),
            filter=(
                _("MusicBrainz Picard Session (%s);;All files (*)") % ("*" + SessionConstants.SESSION_FILE_EXTENSION)
            ),
        )
        if path:
            # Initial progress feedback before heavy load
            self.set_statusbar_message(N_("Loading session from '%(path)s' …"), {'path': path})
            try:
                load_session_from_path(self.tagger, path)
            except FileNotFoundError:
                show_session_not_found_dialog(self, path)
                return
            except (OSError, PermissionError, yaml.YAMLError, KeyError) as e:
                log.debug(f"Error loading session from {path}: {e}")
                QtWidgets.QMessageBox.critical(
                    self,
                    _("Failed to load session"),
                    _("Could not load session from %(path)s:\n\n%(error)s") % {"path": str(path), "error": str(e)},
                )
                return
            else:
                config.persist['last_session_path'] = path
                self.set_statusbar_message(N_("Session loaded from '%(path)s'"), {'path': path})
                # Track in recent sessions
                self._add_to_recent_sessions(path)

    def _load_session_from_recent(self, path):
        # Ask whether to save/close current session before loading a new one
        if not self.show_close_session_confirmation():
            return

        self.set_statusbar_message(N_("Loading session from '%(path)s' …"), {'path': path})
        try:
            load_session_from_path(self.tagger, path)
        except FileNotFoundError:
            show_session_not_found_dialog(self, path)
            self._remove_from_recent_sessions(path)
            return
        except (OSError, PermissionError, yaml.YAMLError, KeyError) as e:
            log.debug(f"Error loading session from {path}: {e}")
            QtWidgets.QMessageBox.critical(
                self,
                _("Failed to load session"),
                _("Could not load session from %(path)s:\n\n%(error)s") % {"path": str(path), "error": str(e)},
            )
            return
        else:
            config = get_config()
            config.persist['last_session_path'] = path
            self.set_statusbar_message(N_("Session loaded from '%(path)s'"), {'path': path})
            self._add_to_recent_sessions(path)

    def close_session(self):
        # Use dedicated confirmation for closing sessions (save / don't save / cancel)
        if not self.show_close_session_confirmation():
            return
        # Clear current state
        self.tagger.clear_session()
        # Reset last_session_path so subsequent saves prompt for a new path
        config = get_config()
        config.persist['last_session_path'] = ''

    def remove_selected_objects(self):
        """Tell the tagger to remove the selected objects."""
        self.panel.remove(self.selected_objects)

    def analyze(self):
        def callback(fingerprinting_system):
            if fingerprinting_system:
                self.tagger.analyze(self.selected_objects)

        self._ensure_fingerprinting_configured(callback)

    def generate_fingerprints(self):
        def callback(fingerprinting_system):
            if fingerprinting_system:
                self.tagger.generate_fingerprints(self.selected_objects)

        self._ensure_fingerprinting_configured(callback)

    def play_file(self):
        for file in iter_files_from_objects(self.selected_objects):
            open_local_path(file.filename)

    def _on_player_error(self, error, msg):
        self.set_statusbar_message(msg, echo=log.warning, translate=None)

    def open_folder(self):
        folders = iter_unique(os.path.dirname(f.filename) for f in iter_files_from_objects(self.selected_objects))
        for folder in folders:
            open_local_path(folder)

    def _ensure_fingerprinting_configured(self, callback):
        config = get_config()

        if not config.setting['fingerprinting_system']:
            if self._show_analyze_settings_info():

                def on_finished(result):
                    callback(config.setting['fingerprinting_system'])

                dialog = self.show_options('fingerprinting')
                dialog.finished.connect(on_finished)
        else:
            callback(config.setting['fingerprinting_system'])

    def _show_analyze_settings_info(self):
        ret = QtWidgets.QMessageBox.question(
            self,
            _("Configuration Required"),
            _("Audio fingerprinting is not yet configured. Would you like to configure it now?"),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes,
        )
        return ret == QtWidgets.QMessageBox.StandardButton.Yes

    def _get_first_obj_with_type(self, type):
        for obj in self.selected_objects:
            if isinstance(obj, type):
                return obj
        return None

    def show_similar_items_search(self):
        obj = self._get_first_obj_with_type(Cluster)
        if obj:
            self.show_more_albums()
        else:
            self.show_more_tracks()

    def show_more_tracks(self):
        if not self.selected_objects:
            return
        obj = self.selected_objects[0]
        if isinstance(obj, Track) and obj.files:
            obj = obj.files[0]
        if not isinstance(obj, File):
            log.debug("show_more_tracks expected a File, got %r", obj)
            return
        dialog = TrackSearchDialog(self, force_advanced_search=True)
        dialog.show_similar_tracks(obj)
        dialog.exec()

    def show_more_albums(self):
        obj = self._get_first_obj_with_type(Cluster)
        if not obj:
            log.debug("show_more_albums expected a Cluster, got %r", obj)
            return
        dialog = AlbumSearchDialog(self, force_advanced_search=True)
        dialog.show_similar_albums(obj)
        dialog.exec()

    def show_album_other_versions(self):
        obj = self._get_first_obj_with_type(Album)
        if obj and obj.release_group:
            AlbumSearchDialog.show_releasegroup_search(obj.release_group.id, obj)

    def view_info(self, default_tab=0):
        try:
            selected = self.selected_objects[0]
        except IndexError:
            return
        if isinstance(selected, Album):
            dialog_class = AlbumInfoDialog
        elif isinstance(selected, Cluster):
            dialog_class = ClusterInfoDialog
        elif isinstance(selected, Track):
            dialog_class = TrackInfoDialog
        else:
            try:
                selected = next(iter_files_from_objects(self.selected_objects))
            except StopIteration:
                return
            dialog_class = FileInfoDialog
        dialog = dialog_class(selected, self)
        dialog.ui.tabWidget.setCurrentIndex(default_tab)
        dialog.exec()

    def cluster(self):
        # Cluster all selected unclustered files. If there are no selected
        # unclustered files cluster all unclustered files.
        files = (
            f for f in iter_files_from_objects(self.selected_objects) if f.parent_item == self.tagger.unclustered_files
        )
        try:
            file = next(files)
        except StopIteration:
            files = self.tagger.unclustered_files.files
        else:
            files = itertools.chain([file], files)
        self.tagger.cluster(files, self._cluster_finished)

    def _cluster_finished(self):
        self.panel.update_current_view()
        # Select clusters if no other item or only empty unclustered files item is selected
        if not self.selected_objects or (
            len(self.selected_objects) == 1
            and self.tagger.unclustered_files in self.selected_objects
            and not self.tagger.unclustered_files.files
        ):
            self.panel.select_object(self.tagger.clusters)
        self._update_actions()

    def refresh(self):
        self.tagger.refresh(self.selected_objects)

    def browser_lookup(self):
        if not self.selected_objects:
            return
        self.tagger.browser_lookup(self.selected_objects[0])

    def submit_cluster(self):
        if self.selected_objects and self._check_add_release():
            for obj in self.selected_objects:
                if isinstance(obj, Cluster):
                    addrelease.submit_cluster(obj)

    def submit_file(self, as_release=False):
        if self.selected_objects and self._check_add_release():
            for file in iter_files_from_objects(self.selected_objects):
                addrelease.submit_file(file, as_release=as_release)

    def _check_add_release(self):
        if addrelease.is_enabled():
            return True
        ret = QtWidgets.QMessageBox.question(
            self,
            _("Browser integration not enabled"),
            _(
                "Submitting releases to MusicBrainz requires the browser integration to be enabled. Do you want to enable the browser integration now?"
            ),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes,
        )
        if ret == QtWidgets.QMessageBox.StandardButton.Yes:
            config = get_config()
            config.setting['browser_integration'] = True
            self.tagger.update_browser_integration()
            if addrelease.is_enabled():
                return True
            else:
                # Something went wrong, let the user configure browser integration manually
                self.show_options('network')
                return False
        else:
            return False

    @throttle(100)
    def _update_actions(self):
        can_remove = False
        can_save = False
        can_analyze = False
        can_refresh = False
        can_autotag = False
        can_submit = False
        single = self.selected_objects[0] if len(self.selected_objects) == 1 else None
        can_view_info = bool(single and single.can_view_info)
        can_browser_lookup = bool(single and single.can_browser_lookup)
        is_file = bool(single and isinstance(single, (File, Track)))
        is_album = bool(single and isinstance(single, Album))
        is_cluster = bool(single and isinstance(single, Cluster) and not single.special)

        if not self.selected_objects:
            have_objects = have_files = False
        else:
            have_objects = True
            try:
                next(iter_files_from_objects(self.selected_objects))
                have_files = True
            except StopIteration:
                have_files = False
            for obj in self.selected_objects:
                if obj is None:
                    continue
                # using x = x or obj.x() form prevents calling function
                # if x is already True
                can_analyze = can_analyze or obj.can_analyze
                can_autotag = can_autotag or obj.can_autotag
                can_refresh = can_refresh or obj.can_refresh
                can_remove = can_remove or obj.can_remove
                can_save = can_save or obj.can_save
                can_submit = can_submit or obj.can_submit
                # Skip further loops if all values now True.
                if can_analyze and can_autotag and can_refresh and can_remove and can_save and can_submit:
                    break

        self.enable_action(MainAction.REMOVE, can_remove)
        self.enable_action(MainAction.SAVE, can_save)
        self.enable_action(MainAction.VIEW_INFO, can_view_info)
        self.enable_action(MainAction.ANALYZE, can_analyze)
        self.enable_action(MainAction.GENERATE_FINGERPRINTS, have_files)
        self.enable_action(MainAction.REFRESH, can_refresh)
        self.enable_action(MainAction.AUTOTAG, can_autotag)
        self.enable_action(MainAction.BROWSER_LOOKUP, can_browser_lookup)
        self.enable_action(MainAction.PLAY_FILE, have_files)
        self.enable_action(MainAction.OPEN_FOLDER, have_files)
        self.enable_action(MainAction.CUT, have_objects)
        self.enable_action(MainAction.SUBMIT_CLUSTER, can_submit)
        self.enable_action(MainAction.SUBMIT_FILE_AS_RECORDING, have_files)
        self.enable_action(MainAction.SUBMIT_FILE_AS_RELEASE, have_files)
        self.enable_action(MainAction.TAGS_FROM_FILENAMES, self._get_selected_or_unmatched_files())
        self.enable_action(MainAction.SIMILAR_ITEMS_SEARCH, is_file or is_cluster)
        self.enable_action(MainAction.TRACK_SEARCH, is_file)
        self.enable_action(MainAction.ALBUM_SEARCH, is_cluster)
        self.enable_action(MainAction.ALBUM_OTHER_VERSIONS, is_album)

    def enable_action(self, action_id, enabled):
        if self.actions[action_id]:
            self.actions[action_id].setEnabled(bool(enabled))

    def update_selection(self, objects=None, new_selection=True, drop_album_caches=False):
        if self.ignore_selection_changes:
            return

        if objects is not None:
            self.selected_objects = objects
        else:
            objects = self.selected_objects

        self._update_actions()

        obj = None

        # Clear any existing status bar messages
        self.set_statusbar_message("")

        if self.player:
            self.player.set_objects(self.selected_objects)

        metadata_visible = self.metadata_view.isVisible()
        coverart_visible = metadata_visible and self.cover_art_box.isVisible()

        if len(objects) == 1:
            obj = list(objects)[0]
            if isinstance(obj, File):
                if obj.state == File.State.ERROR:
                    msg = N_("%(filename)s (error: %(error)s)")
                    mparms = {
                        'filename': obj.filename,
                        'error': obj.errors[0] if obj.errors else '',
                    }
                else:
                    msg = N_("%(filename)s")
                    mparms = {
                        'filename': obj.filename,
                    }
                self.set_statusbar_message(msg, mparms, echo=None, history=None)
            elif isinstance(obj, Track):
                if obj.num_linked_files == 1:
                    file = obj.files[0]
                    if file.has_error():
                        msg = N_("%(filename)s (%(similarity)d%%) (error: %(error)s)")
                        mparms = {
                            'filename': file.filename,
                            'similarity': file.similarity * 100,
                            'error': file.errors[0] if file.errors else '',
                        }
                    else:
                        msg = N_("%(filename)s (%(similarity)d%%)")
                        mparms = {
                            'filename': file.filename,
                            'similarity': file.similarity * 100,
                        }
                    self.set_statusbar_message(msg, mparms, echo=None, history=None)
        elif coverart_visible and new_selection:
            # Create a temporary file list which allows changing cover art for all selected files
            files = list(iter_files_from_objects(objects))
            obj = FileList(files)

        if coverart_visible and new_selection:
            self.cover_art_box.set_item(obj)

        if metadata_visible:
            if new_selection:
                self.metadata_box.selection_dirty = True
            self.metadata_box.update(drop_album_caches=drop_album_caches)
        self.selection_updated.emit(objects)
        self._update_script_editor_example_files()

    def refresh_metadatabox(self):
        self.tagger.window.metadata_box.selection_dirty = True
        self.tagger.window.metadata_box.update()

    def action_is_checked(self, action_id):
        return self.actions[action_id].isChecked()

    def show_metadata_view(self):
        """Show/hide the metadata view (including the cover art box)."""
        show = self.action_is_checked(MainAction.SHOW_METADATA_VIEW)
        self.metadata_view.setVisible(show)
        self.enable_action(MainAction.SHOW_COVER_ART, show)
        if show:
            self.update_selection()

    def show_cover_art(self):
        """Show/hide the cover art box."""
        show = self.action_is_checked(MainAction.SHOW_COVER_ART)
        self.cover_art_box.setVisible(show)
        if show:
            self.update_selection()

    def show_toolbar(self):
        """Show/hide the Action toolbar."""
        if self.action_is_checked(MainAction.SHOW_TOOLBAR):
            self.toolbar.show()
        else:
            self.toolbar.hide()

    def show_file_browser(self):
        """Show/hide the file browser."""
        if self.action_is_checked(MainAction.SHOW_FILE_BROWSER):
            sizes = self.panel.sizes()
            if sizes[0] == 0:
                sizes[0] = sum(sizes) // 4
                self.panel.setSizes(sizes)
            self.file_browser.show()
        else:
            self.file_browser.hide()

    def _show_password_dialog(self, reply, authenticator):
        config = get_config()
        if reply.url().host() == config.setting['server_host']:
            ret = QtWidgets.QMessageBox.question(
                self,
                _("Authentication Required"),
                _(
                    "Picard needs authorization to access your personal data on the MusicBrainz server. Would you like to log in now?"
                ),
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.Yes,
            )
            if ret == QtWidgets.QMessageBox.StandardButton.Yes:
                self.tagger.mb_login(self._on_mb_login_finished)
        else:
            dialog = PasswordDialog(authenticator, reply, parent=self)
            dialog.exec()

    def _on_mb_login_finished(self, successful, error_msg):
        if successful:
            log.debug("MusicBrainz authentication finished successfully")
        else:
            log.info("MusicBrainz authentication failed: %s", error_msg)
            QtWidgets.QMessageBox.critical(
                self,
                _("Authentication failed"),
                _("Login failed: %s") % error_msg,
            )

    def _show_proxy_dialog(self, proxy, authenticator):
        dialog = ProxyDialog(authenticator, proxy, parent=self)
        dialog.exec()

    def autotag(self):
        self.tagger.autotag(self.selected_objects)

    def copy_files(self, objects):
        mimeData = QtCore.QMimeData()
        mimeData.setUrls(QtCore.QUrl.fromLocalFile(f.filename) for f in iter_files_from_objects(objects))
        self.tagger.clipboard().setMimeData(mimeData)

    def paste_files(self, target):
        mimeData = self.tagger.clipboard().mimeData()
        if mimeData.hasUrls():
            BaseTreeView.drop_urls(mimeData.urls(), target)

    def cut(self):
        self.copy_files(self.selected_objects)
        self.enable_action(MainAction.PASTE, self.selected_objects)

    def paste(self):
        selected_objects = self.selected_objects
        if not selected_objects:
            target = self.tagger.unclustered_files
        else:
            target = selected_objects[0]
        self.paste_files(target)
        self.enable_action(MainAction.PASTE, False)

    def do_update_check(self):
        self._check_for_update(True)

    def _auto_update_check(self):
        config = get_config()
        check_for_updates = config.setting['check_for_updates']
        update_check_days = config.setting['update_check_days']
        last_update_check = config.persist['last_update_check']
        update_level = config.setting['update_level']
        today = datetime.date.today().toordinal()
        do_auto_update_check = (
            check_for_updates and update_check_days > 0 and today >= last_update_check + update_check_days
        )
        log.debug(
            (
                "%(check_status)s startup check for program updates."
                " Today: %(today_date)s,"
                " Last check: %(last_check)s (Check interval: %(check_interval)s days),"
                " Update level: %(update_level)s (%(update_level_name)s)"
            ),
            {
                'check_status': 'Initiating' if do_auto_update_check else 'Skipping',
                'today_date': datetime.date.today(),
                'last_check': str(datetime.date.fromordinal(last_update_check)) if last_update_check > 0 else 'never',
                'check_interval': update_check_days,
                'update_level': update_level,
                'update_level_name': PROGRAM_UPDATE_LEVELS[update_level]['name']
                if update_level in PROGRAM_UPDATE_LEVELS
                else 'unknown',
            },
        )
        if do_auto_update_check:
            self._check_for_update(False)

    def _check_for_update(self, show_always):
        config = get_config()
        self.tagger.updatecheckmanager.check_update(
            show_always=show_always,
            update_level=config.setting['update_level'],
            callback=update_last_check_date,
        )

    def _check_and_repair_naming_scripts(self):
        """Check the 'file_renaming_scripts' config setting to ensure that the list of scripts
        is not empty.  Check that the 'selected_file_naming_script_id' config setting points to
        a valid file naming script.
        """
        config = get_config()
        script_key = 'file_renaming_scripts'
        if not config.setting[script_key]:
            config.setting[script_key] = {script['id']: script.to_dict() for script in get_file_naming_script_presets()}
        naming_script_ids = list(config.setting[script_key])
        script_id_key = 'selected_file_naming_script_id'
        if config.setting[script_id_key] not in naming_script_ids:
            config.setting[script_id_key] = naming_script_ids[0]

    def _check_and_repair_profiles(self):
        """Check the profiles and profile settings and repair the values if required.
        Checks that there is a settings dictionary for each profile, and that no profiles
        reference a non-existant file naming script.
        """
        script_id_key = 'selected_file_naming_script_id'
        config = get_config()
        naming_scripts = config.setting['file_renaming_scripts']
        naming_script_ids = set(naming_scripts.keys())
        profile_settings = deepcopy(config.profiles[SettingConfigSection.SETTINGS_KEY])
        for profile in config.profiles[SettingConfigSection.PROFILES_KEY]:
            p_id = profile['id']
            # Add empty settings if none found for a profile
            if p_id not in profile_settings:
                log.warning(
                    "No settings dict found for profile '%s' ('%s'). Adding empty dict.",
                    p_id,
                    profile['title'],
                )
                profile_settings[p_id] = {}
            # Remove any invalid naming script ids from profiles
            if script_id_key in profile_settings[p_id]:
                if profile_settings[p_id][script_id_key] not in naming_script_ids:
                    log.warning(
                        "Removing invalid naming script id '%s' from profile '%s' ('%s')",
                        profile_settings[p_id][script_id_key],
                        p_id,
                        profile['title'],
                    )
                    profile_settings[p_id][script_id_key] = None
        config.profiles[SettingConfigSection.SETTINGS_KEY] = profile_settings

    def _make_script_selector_menu(self):
        """Update the sub-menu of available file naming scripts."""
        if self.script_editor_dialog is None or not isinstance(self.script_editor_dialog, ScriptEditorDialog):
            config = get_config()
            naming_scripts = config.setting['file_renaming_scripts']
            selected_script_id = config.setting['selected_file_naming_script_id']
        else:
            naming_scripts = self.script_editor_dialog.naming_scripts
            selected_script_id = self.script_editor_dialog.selected_script_id

        self.script_quick_selector_menu.clear()

        group = QtGui.QActionGroup(self.script_quick_selector_menu)
        group.setExclusive(True)

        def _add_menu_item(title, id):
            script_action = QtGui.QAction(title, self.script_quick_selector_menu)
            script_action.triggered.connect(partial(self._select_new_naming_script, id))
            script_action.setCheckable(True)
            script_action.setChecked(id == selected_script_id)
            self.script_quick_selector_menu.addAction(script_action)
            group.addAction(script_action)

        for id, naming_script in sorted(naming_scripts.items(), key=lambda item: item[1]['title']):
            _add_menu_item(naming_script['title'], id)

    def _select_new_naming_script(self, id):
        """Update the currently selected naming script ID in the settings.

        Args:
            id (str): ID of the selected file naming script
        """
        config = get_config()
        log.debug("Setting naming script to: %s", id)
        config.setting['selected_file_naming_script_id'] = id
        if self.script_editor_dialog:
            self.script_editor_dialog.set_selected_script_id(id)

    def open_file_naming_script_editor(self):
        """Open the file naming script editor / manager in a new window."""
        examples = ScriptEditorExamples(tagger=self.tagger)
        self.script_editor_dialog = ScriptEditorDialog.show_instance(parent=self, examples=examples)
        self.script_editor_dialog.signal_save.connect(self._script_editor_save)
        self.script_editor_dialog.signal_selection_changed.connect(self._update_selector_from_script_editor)
        self.script_editor_dialog.signal_index_changed.connect(self._script_editor_index_changed)
        self.script_editor_dialog.finished.connect(self._script_editor_closed)
        # Create list of signals to disconnect when opening Options dialog.
        # Do not include `finished` because that is still used to clean up
        # locally when the editor is closed from the Options dialog.
        self.script_editor_signals = [
            self.script_editor_dialog.signal_save,
            self.script_editor_dialog.signal_selection_changed,
            self.script_editor_dialog.signal_index_changed,
        ]
        self.enable_action(MainAction.SHOW_SCRIPT_EDITOR, False)

    def _script_editor_save(self):
        """Process "signal_save" signal from the script editor."""
        self._make_script_selector_menu()

    def _script_editor_closed(self):
        """Process "finished" signal from the script editor."""
        self.enable_action(MainAction.SHOW_SCRIPT_EDITOR, True)
        self.script_editor_dialog = None

    def _update_script_editor_example_files(self):
        """Update the list of example files for the file naming script editor."""
        script_editor_dialog = self.script_editor_dialog
        if script_editor_dialog and script_editor_dialog.isVisible():
            script_editor_dialog.examples.update_sample_example_files()
            self._update_script_editor_examples()

    def _update_script_editor_examples(self):
        """Update the examples for the file naming script editor, using current settings."""
        script_editor_dialog = self.script_editor_dialog
        if script_editor_dialog and script_editor_dialog.isVisible():
            config = get_config()
            override = {
                "rename_files": config.setting["rename_files"],
                "move_files": config.setting["move_files"],
            }
            script_editor_dialog.examples.update_examples(override=override)
            script_editor_dialog.display_examples()

    def _script_editor_index_changed(self):
        """Process "signal_index_changed" signal from the script editor."""
        self._script_editor_save()

    def _update_selector_from_script_editor(self):
        """Process "signal_selection_changed" signal from the script editor."""
        self._script_editor_save()

    def _make_profile_selector_menu(self):
        """Update the sub-menu of available option profiles."""
        config = get_config()
        option_profiles = config.profiles[SettingConfigSection.PROFILES_KEY]
        if not option_profiles:
            self.profile_quick_selector_menu.setDisabled(True)
            return
        self.profile_quick_selector_menu.setDisabled(False)
        self.profile_quick_selector_menu.clear()

        # Use QWidgetAction with a QCheckBox so toggling does not close the menu.
        def _add_menu_item(title, checked, profile_id):
            menu = self.profile_quick_selector_menu
            action = QtWidgets.QWidgetAction(menu)
            container = CheckboxMenuItem(menu, action, title)
            checkbox = container.checkbox
            checkbox.setChecked(checked)
            checkbox.toggled.connect(partial(self._set_profile_enabled, profile_id))
            action.setDefaultWidget(container)
            self.profile_quick_selector_menu.addAction(action)

        for profile in option_profiles:
            _add_menu_item(profile['title'], profile['enabled'], profile['id'])

    def _set_profile_enabled(self, profile_id: str, enabled: bool) -> None:
        """Set the enabled state of a profile and refresh dependent UI.

        Parameters
        ----------
        profile_id : str
            ID code of the profile to modify.
        enabled : bool
            New enabled state for the profile.
        """
        config = get_config()
        option_profiles = config.profiles[SettingConfigSection.PROFILES_KEY]
        for profile in option_profiles:
            if profile['id'] == profile_id:
                if profile['enabled'] != enabled:
                    profile['enabled'] = enabled
                    config.profiles[SettingConfigSection.PROFILES_KEY] = option_profiles
                    # Update menus/settings that may depend on profile overrides.
                    self._reset_option_menu_state()
                return

    def _make_plugin_tools_menu(self):
        """Update the Plugin Tools menu"""
        actions = list(ext_point_plugin_tools_items)

        self.plugin_tools_menu.clear()

        if not actions:
            self.plugin_tools_menu.menuAction().setVisible(False)
            return

        self.plugin_tools_menu.menuAction().setVisible(True)

        for ActionClass in actions:
            # Instantiate action with API
            try:
                action = ActionClass()
                action.setParent(self.plugin_tools_menu)  # Set parent to keep action alive
                self.plugin_tools_menu.addAction(action)
            except Exception as ex:
                log.error("Error adding plugin action", exc_info=ex)

    def _make_settings_selector_menu(self):
        """Update the sub-menu of selected option settings."""
        config = get_config()
        quick_settings: list = deepcopy(config.setting['quick_menu_items'])

        # Don't try to display any settings that don't exist in the current context,
        # such as settings from a plugin options page that has not been loaded.
        for setting in config.setting['quick_menu_items']:
            if not Option.exists('setting', setting):
                quick_settings.remove(setting)

        if not quick_settings:
            self.settings_quick_selector_menu.setDisabled(True)
            return

        self.settings_quick_selector_menu.setDisabled(False)
        self.settings_quick_selector_menu.clear()

        group = QtGui.QActionGroup(self.settings_quick_selector_menu)
        group.setExclusive(False)

        def _add_menu_item(setting_id, title, enabled):
            setting_action = QtGui.QAction(title, self.settings_quick_selector_menu)
            setting_action.triggered.connect(partial(self._toggle_quick_setting, setting_id))
            setting_action.setCheckable(True)
            setting_action.setChecked(enabled)
            self.settings_quick_selector_menu.addAction(setting_action)
            group.addAction(setting_action)

        for setting_id in quick_settings:
            _add_menu_item(setting_id, get_option_title(setting_id), config.setting[setting_id])

    def _toggle_quick_setting(self, setting_id):
        """Toggle the enabled state of the selected setting.

        Args:
            settingid (str): ID code of the setting to modify
        """
        config = get_config()
        config.setting[setting_id] = not config.setting[setting_id]

    def show_new_user_dialog(self):
        config = get_config()
        if config.setting['show_new_user_dialog']:
            msg = NewUserDialog(self)
            config.setting['show_new_user_dialog'] = msg.show()

    def show_plugins_options_page(self):
        self.show_options(page='plugins')

    def show_filter_bars(self):
        show_state = self.action_is_checked(MainAction.SHOW_FILTERBAR)
        self.panel.show_filter_bars(show_state)


def update_last_check_date(is_success):
    if is_success:
        config = get_config()
        config.persist['last_update_check'] = datetime.date.today().toordinal()
    else:
        log.debug('The update check was unsuccessful. The last update date will not be changed.')
