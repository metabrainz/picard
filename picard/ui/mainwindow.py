# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2007 Nikolai Prokoschenko
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2008 Will
# Copyright (C) 2008-2010, 2015, 2018-2023 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 David Hilton
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013, 2015-2017 Wieland Hoffmann
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2013-2023 Laurent Monin
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
# Copyright (C) 2018, 2021-2023 Bob Swift
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


from collections import OrderedDict
from copy import deepcopy
import datetime
from functools import partial
import itertools
import os.path

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
    BoolOption,
    FloatOption,
    IntOption,
    Option,
    SettingConfigSection,
    TextOption,
    get_config,
)
from picard.const import PROGRAM_UPDATE_LEVELS
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.file import File
from picard.formats import supported_formats
from picard.plugin import ExtensionPoint
from picard.script import get_file_naming_script_presets
from picard.track import Track
from picard.util import (
    IgnoreUpdatesContext,
    icontheme,
    iter_files_from_objects,
    iter_unique,
    open_local_path,
    reconnect,
    restore_method,
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
from picard.ui.filebrowser import FileBrowser
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
from picard.ui.metadatabox import MetadataBox
from picard.ui.newuserdialog import NewUserDialog
from picard.ui.options.dialog import OptionsDialog
from picard.ui.passworddialog import (
    PasswordDialog,
    ProxyDialog,
)
from picard.ui.pluginupdatedialog import PluginUpdatesDialog
from picard.ui.savewarningdialog import SaveWarningDialog
from picard.ui.scripteditor import (
    ScriptEditorDialog,
    ScriptEditorExamples,
)
from picard.ui.searchdialog.album import AlbumSearchDialog
from picard.ui.searchdialog.track import TrackSearchDialog
from picard.ui.statusindicator import DesktopStatusIndicator
from picard.ui.tagsfromfilenames import TagsFromFileNamesDialog
from picard.ui.util import (
    MultiDirsSelectDialog,
    find_starting_directory,
)


ui_init = ExtensionPoint(label='ui_init')


def register_ui_init(function):
    ui_init.register(function.__module__, function)


class MainWindowActions:
    _create_actions = []

    @classmethod
    def add(cls):
        def decorator(fn):
            cls._create_actions.append(fn)
            return fn
        return decorator

    @classmethod
    def create(cls, parent):
        for create_action in cls._create_actions:
            create_action(parent)


class MainWindow(QtWidgets.QMainWindow, PreserveGeometry):

    defaultsize = QtCore.QSize(780, 560)
    selection_updated = QtCore.pyqtSignal(object)
    ready_for_display = QtCore.pyqtSignal()

    options = [
        Option('persist', 'window_state', QtCore.QByteArray()),
        BoolOption('persist', 'window_maximized', False),
        BoolOption('persist', 'view_metadata_view', True),
        BoolOption('persist', 'view_cover_art', True),
        BoolOption('persist', 'view_toolbar', True),
        BoolOption('persist', 'view_file_browser', False),
        TextOption('persist', 'current_directory', ""),
        FloatOption('persist', 'mediaplayer_playback_rate', 1.0),
        IntOption('persist', 'mediaplayer_volume', 50),
    ]

    def __init__(self, parent=None, disable_player=False):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NativeWindow)
        self.__shown = False
        app = QtCore.QCoreApplication.instance()
        self._is_wayland = app.is_wayland
        self.selected_objects = []
        self.ignore_selection_changes = IgnoreUpdatesContext(self.update_selection)
        self.toolbar = None
        self.player = None
        self.status_indicators = []
        if DesktopStatusIndicator:
            self.ready_for_display.connect(self._setup_desktop_status_indicator)
        if not disable_player:
            from picard.ui.playertoolbar import Player
            player = Player(self)
            if player.available:
                self.player = player
                self.player.error.connect(self._on_player_error)

        self.script_editor_dialog = None
        self.examples = None

        self.tagger.pluginmanager.updates_available.connect(self.show_plugin_update_dialog)

        self.check_and_repair_naming_scripts()
        self.check_and_repair_profiles()

        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(_("MusicBrainz Picard"))
        icon = QtGui.QIcon()
        for size in (16, 24, 32, 48, 128, 256):
            icon.addFile(
                ":/images/{size}x{size}/{app_id}.png".format(
                    size=size, app_id=PICARD_APP_ID),
                QtCore.QSize(size, size)
            )
        self.setWindowIcon(icon)

        self.show_close_window = IS_MACOS

        self.create_actions()
        self.create_statusbar()
        self.create_toolbar()
        self.create_menus()

        if IS_MACOS:
            self.setUnifiedTitleAndToolBarOnMac(True)

        main_layout = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        main_layout.setObjectName('main_window_bottom_splitter')
        main_layout.setChildrenCollapsible(False)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.panel = MainPanel(self, main_layout)
        self.panel.setObjectName('main_panel_splitter')
        self.file_browser = FileBrowser(self.panel)
        if not self.show_file_browser_action.isChecked():
            self.file_browser.hide()
        self.panel.insertWidget(0, self.file_browser)

        self.log_dialog = LogView(self)
        self.history_dialog = HistoryView(self)

        self.metadata_box = MetadataBox(self)
        self.cover_art_box = CoverArtBox(self)
        metadata_view_layout = QtWidgets.QHBoxLayout()
        metadata_view_layout.setContentsMargins(0, 0, 0, 0)
        metadata_view_layout.setSpacing(0)
        metadata_view_layout.addWidget(self.metadata_box, 1)
        metadata_view_layout.addWidget(self.cover_art_box, 0)
        self.metadata_view = QtWidgets.QWidget()
        self.metadata_view.setLayout(metadata_view_layout)

        self.show_metadata_view()
        self.show_cover_art()

        main_layout.addWidget(self.panel)
        main_layout.addWidget(self.metadata_view)
        self.setCentralWidget(main_layout)

        # accessibility
        self.set_tab_order()

        for function in ui_init:
            function(self)

    def set_processing(self, processing=True):
        self.panel.set_processing(processing)

    def set_sorting(self, sorting=True):
        self.panel.set_sorting(sorting)

    def keyPressEvent(self, event):
        # On macOS Command+Backspace triggers the so called "Forward Delete".
        # It should be treated the same as the Delete button.
        is_forward_delete = IS_MACOS and \
            event.key() == QtCore.Qt.Key.Key_Backspace and \
            event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier
        if event.matches(QtGui.QKeySequence.StandardKey.Delete) or is_forward_delete:
            if self.metadata_box.hasFocus():
                self.metadata_box.remove_selected_tags()
            else:
                self.remove()
        elif event.matches(QtGui.QKeySequence.StandardKey.Find):
            self.search_edit.setFocus(True)
        else:
            super().keyPressEvent(event)

    def show(self):
        self.restoreWindowState()
        super().show()
        self.show_new_user_dialog()
        if self.tagger.autoupdate_enabled:
            self.auto_update_check()
        self.check_for_plugin_update()
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
            if not self.script_editor_dialog.unsaved_changes_confirmation():
                event.ignore()
                return
            else:
                # Silently close the script editor without displaying the confirmation a second time.
                self.script_editor_dialog.loading = True
        event.accept()

    def _setup_desktop_status_indicator(self):
        if DesktopStatusIndicator:
            self.register_status_indicator(DesktopStatusIndicator(self.windowHandle()))

    def register_status_indicator(self, indicator):
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
            txt = ngettext(
                "There is %d unsaved file. Closing Picard will lose all unsaved changes.",
                "There are %d unsaved files. Closing Picard will lose all unsaved changes.",
                unsaved_files) % unsaved_files
            msg.setInformativeText(txt)
            cancel = msg.addButton(QMessageBox.StandardButton.Cancel)
            msg.setDefaultButton(cancel)
            msg.addButton(_("&Quit Picard"), QMessageBox.ButtonRole.YesRole)
            ret = msg.exec()

            if ret == QMessageBox.StandardButton.Cancel:
                return False

        return True

    def saveWindowState(self):
        config = get_config()
        config.persist['window_state'] = self.saveState()
        is_maximized = bool(self.windowState() & QtCore.Qt.WindowState.WindowMaximized)
        self.save_geometry()
        config.persist['window_maximized'] = is_maximized
        config.persist['view_metadata_view'] = self.show_metadata_view_action.isChecked()
        config.persist['view_cover_art'] = self.show_cover_art_action.isChecked()
        config.persist['view_toolbar'] = self.show_toolbar_action.isChecked()
        config.persist['view_file_browser'] = self.show_file_browser_action.isChecked()
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

    def create_statusbar(self):
        """Creates a new status bar."""
        self.statusBar().showMessage(_("Ready"))
        infostatus = InfoStatus(self)
        self._progress = infostatus.get_progress
        self.listening_label = QtWidgets.QLabel()
        self.listening_label.setStyleSheet("QLabel { margin: 0 4px 0 4px; }")
        self.listening_label.setVisible(False)
        self.listening_label.setToolTip("<qt/>" + _(
            "Picard listens on this port to integrate with your browser. When "
            "you \"Search\" or \"Open in Browser\" from Picard, clicking the "
            "\"Tagger\" button on the web page loads the release into Picard."
        ))
        self.statusBar().addPermanentWidget(infostatus)
        self.statusBar().addPermanentWidget(self.listening_label)
        self.tagger.tagger_stats_changed.connect(self.update_statusbar_stats)
        self.tagger.listen_port_changed.connect(self.update_statusbar_listen_port)
        self.register_status_indicator(infostatus)
        self.update_statusbar_stats()

    @throttle(100)
    def update_statusbar_stats(self):
        """Updates the status bar information."""
        total_files = len(self.tagger.files)
        total_albums = len(self.tagger.albums)
        pending_files = File.num_pending_files
        pending_requests = self.tagger.webservice.num_pending_web_requests
        for indicator in self.status_indicators:
            indicator.update(files=total_files, albums=total_albums,
                pending_files=pending_files, pending_requests=pending_requests, progress=self._progress())

    def update_statusbar_listen_port(self, listen_port):
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
        # _ is defined using builtins.__dict__, so setting it as default named argument
        # value doesn't work as expected
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
                msg.setText(_(
                    "You need to configure your AcoustID API key before you can submit fingerprints."))
                open_options = QtWidgets.QPushButton(
                    icontheme.lookup('preferences-desktop'), _("Open AcoustID options"))
                msg.addButton(QtWidgets.QMessageBox.StandardButton.Cancel)
                msg.addButton(open_options, QtWidgets.QMessageBox.ButtonRole.YesRole)
                msg.exec()
                if msg.clickedButton() == open_options:
                    self.show_options('fingerprinting')
            else:
                self.tagger.acoustidmanager.submit()

    @MainWindowActions.add()
    def _create_options_action(self):
        action = QtGui.QAction(icontheme.lookup('preferences-desktop'), _("&Options…"), self)
        action.setMenuRole(QtGui.QAction.MenuRole.PreferencesRole)
        action.triggered.connect(self.show_options)
        self.options_action = action

    @MainWindowActions.add()
    def _create_show_script_editor_action(self):
        action = QtGui.QAction(_("Open &file naming script editor…"))
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+S")))
        action.triggered.connect(self.open_file_naming_script_editor)
        self.show_script_editor_action = action

    @MainWindowActions.add()
    def _create_cut_action(self):
        action = QtGui.QAction(icontheme.lookup('edit-cut', icontheme.ICON_SIZE_MENU), _("&Cut"), self)
        action.setShortcut(QtGui.QKeySequence.StandardKey.Cut)
        action.setEnabled(False)
        action.triggered.connect(self.cut)
        self.cut_action = action

    @MainWindowActions.add()
    def _create_paste_action(self):
        action = QtGui.QAction(icontheme.lookup('edit-paste', icontheme.ICON_SIZE_MENU), _("&Paste"), self)
        action.setShortcut(QtGui.QKeySequence.StandardKey.Paste)
        action.setEnabled(False)
        action.triggered.connect(self.paste)
        self.paste_action = action

    @MainWindowActions.add()
    def _create_help_action(self):
        action = QtGui.QAction(_("&Help…"), self)
        action.setShortcut(QtGui.QKeySequence.StandardKey.HelpContents)
        action.triggered.connect(self.show_help)
        self.help_action = action

    @MainWindowActions.add()
    def _create_about_action(self):
        action = QtGui.QAction(_("&About…"), self)
        action.setMenuRole(QtGui.QAction.MenuRole.AboutRole)
        action.triggered.connect(self.show_about)
        self.about_action = action

    @MainWindowActions.add()
    def _create_donate_action(self):
        action = QtGui.QAction(_("&Donate…"), self)
        action.triggered.connect(self.open_donation_page)
        self.donate_action = action

    @MainWindowActions.add()
    def _create_report_bug_action(self):
        action = QtGui.QAction(_("&Report a Bug…"), self)
        action.triggered.connect(self.open_bug_report)
        self.report_bug_action = action

    @MainWindowActions.add()
    def _create_support_forum_action(self):
        action = QtGui.QAction(_("&Support Forum…"), self)
        action.triggered.connect(self.open_support_forum)
        self.support_forum_action = action

    @MainWindowActions.add()
    def _create_add_files_action(self):
        action = QtGui.QAction(icontheme.lookup('document-open'), _("&Add Files…"), self)
        action.setStatusTip(_("Add files to the tagger"))
        # TR: Keyboard shortcut for "Add Files…"
        action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        action.triggered.connect(self.add_files)
        self.add_files_action = action

    @MainWindowActions.add()
    def _create_add_directory_action(self):
        action = QtGui.QAction(icontheme.lookup('folder'), _("Add Fold&er…"), self)
        action.setStatusTip(_("Add a folder to the tagger"))
        # TR: Keyboard shortcut for "Add Directory…"
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+E")))
        action.triggered.connect(self.add_directory)
        self.add_directory_action = action

    @MainWindowActions.add()
    def _create_close_window_action(self):
        if self.show_close_window:
            action = QtGui.QAction(_("Close Window"), self)
            action.setShortcut(QtGui.QKeySequence(_("Ctrl+W")))
            action.triggered.connect(self.close_active_window)
        else:
            action = None
        self.close_window_action = action

    @MainWindowActions.add()
    def _create_save_action(self):
        action = QtGui.QAction(icontheme.lookup('document-save'), _("&Save"), self)
        action.setStatusTip(_("Save selected files"))
        # TR: Keyboard shortcut for "Save"
        action.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        action.setEnabled(False)
        action.triggered.connect(self.save)
        self.save_action = action

    @MainWindowActions.add()
    def _create_submit_acoustid_action(self):
        action = QtGui.QAction(icontheme.lookup('acoustid-fingerprinter'), _("S&ubmit AcoustIDs"), self)
        action.setStatusTip(_("Submit acoustic fingerprints"))
        action.setEnabled(False)
        action.triggered.connect(self._on_submit_acoustid)
        self.submit_acoustid_action = action

    @MainWindowActions.add()
    def _create_exit_action(self):
        action = QtGui.QAction(_("E&xit"), self)
        action.setMenuRole(QtGui.QAction.MenuRole.QuitRole)
        # TR: Keyboard shortcut for "Exit"
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+Q")))
        action.triggered.connect(self.close)
        self.exit_action = action

    @MainWindowActions.add()
    def _create_remove_action(self):
        action = QtGui.QAction(icontheme.lookup('list-remove'), _("&Remove"), self)
        action.setStatusTip(_("Remove selected files/albums"))
        action.setEnabled(False)
        action.triggered.connect(self.remove)
        self.remove_action = action

    @MainWindowActions.add()
    def _create_browser_lookup_action(self):
        action = QtGui.QAction(icontheme.lookup('lookup-musicbrainz'), _("Lookup in &Browser"), self)
        action.setStatusTip(_("Lookup selected item on MusicBrainz website"))
        action.setEnabled(False)
        # TR: Keyboard shortcut for "Lookup in Browser"
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+L")))
        action.triggered.connect(self.browser_lookup)
        self.browser_lookup_action = action

    @MainWindowActions.add()
    def _create_submit_cluster_action(self):
        if addrelease.is_available():
            action = QtGui.QAction(_("Submit cluster as release…"), self)
            action.setStatusTip(_("Submit cluster as a new release to MusicBrainz"))
            action.setEnabled(False)
            action.triggered.connect(self.submit_cluster)
        else:
            action = None
        self.submit_cluster_action = action

    @MainWindowActions.add()
    def _create_submit_file_as_recording_action(self):
        if addrelease.is_available():
            action = QtGui.QAction(_("Submit file as standalone recording…"), self)
            action.setStatusTip(_("Submit file as a new recording to MusicBrainz"))
            action.setEnabled(False)
            action.triggered.connect(self.submit_file)
        else:
            action = None
        self.submit_file_as_recording_action = action

    @MainWindowActions.add()
    def _create_submit_file_as_release_action(self):
        if addrelease.is_available():
            action = QtGui.QAction(_("Submit file as release…"), self)
            action.setStatusTip(_("Submit file as a new release to MusicBrainz"))
            action.setEnabled(False)
            action.triggered.connect(partial(self.submit_file, as_release=True))
        else:
            action = None
        self.submit_file_as_release_action = action

    @MainWindowActions.add()
    def _create_similar_items_search_action(self):
        action = QtGui.QAction(icontheme.lookup('system-search'), _("Search for similar items…"), self)
        action.setIconText(_("Similar items"))
        action.setStatusTip(_("View similar releases or recordings and optionally choose a different one"))
        action.setEnabled(False)
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
        action.triggered.connect(self.show_similar_items_search)
        self.similar_items_search_action = action

    @MainWindowActions.add()
    def _create_album_search_action(self):
        action = QtGui.QAction(icontheme.lookup('system-search'), _("Search for similar albums…"), self)
        action.setStatusTip(_("View similar releases and optionally choose a different release"))
        action.setEnabled(False)
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
        action.triggered.connect(self.show_more_albums)
        self.album_search_action = action

    @MainWindowActions.add()
    def _create_track_search_action(self):
        action = QtGui.QAction(icontheme.lookup('system-search'), _("Search for similar tracks…"), self)
        action.setStatusTip(_("View similar tracks and optionally choose a different release"))
        action.setEnabled(False)
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
        action.triggered.connect(self.show_more_tracks)
        self.track_search_action = action

    @MainWindowActions.add()
    def _create_album_other_versions_action(self):
        action = QtGui.QAction(_("Show &other album versions…"), self)
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+O")))
        action.triggered.connect(self.show_album_other_versions)
        self.album_other_versions_action = action

    @MainWindowActions.add()
    def _create_show_file_browser_action(self):
        config = get_config()
        action = QtGui.QAction(_("File &Browser"), self)
        action.setCheckable(True)
        if config.persist['view_file_browser']:
            action.setChecked(True)
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+B")))
        action.triggered.connect(self.show_file_browser)
        self.show_file_browser_action = action

    @MainWindowActions.add()
    def _create_show_metadata_view_action(self):
        config = get_config()
        action = QtGui.QAction(_("&Metadata"), self)
        action.setCheckable(True)
        if config.persist['view_metadata_view']:
            action.setChecked(True)
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+M")))
        action.triggered.connect(self.show_metadata_view)
        self.show_metadata_view_action = action

    @MainWindowActions.add()
    def _create_show_cover_art_action(self):
        config = get_config()
        action = QtGui.QAction(_("&Cover Art"), self)
        action.setCheckable(True)
        if config.persist['view_cover_art']:
            action.setChecked(True)
        action.setEnabled(self.show_metadata_view_action.isChecked())
        action.triggered.connect(self.show_cover_art)
        self.show_cover_art_action = action

    @MainWindowActions.add()
    def _create_show_toolbar_action(self):
        config = get_config()
        action = QtGui.QAction(_("&Actions"), self)
        action.setCheckable(True)
        if config.persist['view_toolbar']:
            action.setChecked(True)
        action.triggered.connect(self.show_toolbar)
        self.show_toolbar_action = action

    @MainWindowActions.add()
    def _create_search_action(self):
        action = QtGui.QAction(icontheme.lookup('system-search'), _("Search"), self)
        action.setEnabled(False)
        action.triggered.connect(self.search)
        self.search_action = action

    @MainWindowActions.add()
    def _create_cd_lookup_action(self):
        action = QtGui.QAction(icontheme.lookup('media-optical'), _("Lookup &CD…"), self)
        action.setStatusTip(_("Lookup the details of the CD in your drive"))
        # TR: Keyboard shortcut for "Lookup CD"
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+K")))
        action.triggered.connect(self.tagger.lookup_cd)
        self.cd_lookup_action = action

        menu = QtWidgets.QMenu(_("Lookup &CD…"))
        menu.setIcon(icontheme.lookup('media-optical'))
        menu.triggered.connect(self.tagger.lookup_cd)
        self.cd_lookup_menu = menu
        if discid is None:
            log.warning("CDROM: discid library not found - Lookup CD functionality disabled")
            self.cd_lookup_action.setEnabled(False)
            self.cd_lookup_menu.setEnabled(False)
        else:
            thread.run_task(get_cdrom_drives, self._update_cd_lookup_actions)

    @MainWindowActions.add()
    def _create_analyze_action(self):
        action = QtGui.QAction(icontheme.lookup('picard-analyze'), _("&Scan"), self)
        action.setStatusTip(_("Use AcoustID audio fingerprint to identify the files by the actual music, even if they have no metadata"))
        action.setEnabled(False)
        action.setToolTip(_("Identify the file using its AcoustID audio fingerprint"))
        # TR: Keyboard shortcut for "Analyze"
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+Y")))
        action.triggered.connect(self.analyze)
        self.analyze_action = action

    @MainWindowActions.add()
    def _create_generate_fingerprints_action(self):
        action = QtGui.QAction(icontheme.lookup('fingerprint'), _("&Generate AcoustID Fingerprints"), self)
        action.setIconText(_("Generate Fingerprints"))
        action.setStatusTip(_("Generate the AcoustID audio fingerprints for the selected files without doing a lookup"))
        action.setEnabled(False)
        action.setToolTip(_("Generate the AcoustID audio fingerprints for the selected files"))
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+Y")))
        action.triggered.connect(self.generate_fingerprints)
        self.generate_fingerprints_action = action

    @MainWindowActions.add()
    def _create_cluster_action(self):
        action = QtGui.QAction(icontheme.lookup('picard-cluster'), _("Cl&uster"), self)
        action.setStatusTip(_("Cluster files into album clusters"))
        action.setEnabled(False)
        # TR: Keyboard shortcut for "Cluster"
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+U")))
        action.triggered.connect(self.cluster)
        self.cluster_action = action

    @MainWindowActions.add()
    def _create_autotag_action(self):
        action = QtGui.QAction(icontheme.lookup('picard-auto-tag'), _("&Lookup"), self)
        tip = _("Lookup selected items in MusicBrainz")
        action.setToolTip(tip)
        action.setStatusTip(tip)
        action.setEnabled(False)
        # TR: Keyboard shortcut for "Lookup"
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+L")))
        action.triggered.connect(self.autotag)
        self.autotag_action = action

    @MainWindowActions.add()
    def _create_view_info_action(self):
        action = QtGui.QAction(icontheme.lookup('picard-edit-tags'), _("&Info…"), self)
        action.setEnabled(False)
        # TR: Keyboard shortcut for "Info"
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+I")))
        action.triggered.connect(self.view_info)
        self.view_info_action = action

    @MainWindowActions.add()
    def _create_refresh_action(self):
        action = QtGui.QAction(icontheme.lookup('view-refresh', icontheme.ICON_SIZE_MENU), _("&Refresh"), self)
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+R")))
        action.triggered.connect(self.refresh)
        self.refresh_action = action

    @MainWindowActions.add()
    def _create_enable_renaming_action(self):
        config = get_config()
        action = QtGui.QAction(_("&Rename Files"), self)
        action.setCheckable(True)
        action.setChecked(config.setting['rename_files'])
        action.triggered.connect(self.toggle_rename_files)
        self.enable_renaming_action = action

    @MainWindowActions.add()
    def _create_enable_moving_action(self):
        config = get_config()
        action = QtGui.QAction(_("&Move Files"), self)
        action.setCheckable(True)
        action.setChecked(config.setting['move_files'])
        action.triggered.connect(self.toggle_move_files)
        self.enable_moving_action = action

    @MainWindowActions.add()
    def _create_enable_tag_saving_action(self):
        config = get_config()
        action = QtGui.QAction(_("Save &Tags"), self)
        action.setCheckable(True)
        action.setChecked(not config.setting['dont_write_tags'])
        action.triggered.connect(self.toggle_tag_saving)
        self.enable_tag_saving_action = action

    @MainWindowActions.add()
    def _create_tags_from_filenames_action(self):
        action = QtGui.QAction(icontheme.lookup('picard-tags-from-filename'), _("Tags From &File Names…"), self)
        action.setIconText(_("Parse File Names…"))
        action.setToolTip(_("Set tags based on the file names"))
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+T")))
        action.setEnabled(False)
        action.triggered.connect(self.open_tags_from_filenames)
        self.tags_from_filenames_action = action

    @MainWindowActions.add()
    def _create_open_collection_in_browser_action(self):
        config = get_config()
        action = QtGui.QAction(_("&Open My Collections in Browser"), self)
        action.setEnabled(config.setting['username'] != '')
        action.triggered.connect(self.open_collection_in_browser)
        self.open_collection_in_browser_action = action

    @MainWindowActions.add()
    def _create_view_log_action(self):
        action = QtGui.QAction(_("View &Error/Debug Log"), self)
        # TR: Keyboard shortcut for "View Error/Debug Log"
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+G")))
        action.triggered.connect(self.show_log)
        self.view_log_action = action

    @MainWindowActions.add()
    def _create_view_history_action(self):
        action = QtGui.QAction(_("View Activity &History"), self)
        # TR: Keyboard shortcut for "View Activity History"
        # On macOS ⌘+H is a system shortcut to hide the window. Use ⌘+Shift+H instead.
        action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+H") if IS_MACOS else _("Ctrl+H")))
        action.triggered.connect(self.show_history)
        self.view_history_action = action

    @MainWindowActions.add()
    def _create_play_file_action(self):
        action = QtGui.QAction(icontheme.lookup('play-music'), _("Open in &Player"), self)
        action.setStatusTip(_("Play the file in your default media player"))
        action.setEnabled(False)
        action.triggered.connect(self.play_file)
        self.play_file_action = action

    @MainWindowActions.add()
    def _create_open_folder_action(self):
        action = QtGui.QAction(icontheme.lookup('folder', icontheme.ICON_SIZE_MENU), _("Open Containing &Folder"), self)
        action.setStatusTip(_("Open the containing folder in your file explorer"))
        action.setEnabled(False)
        action.triggered.connect(self.open_folder)
        self.open_folder_action = action

    @MainWindowActions.add()
    def _create_check_update_action(self):
        if self.tagger.autoupdate_enabled:
            action = QtGui.QAction(_("&Check for Update…"), self)
            action.setMenuRole(QtGui.QAction.MenuRole.ApplicationSpecificRole)
            action.triggered.connect(self.do_update_check)
        else:
            action = None
        self.check_update_action = action

    def create_actions(self):
        MainWindowActions.create(self)

        webservice_manager = self.tagger.webservice.manager
        webservice_manager.authenticationRequired.connect(self.show_password_dialog)
        webservice_manager.proxyAuthenticationRequired.connect(self.show_proxy_dialog)

    def _update_cd_lookup_actions(self, result=None, error=None):
        if error:
            log.error("CDROM: Error on CD-ROM drive detection: %r", error)
        else:
            self.update_cd_lookup_drives(result)

    def update_cd_lookup_drives(self, drives):
        self.cd_lookup_menu.clear()
        self.cd_lookup_action.setEnabled(discid is not None)
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
            reconnect(self.cd_lookup_action.triggered, action.trigger)
        else:
            reconnect(self.cd_lookup_action.triggered, self.tagger.lookup_cd)

    def _update_cd_lookup_button(self):
        button = self.toolbar.widgetForAction(self.cd_lookup_action)
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
        self.update_script_editor_examples()

    def toggle_move_files(self, checked):
        config = get_config()
        config.setting['move_files'] = checked
        self.update_script_editor_examples()

    def toggle_tag_saving(self, checked):
        config = get_config()
        config.setting['dont_write_tags'] = not checked

    def get_selected_or_unmatched_files(self):
        if self.selected_objects:
            files = list(iter_files_from_objects(self.selected_objects))
            if files:
                return files
        return self.tagger.unclustered_files.files

    def open_tags_from_filenames(self):
        files = self.get_selected_or_unmatched_files()
        if files:
            dialog = TagsFromFileNamesDialog(files, self)
            dialog.exec()

    def open_collection_in_browser(self):
        self.tagger.collection_lookup()

    def create_menus(self):
        menu = self.menuBar().addMenu(_("&File"))
        menu.addAction(self.add_directory_action)
        menu.addAction(self.add_files_action)
        if self.show_close_window:
            menu.addAction(self.close_window_action)
        menu.addSeparator()
        menu.addAction(self.play_file_action)
        menu.addAction(self.open_folder_action)
        menu.addSeparator()
        menu.addAction(self.save_action)
        menu.addAction(self.submit_acoustid_action)
        menu.addSeparator()
        menu.addAction(self.exit_action)
        menu = self.menuBar().addMenu(_("&Edit"))
        menu.addAction(self.cut_action)
        menu.addAction(self.paste_action)
        menu.addSeparator()
        menu.addAction(self.view_info_action)
        menu.addAction(self.remove_action)
        menu = self.menuBar().addMenu(_("&View"))
        menu.addAction(self.show_file_browser_action)
        menu.addAction(self.show_metadata_view_action)
        menu.addAction(self.show_cover_art_action)
        menu.addSeparator()
        menu.addAction(self.show_toolbar_action)
        menu.addAction(self.search_toolbar_toggle_action)
        if self.player:
            menu.addAction(self.player_toolbar_toggle_action)
        menu = self.menuBar().addMenu(_("&Options"))
        menu.addAction(self.enable_renaming_action)
        menu.addAction(self.enable_moving_action)
        menu.addAction(self.enable_tag_saving_action)
        menu.addSeparator()

        self.script_quick_selector_menu = QtWidgets.QMenu(_("&Select file naming script"))
        self.script_quick_selector_menu.setIcon(icontheme.lookup('document-open'))
        self.make_script_selector_menu()

        menu.addMenu(self.script_quick_selector_menu)
        menu.addAction(self.show_script_editor_action)
        menu.addSeparator()

        self.profile_quick_selector_menu = QtWidgets.QMenu(_("&Enable/disable profiles"))
        # self.profile_quick_selector_menu.setIcon(icontheme.lookup('document-open'))
        self.make_profile_selector_menu()

        menu.addMenu(self.profile_quick_selector_menu)
        menu.addSeparator()
        menu.addAction(self.options_action)
        menu = self.menuBar().addMenu(_("&Tools"))
        menu.addAction(self.refresh_action)
        menu.addMenu(self.cd_lookup_menu)
        menu.addAction(self.autotag_action)
        menu.addAction(self.analyze_action)
        menu.addAction(self.cluster_action)
        menu.addAction(self.browser_lookup_action)
        menu.addAction(self.similar_items_search_action)
        menu.addAction(self.album_other_versions_action)
        menu.addSeparator()
        menu.addAction(self.generate_fingerprints_action)
        menu.addAction(self.tags_from_filenames_action)
        menu.addAction(self.open_collection_in_browser_action)
        self.menuBar().addSeparator()
        menu = self.menuBar().addMenu(_("&Help"))
        menu.addAction(self.help_action)
        menu.addSeparator()
        menu.addAction(self.view_history_action)
        menu.addSeparator()
        if self.tagger.autoupdate_enabled:
            menu.addAction(self.check_update_action)
            menu.addSeparator()
        menu.addAction(self.support_forum_action)
        menu.addAction(self.report_bug_action)
        menu.addAction(self.view_log_action)
        menu.addSeparator()
        menu.addAction(self.donate_action)
        menu.addAction(self.about_action)

    def update_toolbar_style(self):
        config = get_config()
        style = QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly
        if config.setting['toolbar_show_labels']:
            style = QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        self.toolbar.setToolButtonStyle(style)
        if self.player:
            self.player.toolbar.setToolButtonStyle(style)

    def create_toolbar(self):
        self.create_search_toolbar()
        if self.player:
            self.create_player_toolbar()
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

        def add_toolbar_action(action):
            toolbar.addAction(action)
            widget = toolbar.widgetForAction(action)
            widget.setFocusPolicy(QtCore.Qt.FocusPolicy.TabFocus)
            widget.setAttribute(QtCore.Qt.WidgetAttribute.WA_MacShowFocusRect)

        config = get_config()
        for action in config.setting['toolbar_layout']:
            if action == 'cd_lookup_action':
                add_toolbar_action(self.cd_lookup_action)
                self._update_cd_lookup_button()
            elif action == 'separator':
                toolbar.addSeparator()
            else:
                try:
                    add_toolbar_action(getattr(self, action))
                except AttributeError:
                    log.warning("Warning: Unknown action name '%r' found in config. Ignored.", action)
        self.show_toolbar()

    def create_player_toolbar(self):
        """"Create a toolbar with internal player control elements"""
        toolbar = self.player.create_toolbar()
        self.addToolBar(QtCore.Qt.ToolBarArea.BottomToolBarArea, toolbar)
        if self._is_wayland:
            toolbar.setFloatable(False)  # https://bugreports.qt.io/browse/QTBUG-92191
        self.player_toolbar_toggle_action = toolbar.toggleViewAction()
        toolbar.hide()  # Hide by default

    def create_search_toolbar(self):
        config = get_config()
        self.search_toolbar = toolbar = self.addToolBar(_("Search"))
        self.search_toolbar_toggle_action = self.search_toolbar.toggleViewAction()
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
        self.search_edit.returnPressed.connect(self.trigger_search_action)
        self.search_edit.textChanged.connect(self.enable_search)
        hbox.addWidget(self.search_edit, 0)
        self.search_button = QtWidgets.QToolButton(search_panel)
        self.search_button.setAutoRaise(True)
        self.search_button.setDefaultAction(self.search_action)
        self.search_button.setIconSize(QtCore.QSize(22, 22))
        self.search_button.setAttribute(QtCore.Qt.WidgetAttribute.WA_MacShowFocusRect)

        # search button contextual menu, shortcut to toggle search options
        def search_button_menu(position):
            menu = QtWidgets.QMenu()
            opts = OrderedDict([
                ('use_adv_search_syntax', N_("&Advanced search")),
                ('builtin_search', N_("&Builtin search"))
            ])

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
        tw = self.toolbar.widgetForAction
        prev_action = None
        current_action = None
        # Setting toolbar widget tab-orders for accessibility
        config = get_config()
        for action in config.setting['toolbar_layout']:
            if action != 'separator':
                try:
                    current_action = tw(getattr(self, action))
                except AttributeError:
                    # No need to log warnings since we have already
                    # done it once in create_toolbar
                    pass

            if prev_action is not None and prev_action != current_action:
                tab_order(prev_action, current_action)

            prev_action = current_action

        tab_order(prev_action, self.search_combo)
        tab_order(self.search_combo, self.search_edit)
        tab_order(self.search_edit, self.search_button)
        # Panels
        tab_order(self.search_button, self.file_browser)
        self.panel.tab_order(tab_order, self.file_browser, self.metadata_box)

    def enable_submit(self, enabled):
        """Enable/disable the 'Submit fingerprints' action."""
        self.submit_acoustid_action.setEnabled(enabled)

    def enable_cluster(self, enabled):
        """Enable/disable the 'Cluster' action."""
        self.cluster_action.setEnabled(enabled)

    def enable_search(self):
        """Enable/disable the 'Search' action."""
        self.search_action.setEnabled(bool(self.search_edit.text()))

    def trigger_search_action(self):
        if self.search_action.isEnabled():
            self.search_action.trigger()

    def search_mbid_found(self, entity, mbid):
        self.search_edit.setText('%s:%s' % (entity, mbid))

    def search(self):
        """Search for album, artist or track on the MusicBrainz website."""
        text = self.search_edit.text()
        entity = self.search_combo.itemData(self.search_combo.currentIndex())
        config = get_config()
        self.tagger.search(text, entity,
                           config.setting['use_adv_search_syntax'],
                           mbid_matched_callback=self.search_mbid_found)

    def add_files(self):
        """Add files to the tagger."""
        current_directory = find_starting_directory()
        formats = []
        extensions = []
        for exts, name in supported_formats():
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
        files, _filter = QtWidgets.QFileDialog.getOpenFileNames(self, "", current_directory, ";;".join(formats))
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
            directory = QtWidgets.QFileDialog.getExistingDirectory(self, "", current_directory)
            if directory:
                dir_list.append(directory)
        else:
            file_dialog = MultiDirsSelectDialog(self, "", current_directory)
            if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                dir_list = file_dialog.selectedFiles()

        dir_count = len(dir_list)
        if dir_count:
            parent = os.path.dirname(dir_list[0]) if dir_count > 1 else dir_list[0]
            config.persist['current_directory'] = parent
            if dir_count > 1:
                self.set_statusbar_message(
                    N_("Adding multiple directories from '%(directory)s' …"),
                    {'directory': parent}
                )
            else:
                self.set_statusbar_message(
                    N_("Adding directory: '%(directory)s' …"),
                    {'directory': dir_list[0]}
                )

            self.tagger.add_paths(dir_list)

    def close_active_window(self):
        self.tagger.activeWindow().close()

    def show_about(self):
        return AboutDialog.show_instance(self)

    def show_options(self, page=None):
        options_dialog = OptionsDialog.show_instance(page, self)
        options_dialog.finished.connect(self.options_closed)
        if self.script_editor_dialog is not None:
            # Disable signal processing to avoid saving changes not processed with "Make It So!"
            for signal in self.script_editor_signals:
                signal.disconnect()

        return options_dialog

    def options_closed(self):
        if self.script_editor_dialog is not None:
            self.open_file_naming_script_editor()
            self.script_editor_dialog.show()
        else:
            self.show_script_editor_action.setEnabled(True)
        self.make_profile_selector_menu()
        self.make_script_selector_menu()

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

    def remove(self):
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
        folders = iter_unique(
            os.path.dirname(f.filename) for f
            in iter_files_from_objects(self.selected_objects))
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
        ret = QtWidgets.QMessageBox.question(self,
            _("Configuration Required"),
            _("Audio fingerprinting is not yet configured. Would you like to configure it now?"),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes)
        return ret == QtWidgets.QMessageBox.StandardButton.Yes

    def get_first_obj_with_type(self, type):
        for obj in self.selected_objects:
            if isinstance(obj, type):
                return obj
        return None

    def show_similar_items_search(self):
        obj = self.get_first_obj_with_type(Cluster)
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
        obj = self.get_first_obj_with_type(Cluster)
        if not obj:
            log.debug("show_more_albums expected a Cluster, got %r", obj)
            return
        dialog = AlbumSearchDialog(self, force_advanced_search=True)
        dialog.show_similar_albums(obj)
        dialog.exec()

    def show_album_other_versions(self):
        obj = self.get_first_obj_with_type(Album)
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
            f for f in iter_files_from_objects(self.selected_objects)
            if f.parent == self.tagger.unclustered_files
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
        if not self.selected_objects or (len(self.selected_objects) == 1
                and self.tagger.unclustered_files in self.selected_objects
                and not self.tagger.unclustered_files.files):
            self.panel.select_object(self.tagger.clusters)
        self.update_actions()

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
        ret = QtWidgets.QMessageBox.question(self,
            _("Browser integration not enabled"),
            _("Submitting releases to MusicBrainz requires the browser integration to be enabled. Do you want to enable the browser integration now?"),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes)
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
    def update_actions(self):
        can_remove = False
        can_save = False
        can_analyze = False
        can_refresh = False
        can_autotag = False
        can_submit = False
        single = self.selected_objects[0] if len(self.selected_objects) == 1 else None
        can_view_info = bool(single and single.can_view_info())
        can_browser_lookup = bool(single and single.can_browser_lookup())
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
                can_analyze = can_analyze or obj.can_analyze()
                can_autotag = can_autotag or obj.can_autotag()
                can_refresh = can_refresh or obj.can_refresh()
                can_remove = can_remove or obj.can_remove()
                can_save = can_save or obj.can_save()
                can_submit = can_submit or obj.can_submit()
                # Skip further loops if all values now True.
                if (
                    can_analyze
                    and can_autotag
                    and can_refresh
                    and can_remove
                    and can_save
                    and can_submit
                ):
                    break
        self.remove_action.setEnabled(can_remove)
        self.save_action.setEnabled(can_save)
        self.view_info_action.setEnabled(can_view_info)
        self.analyze_action.setEnabled(can_analyze)
        self.generate_fingerprints_action.setEnabled(have_files)
        self.refresh_action.setEnabled(can_refresh)
        self.autotag_action.setEnabled(can_autotag)
        self.browser_lookup_action.setEnabled(can_browser_lookup)
        self.play_file_action.setEnabled(have_files)
        self.open_folder_action.setEnabled(have_files)
        self.cut_action.setEnabled(have_objects)
        if self.submit_cluster_action:
            self.submit_cluster_action.setEnabled(can_submit)
        if self.submit_file_as_recording_action:
            self.submit_file_as_recording_action.setEnabled(have_files)
        if self.submit_file_as_release_action:
            self.submit_file_as_release_action.setEnabled(have_files)
        files = self.get_selected_or_unmatched_files()
        self.tags_from_filenames_action.setEnabled(bool(files))
        self.similar_items_search_action.setEnabled(is_file or is_cluster)
        self.track_search_action.setEnabled(is_file)
        self.album_search_action.setEnabled(is_cluster)
        self.album_other_versions_action.setEnabled(is_album)

    def update_selection(self, objects=None, new_selection=True, drop_album_caches=False):
        if self.ignore_selection_changes:
            return

        if objects is not None:
            self.selected_objects = objects
        else:
            objects = self.selected_objects

        self.update_actions()

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
                if obj.state == obj.ERROR:
                    msg = N_("%(filename)s (error: %(error)s)")
                    mparms = {
                        'filename': obj.filename,
                        'error': obj.errors[0] if obj.errors else ''
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
                            'error': file.errors[0] if file.errors else ''
                        }
                    else:
                        msg = N_("%(filename)s (%(similarity)d%%)")
                        mparms = {
                            'filename': file.filename,
                            'similarity': file.similarity * 100,
                        }
                    self.set_statusbar_message(msg, mparms, echo=None,
                                               history=None)
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
        self.update_script_editor_example_files()

    def refresh_metadatabox(self):
        self.tagger.window.metadata_box.selection_dirty = True
        self.tagger.window.metadata_box.update()

    def show_metadata_view(self):
        """Show/hide the metadata view (including the cover art box)."""
        show = self.show_metadata_view_action.isChecked()
        self.metadata_view.setVisible(show)
        self.show_cover_art_action.setEnabled(show)
        if show:
            self.update_selection()

    def show_cover_art(self):
        """Show/hide the cover art box."""
        show = self.show_cover_art_action.isChecked()
        self.cover_art_box.setVisible(show)
        if show:
            self.update_selection()

    def show_toolbar(self):
        """Show/hide the Action toolbar."""
        if self.show_toolbar_action.isChecked():
            self.toolbar.show()
        else:
            self.toolbar.hide()

    def show_file_browser(self):
        """Show/hide the file browser."""
        if self.show_file_browser_action.isChecked():
            sizes = self.panel.sizes()
            if sizes[0] == 0:
                sizes[0] = sum(sizes) // 4
                self.panel.setSizes(sizes)
            self.file_browser.show()
        else:
            self.file_browser.hide()

    def show_password_dialog(self, reply, authenticator):
        config = get_config()
        if reply.url().host() == config.setting['server_host']:
            ret = QtWidgets.QMessageBox.question(self,
                _("Authentication Required"),
                _("Picard needs authorization to access your personal data on the MusicBrainz server. Would you like to log in now?"),
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.Yes)
            if ret == QtWidgets.QMessageBox.StandardButton.Yes:
                self.tagger.mb_login(self.on_mb_login_finished)
        else:
            dialog = PasswordDialog(authenticator, reply, parent=self)
            dialog.exec()

    def on_mb_login_finished(self, successful, error_msg):
        if successful:
            log.debug("MusicBrainz authentication finished successfully")
        else:
            log.info("MusicBrainz authentication failed: %s", error_msg)
            QtWidgets.QMessageBox.critical(self,
                _("Authentication failed"),
                _("Login failed: %s") % error_msg)

    def show_proxy_dialog(self, proxy, authenticator):
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
        self.paste_action.setEnabled(bool(self.selected_objects))

    def paste(self):
        selected_objects = self.selected_objects
        if not selected_objects:
            target = self.tagger.unclustered_files
        else:
            target = selected_objects[0]
        self.paste_files(target)
        self.paste_action.setEnabled(False)

    def do_update_check(self):
        self.check_for_update(True)

    def auto_update_check(self):
        config = get_config()
        check_for_updates = config.setting['check_for_updates']
        update_check_days = config.setting['update_check_days']
        last_update_check = config.persist['last_update_check']
        update_level = config.setting['update_level']
        today = datetime.date.today().toordinal()
        do_auto_update_check = check_for_updates and update_check_days > 0 and today >= last_update_check + update_check_days
        log.debug("%(check_status)s startup check for program updates.  Today: %(today_date)s, Last check: %(last_check)s (Check interval: %(check_interval)s days), Update level: %(update_level)s (%(update_level_name)s)", {
            'check_status': 'Initiating' if do_auto_update_check else 'Skipping',
            'today_date': datetime.date.today(),
            'last_check': str(datetime.date.fromordinal(last_update_check)) if last_update_check > 0 else 'never',
            'check_interval': update_check_days,
            'update_level': update_level,
            'update_level_name': PROGRAM_UPDATE_LEVELS[update_level]['name'] if update_level in PROGRAM_UPDATE_LEVELS else 'unknown',
        })
        if do_auto_update_check:
            self.check_for_update(False)

    def check_for_update(self, show_always):
        config = get_config()
        self.tagger.updatecheckmanager.check_update(
            show_always=show_always,
            update_level=config.setting['update_level'],
            callback=update_last_check_date
        )

    def check_and_repair_naming_scripts(self):
        """Check the 'file_renaming_scripts' config setting to ensure that the list of scripts
        is not empty.  Check that the 'selected_file_naming_script_id' config setting points to
        a valid file naming script.
        """
        config = get_config()
        script_key = 'file_renaming_scripts'
        if not config.setting[script_key]:
            config.setting[script_key] = {
                script['id']: script.to_dict()
                for script in get_file_naming_script_presets()
            }
        naming_script_ids = list(config.setting[script_key])
        script_id_key = 'selected_file_naming_script_id'
        if config.setting[script_id_key] not in naming_script_ids:
            config.setting[script_id_key] = naming_script_ids[0]

    def check_and_repair_profiles(self):
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

    def make_script_selector_menu(self):
        """Update the sub-menu of available file naming scripts.
        """
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
            script_action.triggered.connect(partial(self.select_new_naming_script, id))
            script_action.setCheckable(True)
            script_action.setChecked(id == selected_script_id)
            self.script_quick_selector_menu.addAction(script_action)
            group.addAction(script_action)

        for (id, naming_script) in sorted(naming_scripts.items(), key=lambda item: item[1]['title']):
            _add_menu_item(naming_script['title'], id)

    def select_new_naming_script(self, id):
        """Update the currently selected naming script ID in the settings.

        Args:
            id (str): ID of the selected file naming script
        """
        config = get_config()
        log.debug("Setting naming script to: %s", id)
        config.setting['selected_file_naming_script_id'] = id
        self.make_script_selector_menu()
        if self.script_editor_dialog:
            self.script_editor_dialog.set_selected_script_id(id)

    def open_file_naming_script_editor(self):
        """Open the file naming script editor / manager in a new window.
        """
        self.examples = ScriptEditorExamples(tagger=self.tagger)
        self.script_editor_dialog = ScriptEditorDialog.show_instance(parent=self, examples=self.examples)
        self.script_editor_dialog.signal_save.connect(self.script_editor_save)
        self.script_editor_dialog.signal_selection_changed.connect(self.update_selector_from_script_editor)
        self.script_editor_dialog.signal_index_changed.connect(self.script_editor_index_changed)
        self.script_editor_dialog.finished.connect(self.script_editor_closed)
        # Create list of signals to disconnect when opening Options dialog.
        # Do not include `finished` because that is still used to clean up
        # locally when the editor is closed from the Options dialog.
        self.script_editor_signals = [
            self.script_editor_dialog.signal_save,
            self.script_editor_dialog.signal_selection_changed,
            self.script_editor_dialog.signal_index_changed,
        ]
        self.show_script_editor_action.setEnabled(False)

    def script_editor_save(self):
        """Process "signal_save" signal from the script editor.
        """
        self.make_script_selector_menu()

    def script_editor_closed(self):
        """Process "finished" signal from the script editor.
        """
        self.show_script_editor_action.setEnabled(True)
        self.script_editor_dialog = None
        self.make_script_selector_menu()

    def update_script_editor_example_files(self):
        """Update the list of example files for the file naming script editor.
        """
        if self.examples:
            self.examples.update_sample_example_files()
            self.update_script_editor_examples()

    def update_script_editor_examples(self):
        """Update the examples for the file naming script editor, using current settings.
        """
        if self.examples:
            config = get_config()
            override = {
                "rename_files": config.setting["rename_files"],
                "move_files": config.setting["move_files"],
            }
            self.examples.update_examples(override=override)
            if self.script_editor_dialog:
                self.script_editor_dialog.display_examples()

    def script_editor_index_changed(self):
        """Process "signal_index_changed" signal from the script editor.
        """
        self.script_editor_save()

    def update_selector_from_script_editor(self):
        """Process "signal_selection_changed" signal from the script editor.
        """
        self.script_editor_save()

    def make_profile_selector_menu(self):
        """Update the sub-menu of available option profiles.
        """
        config = get_config()
        option_profiles = config.profiles[SettingConfigSection.PROFILES_KEY]
        if not option_profiles:
            self.profile_quick_selector_menu.setDisabled(True)
            return
        self.profile_quick_selector_menu.setDisabled(False)
        self.profile_quick_selector_menu.clear()

        group = QtGui.QActionGroup(self.profile_quick_selector_menu)
        group.setExclusive(False)

        def _add_menu_item(title, enabled, profile_id):
            profile_action = QtGui.QAction(title, self.profile_quick_selector_menu)
            profile_action.triggered.connect(partial(self.update_profile_selection, profile_id))
            profile_action.setCheckable(True)
            profile_action.setChecked(enabled)
            self.profile_quick_selector_menu.addAction(profile_action)
            group.addAction(profile_action)

        for profile in option_profiles:
            _add_menu_item(profile['title'], profile['enabled'], profile['id'])

    def update_profile_selection(self, profile_id):
        """Toggle the enabled state of the selected profile.

        Args:
            profile_id (str): ID code of the profile to modify
        """
        config = get_config()
        option_profiles = config.profiles[SettingConfigSection.PROFILES_KEY]
        for profile in option_profiles:
            if profile['id'] == profile_id:
                profile['enabled'] = not profile['enabled']
                self.make_script_selector_menu()
                return

    def show_new_user_dialog(self):
        config = get_config()
        if config.setting['show_new_user_dialog']:
            msg = NewUserDialog(self)
            config.setting['show_new_user_dialog'] = msg.show()

    def check_for_plugin_update(self):
        config = get_config()
        if config.setting['check_for_plugin_updates']:
            self.tagger.pluginmanager.check_update()

    def show_plugin_update_dialog(self, plugin_names):
        if not plugin_names:
            return

        msg = PluginUpdatesDialog(self, plugin_names)
        show_options_page, perform_check = msg.show()
        config = get_config()
        config.setting['check_for_plugin_updates'] = perform_check
        if show_options_page:
            self.show_plugins_options_page()

    def show_plugins_options_page(self):
        self.show_options(page='plugins')


def update_last_check_date(is_success):
    if is_success:
        config = get_config()
        config.persist['last_update_check'] = datetime.date.today().toordinal()
    else:
        log.debug('The update check was unsuccessful. The last update date will not be changed.')
