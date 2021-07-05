# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2007 Nikolai Prokoschenko
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2008 Will
# Copyright (C) 2008-2010, 2015, 2018-2021 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 David Hilton
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013, 2015-2017 Wieland Hoffmann
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2013-2021 Laurent Monin
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
# Copyright (C) 2018, 2021 Bob Swift
# Copyright (C) 2019 Timur Enikeev
# Copyright (C) 2020 Gabriel Ferreira
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
import os.path

from PyQt5 import (
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
    icontheme,
    iter_files_from_objects,
    iter_unique,
    restore_method,
    thread,
    throttle,
    webbrowser2,
)
from picard.util.cdrom import (
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
from picard.ui.itemviews import MainPanel
from picard.ui.logview import (
    HistoryView,
    LogView,
)
from picard.ui.metadatabox import MetadataBox
from picard.ui.options.dialog import OptionsDialog
from picard.ui.passworddialog import (
    PasswordDialog,
    ProxyDialog,
)
from picard.ui.profileeditor import ProfileEditorDialog
from picard.ui.scripteditor import (
    ScriptEditorDialog,
    ScriptEditorExamples,
    user_script_title,
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


class IgnoreSelectionContext:
    """Context manager for holding a boolean value, indicating whether selection changes are performed or not.
    By default the context resolves to False. If entered it is True. This allows
    to temporarily set a state on a block of code like:

        ignore_changes = IgnoreSelectionContext()
        # Initially ignore_changes is True
        with ignore_changes:
            # Perform some tasks with ignore_changes now being True
            ...
        # ignore_changes is False again
    """

    def __init__(self, onexit=None):
        self._entered = 0
        self._onexit = onexit

    def __enter__(self):
        self._entered += 1

    def __exit__(self, type, value, tb):
        self._entered -= 1
        if self._onexit:
            self._onexit()

    def __bool__(self):
        return self._entered > 0


class MainWindow(QtWidgets.QMainWindow, PreserveGeometry):

    defaultsize = QtCore.QSize(780, 560)
    selection_updated = QtCore.pyqtSignal(object)
    ready_for_display = QtCore.pyqtSignal()

    options = [
        Option("persist", "window_state", QtCore.QByteArray()),
        BoolOption("persist", "window_maximized", False),
        BoolOption("persist", "view_metadata_view", True),
        BoolOption("persist", "view_cover_art", True),
        BoolOption("persist", "view_toolbar", True),
        BoolOption("persist", "view_file_browser", False),
        TextOption("persist", "current_directory", ""),
        FloatOption("persist", "mediaplayer_playback_rate", 1.0),
        IntOption("persist", "mediaplayer_volume", 50),
    ]

    def __init__(self, parent=None, disable_player=False):
        super().__init__(parent)
        self.__shown = False
        self.selected_objects = []
        self.ignore_selection_changes = IgnoreSelectionContext(self.update_selection)
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

        main_layout = QtWidgets.QSplitter(QtCore.Qt.Vertical)
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
            event.key() == QtCore.Qt.Key_Backspace and \
            event.modifiers() & QtCore.Qt.ControlModifier
        if event.matches(QtGui.QKeySequence.Delete) or is_forward_delete:
            if self.metadata_box.hasFocus():
                self.metadata_box.remove_selected_tags()
            else:
                self.remove()
        elif event.matches(QtGui.QKeySequence.Find):
            self.search_edit.setFocus(True)
        else:
            super().keyPressEvent(event)

    def show(self):
        self.restoreWindowState()
        super().show()
        if self.tagger.autoupdate_enabled:
            self.auto_update_check()
        self.metadata_box.restore_state()

    def showEvent(self, event):
        if not self.__shown:
            self.ready_for_display.emit()
            self.__shown = True
        super().showEvent(event)

    def closeEvent(self, event):
        config = get_config()
        if config.setting["quit_confirmation"] and not self.show_quit_confirmation():
            event.ignore()
            return
        if self.player:
            config.persist['mediaplayer_playback_rate'] = self.player.playback_rate()
            config.persist['mediaplayer_volume'] = self.player.volume()
        self.saveWindowState()
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
            msg.setIcon(QMessageBox.Question)
            msg.setWindowModality(QtCore.Qt.WindowModal)
            msg.setWindowTitle(_("Unsaved Changes"))
            msg.setText(_("Are you sure you want to quit Picard?"))
            txt = ngettext(
                "There is %d unsaved file. Closing Picard will lose all unsaved changes.",
                "There are %d unsaved files. Closing Picard will lose all unsaved changes.",
                unsaved_files) % unsaved_files
            msg.setInformativeText(txt)
            cancel = msg.addButton(QMessageBox.Cancel)
            msg.setDefaultButton(cancel)
            msg.addButton(_("&Quit Picard"), QMessageBox.YesRole)
            ret = msg.exec_()

            if ret == QMessageBox.Cancel:
                return False

        return True

    def saveWindowState(self):
        config = get_config()
        config.persist["window_state"] = self.saveState()
        isMaximized = int(self.windowState()) & QtCore.Qt.WindowMaximized != 0
        self.save_geometry()
        config.persist["window_maximized"] = isMaximized
        config.persist["view_metadata_view"] = self.show_metadata_view_action.isChecked()
        config.persist["view_cover_art"] = self.show_cover_art_action.isChecked()
        config.persist["view_toolbar"] = self.show_toolbar_action.isChecked()
        config.persist["view_file_browser"] = self.show_file_browser_action.isChecked()
        self.file_browser.save_state()
        self.panel.save_state()
        self.metadata_box.save_state()

    @restore_method
    def restoreWindowState(self):
        config = get_config()
        self.restoreState(config.persist["window_state"])
        self.restore_geometry()
        if config.persist["window_maximized"]:
            self.setWindowState(QtCore.Qt.WindowMaximized)
        splitters = config.persist["splitters_MainWindow"]
        if splitters is None or 'main_window_bottom_splitter' not in splitters:
            self.centralWidget().setSizes([366, 194])
        self.file_browser.restore_state()

    def create_statusbar(self):
        """Creates a new status bar."""
        self.statusBar().showMessage(_("Ready"))
        infostatus = InfoStatus(self)
        self.listening_label = QtWidgets.QLabel()
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
                pending_files=pending_files, pending_requests=pending_requests)

    def update_statusbar_listen_port(self, listen_port):
        if listen_port:
            self.listening_label.setVisible(True)
            self.listening_label.setText(_(" Listening on port %(port)d ") % {"port": listen_port})
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
            if not config.setting["acoustid_apikey"]:
                msg = QtWidgets.QMessageBox(self)
                msg.setIcon(QtWidgets.QMessageBox.Information)
                msg.setWindowModality(QtCore.Qt.WindowModal)
                msg.setWindowTitle(_("AcoustID submission not configured"))
                msg.setText(_(
                    "You need to configure your AcoustID API key before you can submit fingerprints."))
                open_options = QtWidgets.QPushButton(
                    icontheme.lookup('preferences-desktop'), _("Open AcoustID options"))
                msg.addButton(QtWidgets.QMessageBox.Cancel)
                msg.addButton(open_options, QtWidgets.QMessageBox.YesRole)
                msg.exec_()
                if msg.clickedButton() == open_options:
                    self.show_options("fingerprinting")
            else:
                self.tagger.acoustidmanager.submit()

    def create_actions(self):
        config = get_config()
        self.options_action = QtWidgets.QAction(icontheme.lookup('preferences-desktop'), _("&Options..."), self)
        self.options_action.setMenuRole(QtWidgets.QAction.PreferencesRole)
        self.options_action.triggered.connect(self.show_options)

        self.show_script_editor_action = QtWidgets.QAction(_("Open &file naming script editor..."))
        self.show_script_editor_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+S")))
        self.show_script_editor_action.triggered.connect(self.open_file_naming_script_editor)

        self.show_profile_editor_action = QtWidgets.QAction(_("Open option &profile editor..."))
        self.show_profile_editor_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+P")))
        self.show_profile_editor_action.triggered.connect(self.open_profile_editor)

        self.cut_action = QtWidgets.QAction(icontheme.lookup('edit-cut', icontheme.ICON_SIZE_MENU), _("&Cut"), self)
        self.cut_action.setShortcut(QtGui.QKeySequence.Cut)
        self.cut_action.setEnabled(False)
        self.cut_action.triggered.connect(self.cut)

        self.paste_action = QtWidgets.QAction(icontheme.lookup('edit-paste', icontheme.ICON_SIZE_MENU), _("&Paste"), self)
        self.paste_action.setShortcut(QtGui.QKeySequence.Paste)
        self.paste_action.setEnabled(False)
        self.paste_action.triggered.connect(self.paste)

        self.help_action = QtWidgets.QAction(_("&Help..."), self)
        self.help_action.setShortcut(QtGui.QKeySequence.HelpContents)
        self.help_action.triggered.connect(self.show_help)

        self.about_action = QtWidgets.QAction(_("&About..."), self)
        self.about_action.setMenuRole(QtWidgets.QAction.AboutRole)
        self.about_action.triggered.connect(self.show_about)

        self.donate_action = QtWidgets.QAction(_("&Donate..."), self)
        self.donate_action.triggered.connect(self.open_donation_page)

        self.report_bug_action = QtWidgets.QAction(_("&Report a Bug..."), self)
        self.report_bug_action.triggered.connect(self.open_bug_report)

        self.support_forum_action = QtWidgets.QAction(_("&Support Forum..."), self)
        self.support_forum_action.triggered.connect(self.open_support_forum)

        self.add_files_action = QtWidgets.QAction(icontheme.lookup('document-open'), _("&Add Files..."), self)
        self.add_files_action.setStatusTip(_("Add files to the tagger"))
        # TR: Keyboard shortcut for "Add Files..."
        self.add_files_action.setShortcut(QtGui.QKeySequence.Open)
        self.add_files_action.triggered.connect(self.add_files)

        self.add_directory_action = QtWidgets.QAction(icontheme.lookup('folder'), _("Add Fold&er..."), self)
        self.add_directory_action.setStatusTip(_("Add a folder to the tagger"))
        # TR: Keyboard shortcut for "Add Directory..."
        self.add_directory_action.setShortcut(QtGui.QKeySequence(_("Ctrl+E")))
        self.add_directory_action.triggered.connect(self.add_directory)

        if self.show_close_window:
            self.close_window_action = QtWidgets.QAction(_("Close Window"), self)
            self.close_window_action.setShortcut(QtGui.QKeySequence(_("Ctrl+W")))
            self.close_window_action.triggered.connect(self.close_active_window)

        self.save_action = QtWidgets.QAction(icontheme.lookup('document-save'), _("&Save"), self)
        self.save_action.setStatusTip(_("Save selected files"))
        # TR: Keyboard shortcut for "Save"
        self.save_action.setShortcut(QtGui.QKeySequence.Save)
        self.save_action.setEnabled(False)
        self.save_action.triggered.connect(self.save)

        self.submit_acoustid_action = QtWidgets.QAction(icontheme.lookup('acoustid-fingerprinter'), _("S&ubmit AcoustIDs"), self)
        self.submit_acoustid_action.setStatusTip(_("Submit acoustic fingerprints"))
        self.submit_acoustid_action.setEnabled(False)
        self.submit_acoustid_action.triggered.connect(self._on_submit_acoustid)

        self.exit_action = QtWidgets.QAction(_("E&xit"), self)
        self.exit_action.setMenuRole(QtWidgets.QAction.QuitRole)
        # TR: Keyboard shortcut for "Exit"
        self.exit_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Q")))
        self.exit_action.triggered.connect(self.close)

        self.remove_action = QtWidgets.QAction(icontheme.lookup('list-remove'), _("&Remove"), self)
        self.remove_action.setStatusTip(_("Remove selected files/albums"))
        self.remove_action.setEnabled(False)
        self.remove_action.triggered.connect(self.remove)

        self.browser_lookup_action = QtWidgets.QAction(icontheme.lookup('lookup-musicbrainz'), _("Lookup in &Browser"), self)
        self.browser_lookup_action.setStatusTip(_("Lookup selected item on MusicBrainz website"))
        self.browser_lookup_action.setEnabled(False)
        # TR: Keyboard shortcut for "Lookup in Browser"
        self.browser_lookup_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+L")))
        self.browser_lookup_action.triggered.connect(self.browser_lookup)

        if addrelease.is_available():
            self.submit_cluster_action = QtWidgets.QAction(_("Submit cluster as release..."), self)
            self.submit_cluster_action.setStatusTip(_("Submit cluster as a new release to MusicBrainz"))
            self.submit_cluster_action.setEnabled(False)
            self.submit_cluster_action.triggered.connect(self.submit_cluster)

            self.submit_file_as_recording_action = QtWidgets.QAction(_("Submit file as standalone recording..."), self)
            self.submit_file_as_recording_action.setStatusTip(_("Submit file as a new recording to MusicBrainz"))
            self.submit_file_as_recording_action.setEnabled(False)
            self.submit_file_as_recording_action.triggered.connect(self.submit_file)

            self.submit_file_as_release_action = QtWidgets.QAction(_("Submit file as release..."), self)
            self.submit_file_as_release_action.setStatusTip(_("Submit file as a new release to MusicBrainz"))
            self.submit_file_as_release_action.setEnabled(False)
            self.submit_file_as_release_action.triggered.connect(partial(self.submit_file, as_release=True))
        else:
            self.submit_cluster_action = None
            self.submit_file_as_recording_action = None
            self.submit_file_as_release_action = None

        self.album_search_action = QtWidgets.QAction(icontheme.lookup('system-search'), _("Search for similar albums..."), self)
        self.album_search_action.setStatusTip(_("View similar releases and optionally choose a different release"))
        self.album_search_action.triggered.connect(self.show_more_albums)

        self.track_search_action = QtWidgets.QAction(icontheme.lookup('system-search'), _("Search for similar tracks..."), self)
        self.track_search_action.setStatusTip(_("View similar tracks and optionally choose a different release"))
        self.track_search_action.setEnabled(False)
        self.track_search_action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
        self.track_search_action.triggered.connect(self.show_more_tracks)

        self.show_file_browser_action = QtWidgets.QAction(_("File &Browser"), self)
        self.show_file_browser_action.setCheckable(True)
        if config.persist["view_file_browser"]:
            self.show_file_browser_action.setChecked(True)
        self.show_file_browser_action.setShortcut(QtGui.QKeySequence(_("Ctrl+B")))
        self.show_file_browser_action.triggered.connect(self.show_file_browser)

        self.show_metadata_view_action = QtWidgets.QAction(_("&Metadata"), self)
        self.show_metadata_view_action.setCheckable(True)
        if config.persist["view_metadata_view"]:
            self.show_metadata_view_action.setChecked(True)
        self.show_metadata_view_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+M")))
        self.show_metadata_view_action.triggered.connect(self.show_metadata_view)

        self.show_cover_art_action = QtWidgets.QAction(_("&Cover Art"), self)
        self.show_cover_art_action.setCheckable(True)
        if config.persist["view_cover_art"]:
            self.show_cover_art_action.setChecked(True)
        self.show_cover_art_action.setEnabled(self.show_metadata_view_action.isChecked())
        self.show_cover_art_action.triggered.connect(self.show_cover_art)

        self.show_toolbar_action = QtWidgets.QAction(_("&Actions"), self)
        self.show_toolbar_action.setCheckable(True)
        if config.persist["view_toolbar"]:
            self.show_toolbar_action.setChecked(True)
        self.show_toolbar_action.triggered.connect(self.show_toolbar)

        self.search_action = QtWidgets.QAction(icontheme.lookup('system-search'), _("Search"), self)
        self.search_action.setEnabled(False)
        self.search_action.triggered.connect(self.search)

        self.cd_lookup_action = QtWidgets.QAction(icontheme.lookup('media-optical'), _("Lookup &CD..."), self)
        self.cd_lookup_action.setStatusTip(_("Lookup the details of the CD in your drive"))
        # TR: Keyboard shortcut for "Lookup CD"
        self.cd_lookup_action.setShortcut(QtGui.QKeySequence(_("Ctrl+K")))
        self.cd_lookup_action.triggered.connect(self.tagger.lookup_cd)

        self.cd_lookup_menu = QtWidgets.QMenu(_("Lookup &CD..."))
        self.cd_lookup_menu.triggered.connect(self.tagger.lookup_cd)
        self.cd_lookup_action.setEnabled(False)
        if discid is None:
            log.warning("CDROM: discid library not found - Lookup CD functionality disabled")
        else:
            thread.run_task(get_cdrom_drives, self._update_cd_lookup_actions)

        self.analyze_action = QtWidgets.QAction(icontheme.lookup('picard-analyze'), _("&Scan"), self)
        self.analyze_action.setStatusTip(_("Use AcoustID audio fingerprint to identify the files by the actual music, even if they have no metadata"))
        self.analyze_action.setEnabled(False)
        self.analyze_action.setToolTip(_('Identify the file using its AcoustID audio fingerprint'))
        # TR: Keyboard shortcut for "Analyze"
        self.analyze_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Y")))
        self.analyze_action.triggered.connect(self.analyze)

        self.generate_fingerprints_action = QtWidgets.QAction(icontheme.lookup('fingerprint'), _("&Generate AcoustID Fingerprints"), self)
        self.generate_fingerprints_action.setIconText(_("Generate Fingerprints"))
        self.generate_fingerprints_action.setStatusTip(_("Generate the AcoustID audio fingerprints for the selected files without doing a lookup"))
        self.generate_fingerprints_action.setEnabled(False)
        self.generate_fingerprints_action.setToolTip(_('Generate the AcoustID audio fingerprints for the selected files'))
        self.generate_fingerprints_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+Y")))
        self.generate_fingerprints_action.triggered.connect(self.generate_fingerprints)

        self.cluster_action = QtWidgets.QAction(icontheme.lookup('picard-cluster'), _("Cl&uster"), self)
        self.cluster_action.setStatusTip(_("Cluster files into album clusters"))
        self.cluster_action.setEnabled(False)
        # TR: Keyboard shortcut for "Cluster"
        self.cluster_action.setShortcut(QtGui.QKeySequence(_("Ctrl+U")))
        self.cluster_action.triggered.connect(self.cluster)

        self.autotag_action = QtWidgets.QAction(icontheme.lookup('picard-auto-tag'), _("&Lookup"), self)
        tip = _("Lookup selected items in MusicBrainz")
        self.autotag_action.setToolTip(tip)
        self.autotag_action.setStatusTip(tip)
        self.autotag_action.setEnabled(False)
        # TR: Keyboard shortcut for "Lookup"
        self.autotag_action.setShortcut(QtGui.QKeySequence(_("Ctrl+L")))
        self.autotag_action.triggered.connect(self.autotag)

        self.view_info_action = QtWidgets.QAction(icontheme.lookup('picard-edit-tags'), _("&Info..."), self)
        self.view_info_action.setEnabled(False)
        # TR: Keyboard shortcut for "Info"
        self.view_info_action.setShortcut(QtGui.QKeySequence(_("Ctrl+I")))
        self.view_info_action.triggered.connect(self.view_info)

        self.refresh_action = QtWidgets.QAction(icontheme.lookup('view-refresh', icontheme.ICON_SIZE_MENU), _("&Refresh"), self)
        self.refresh_action.setShortcut(QtGui.QKeySequence(_("Ctrl+R")))
        self.refresh_action.triggered.connect(self.refresh)

        self.enable_renaming_action = QtWidgets.QAction(_("&Rename Files"), self)
        self.enable_renaming_action.setCheckable(True)
        self.enable_renaming_action.setChecked(config.setting["rename_files"])
        self.enable_renaming_action.triggered.connect(self.toggle_rename_files)

        self.enable_moving_action = QtWidgets.QAction(_("&Move Files"), self)
        self.enable_moving_action.setCheckable(True)
        self.enable_moving_action.setChecked(config.setting["move_files"])
        self.enable_moving_action.triggered.connect(self.toggle_move_files)

        self.enable_tag_saving_action = QtWidgets.QAction(_("Save &Tags"), self)
        self.enable_tag_saving_action.setCheckable(True)
        self.enable_tag_saving_action.setChecked(not config.setting["dont_write_tags"])
        self.enable_tag_saving_action.triggered.connect(self.toggle_tag_saving)

        self.tags_from_filenames_action = QtWidgets.QAction(icontheme.lookup('picard-tags-from-filename'), _("Tags From &File Names..."), self)
        self.tags_from_filenames_action.setIconText(_("Parse File Names..."))
        self.tags_from_filenames_action.setToolTip(_('Set tags based on the file names'))
        self.tags_from_filenames_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+T")))
        self.tags_from_filenames_action.triggered.connect(self.open_tags_from_filenames)
        self.tags_from_filenames_action.setEnabled(False)

        self.open_collection_in_browser_action = QtWidgets.QAction(_("&Open My Collections in Browser"), self)
        self.open_collection_in_browser_action.triggered.connect(self.open_collection_in_browser)
        self.open_collection_in_browser_action.setEnabled(config.setting["username"] != '')

        self.view_log_action = QtWidgets.QAction(_("View &Error/Debug Log"), self)
        self.view_log_action.triggered.connect(self.show_log)
        # TR: Keyboard shortcut for "View Error/Debug Log"
        self.view_log_action.setShortcut(QtGui.QKeySequence(_("Ctrl+G")))

        self.view_history_action = QtWidgets.QAction(_("View Activity &History"), self)
        self.view_history_action.triggered.connect(self.show_history)
        # TR: Keyboard shortcut for "View Activity History"
        # On macOS ⌘+H is a system shortcut to hide the window. Use ⌘+Shift+H instead.
        self.view_history_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Shift+H") if IS_MACOS else _("Ctrl+H")))

        webservice_manager = self.tagger.webservice.manager
        webservice_manager.authenticationRequired.connect(self.show_password_dialog)
        webservice_manager.proxyAuthenticationRequired.connect(self.show_proxy_dialog)

        self.play_file_action = QtWidgets.QAction(icontheme.lookup('play-music'), _("Open in &Player"), self)
        self.play_file_action.setStatusTip(_("Play the file in your default media player"))
        self.play_file_action.setEnabled(False)
        self.play_file_action.triggered.connect(self.play_file)

        self.open_folder_action = QtWidgets.QAction(icontheme.lookup('folder', icontheme.ICON_SIZE_MENU), _("Open Containing &Folder"), self)
        self.open_folder_action.setStatusTip(_("Open the containing folder in your file explorer"))
        self.open_folder_action.setEnabled(False)
        self.open_folder_action.triggered.connect(self.open_folder)

        if self.tagger.autoupdate_enabled:
            self.check_update_action = QtWidgets.QAction(_("&Check for Update…"), self)
            self.check_update_action.setMenuRole(QtWidgets.QAction.ApplicationSpecificRole)
            self.check_update_action.triggered.connect(self.do_update_check)

    def _update_cd_lookup_actions(self, result=None, error=None):
        if error:
            log.error("CDROM: Error on CD-ROM drive detection: %r", error)
        else:
            self.update_cd_lookup_drives(result)

    def update_cd_lookup_drives(self, drives):
        if not drives:
            log.warning("CDROM: No CD-ROM drives found - Lookup CD functionality disabled")
        else:
            config = get_config()
            shortcut_drive = config.setting["cd_lookup_device"].split(",")[0] if len(drives) > 1 else ""
            self.cd_lookup_action.setEnabled(discid is not None)
            self.cd_lookup_menu.clear()
            for drive in drives:
                action = self.cd_lookup_menu.addAction(drive)
                action.setData(drive)
                if drive == shortcut_drive:
                    # Clear existing shortcode on main action and assign it to sub-action
                    self.cd_lookup_action.setShortcut(QtGui.QKeySequence())
                    action.setShortcut(QtGui.QKeySequence(_("Ctrl+K")))
        self._update_cd_lookup_button()

    def _update_cd_lookup_button(self):
        if len(self.cd_lookup_menu.actions()) > 1:
            button = self.toolbar.widgetForAction(self.cd_lookup_action)
            if button:
                button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
            self.cd_lookup_action.setMenu(self.cd_lookup_menu)
        else:
            self.cd_lookup_action.setMenu(None)

    def toggle_rename_files(self, checked):
        config = get_config()
        config.setting["rename_files"] = checked
        self.update_script_editor_examples()

    def toggle_move_files(self, checked):
        config = get_config()
        config.setting["move_files"] = checked
        self.update_script_editor_examples()

    def toggle_tag_saving(self, checked):
        config = get_config()
        config.setting["dont_write_tags"] = not checked

    def get_selected_or_unmatched_files(self):
        files = self.tagger.get_files_from_objects(self.selected_objects)
        if not files:
            files = self.tagger.unclustered_files.files
        return files

    def open_tags_from_filenames(self):
        files = self.get_selected_or_unmatched_files()
        if files:
            dialog = TagsFromFileNamesDialog(files, self)
            dialog.exec_()

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

        self.script_quick_selector_menu = QtWidgets.QMenu(_("&Select file naming script"))
        self.script_quick_selector_menu.setIcon(icontheme.lookup('document-open'))
        self.make_script_selector_menu()

        menu.addMenu(self.script_quick_selector_menu)
        menu.addSeparator()
        menu.addAction(self.show_script_editor_action)
        menu.addSeparator()
        menu.addAction(self.show_profile_editor_action)
        menu.addSeparator()
        menu.addAction(self.options_action)
        menu = self.menuBar().addMenu(_("&Tools"))
        menu.addAction(self.refresh_action)
        menu.addAction(self.cd_lookup_action)
        menu.addAction(self.autotag_action)
        menu.addAction(self.analyze_action)
        menu.addAction(self.cluster_action)
        menu.addAction(self.browser_lookup_action)
        menu.addAction(self.track_search_action)
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
        if config.setting["toolbar_show_labels"]:
            self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            if self.player:
                self.player.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        else:
            self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
            if self.player:
                self.player.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)

    def create_toolbar(self):
        self.create_search_toolbar()
        if self.player:
            self.create_player_toolbar()
        self.create_action_toolbar()

    def create_action_toolbar(self):
        if self.toolbar:
            self.toolbar.clear()
            self.removeToolBar(self.toolbar)
        self.toolbar = toolbar = QtWidgets.QToolBar(_("Actions"))
        self.insertToolBar(self.search_toolbar, self.toolbar)
        self.update_toolbar_style()
        toolbar.setObjectName("main_toolbar")
        if IS_MACOS:
            self.toolbar.setMovable(False)

        def add_toolbar_action(action):
            toolbar.addAction(action)
            widget = toolbar.widgetForAction(action)
            widget.setFocusPolicy(QtCore.Qt.TabFocus)
            widget.setAttribute(QtCore.Qt.WA_MacShowFocusRect)

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
                    log.warning('Warning: Unknown action name "%r" found in config. Ignored.', action)
        self.show_toolbar()

    def create_player_toolbar(self):
        """"Create a toolbar with internal player control elements"""
        toolbar = self.player.create_toolbar()
        self.addToolBar(QtCore.Qt.BottomToolBarArea, toolbar)
        self.player_toolbar_toggle_action = toolbar.toggleViewAction()
        toolbar.hide()  # Hide by default

    def create_search_toolbar(self):
        config = get_config()
        self.search_toolbar = toolbar = self.addToolBar(_("Search"))
        self.search_toolbar_toggle_action = self.search_toolbar.toggleViewAction()
        toolbar.setObjectName("search_toolbar")
        if IS_MACOS:
            self.search_toolbar.setMovable(False)

        search_panel = QtWidgets.QWidget(toolbar)
        hbox = QtWidgets.QHBoxLayout(search_panel)
        self.search_combo = QtWidgets.QComboBox(search_panel)
        self.search_combo.addItem(_("Album"), "album")
        self.search_combo.addItem(_("Artist"), "artist")
        self.search_combo.addItem(_("Track"), "track")
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
        self.search_button.setAttribute(QtCore.Qt.WA_MacShowFocusRect)

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
                action = QtWidgets.QAction(_(label), menu)
                action.setCheckable(True)
                action.setChecked(config.setting[opt])
                action.triggered.connect(partial(toggle_opt, opt))
                menu.addAction(action)
            menu.exec_(self.search_button.mapToGlobal(position))

        self.search_button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
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
        if self.search_edit.text():
            self.search_action.setEnabled(True)
        else:
            self.search_action.setEnabled(False)

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
                           config.setting["use_adv_search_syntax"],
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
            config.persist["current_directory"] = os.path.dirname(files[0])
            self.tagger.add_files(files)

    def add_directory(self):
        """Add directory to the tagger."""
        current_directory = find_starting_directory()

        dir_list = []
        config = get_config()
        if not config.setting["toolbar_multiselect"]:
            directory = QtWidgets.QFileDialog.getExistingDirectory(self, "", current_directory)
            if directory:
                dir_list.append(directory)
        else:
            file_dialog = MultiDirsSelectDialog(self, "", current_directory)
            if file_dialog.exec_() == QtWidgets.QDialog.Accepted:
                dir_list = file_dialog.selectedFiles()

        dir_count = len(dir_list)
        if dir_count:
            parent = os.path.dirname(dir_list[0]) if dir_count > 1 else dir_list[0]
            config.persist["current_directory"] = parent
            if dir_count > 1:
                self.set_statusbar_message(
                    N_("Adding multiple directories from '%(directory)s' ..."),
                    {'directory': parent}
                )
            else:
                self.set_statusbar_message(
                    N_("Adding directory: '%(directory)s' ..."),
                    {'directory': dir_list[0]}
                )

            self.tagger.add_paths(dir_list)

    def close_active_window(self):
        self.tagger.activeWindow().close()

    def show_about(self):
        return AboutDialog.show_instance(self)

    def show_options(self, page=None):
        return OptionsDialog.show_instance(page, self)

    def show_help(self):
        webbrowser2.open('documentation')

    def show_log(self):
        self.log_dialog.show()
        self.log_dialog.raise_()
        self.log_dialog.activateWindow()

    def show_history(self):
        self.history_dialog.show()
        self.history_dialog.raise_()
        self.history_dialog.activateWindow()

    def open_bug_report(self):
        webbrowser2.open('troubleshooting')

    def open_support_forum(self):
        webbrowser2.open('forum')

    def open_donation_page(self):
        webbrowser2.open('donate')

    def save(self):
        """Tell the tagger to save the selected objects."""
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

    def _openUrl(self, url):
        return QtCore.QUrl.fromLocalFile(url)

    def play_file(self):
        for file in iter_files_from_objects(self.selected_objects):
            QtGui.QDesktopServices.openUrl(self._openUrl(file.filename))

    def _on_player_error(self, error, msg):
        self.set_statusbar_message(msg, echo=log.warning, translate=None)

    def open_folder(self):
        folders = iter_unique(
            os.path.dirname(f.filename) for f
            in iter_files_from_objects(self.selected_objects))
        for folder in folders:
            QtGui.QDesktopServices.openUrl(self._openUrl(folder))

    def _ensure_fingerprinting_configured(self, callback):
        config = get_config()

        def on_finished(result):
            callback(config.setting['fingerprinting_system'])
        if not config.setting['fingerprinting_system']:
            if self._show_analyze_settings_info():
                dialog = self.show_options("fingerprinting")
                dialog.finished.connect(on_finished)
        else:
            callback(config.setting['fingerprinting_system'])

    def _show_analyze_settings_info(self):
        ret = QtWidgets.QMessageBox.question(self,
            _("Configuration Required"),
            _("Audio fingerprinting is not yet configured. Would you like to configure it now?"),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes)
        return ret == QtWidgets.QMessageBox.Yes

    def get_first_obj_with_type(self, type):
        for obj in self.selected_objects:
            if isinstance(obj, type):
                return obj
        return None

    def show_more_tracks(self):
        if not self.selected_objects:
            return
        obj = self.selected_objects[0]
        if isinstance(obj, Track) and obj.files:
            obj = obj.files[0]
        if not isinstance(obj, File):
            log.debug('show_more_tracks expected a File, got %r' % obj)
            return
        dialog = TrackSearchDialog(self)
        dialog.load_similar_tracks(obj)
        dialog.exec_()

    def show_more_albums(self):
        obj = self.get_first_obj_with_type(Cluster)
        if not obj:
            log.debug('show_more_albums expected a Cluster, got %r' % obj)
            return
        dialog = AlbumSearchDialog(self)
        dialog.show_similar_albums(obj)
        dialog.exec_()

    def view_info(self, default_tab=0):
        if not self.selected_objects:
            return
        elif isinstance(self.selected_objects[0], Album):
            album = self.selected_objects[0]
            dialog = AlbumInfoDialog(album, self)
        elif isinstance(self.selected_objects[0], Cluster):
            cluster = self.selected_objects[0]
            dialog = ClusterInfoDialog(cluster, self)
        elif isinstance(self.selected_objects[0], Track):
            track = self.selected_objects[0]
            dialog = TrackInfoDialog(track, self)
        else:
            file = self.tagger.get_files_from_objects(self.selected_objects)[0]
            dialog = FileInfoDialog(file, self)
        dialog.ui.tabWidget.setCurrentIndex(default_tab)
        dialog.exec_()

    def cluster(self):
        self.tagger.cluster(self.selected_objects)
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
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes)
        if ret == QtWidgets.QMessageBox.Yes:
            config = get_config()
            config.setting["browser_integration"] = True
            self.tagger.update_browser_integration()
            if addrelease.is_enabled():
                return True
            else:
                # Something went wrong, let the user configure browser integration manually
                self.show_options("network")
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
        have_files = bool(self.tagger.get_files_from_objects(self.selected_objects))
        have_objects = bool(self.selected_objects)
        for obj in self.selected_objects:
            if obj is None:
                continue
            if obj.can_analyze():
                can_analyze = True
            if obj.can_save():
                can_save = True
            if obj.can_remove():
                can_remove = True
            if obj.can_refresh():
                can_refresh = True
            if obj.can_autotag():
                can_autotag = True
            if obj.can_submit():
                can_submit = True
            # Skip further loops if all values now True.
            if can_analyze and can_save and can_remove and can_refresh and can_autotag and can_submit:
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
        self.track_search_action.setEnabled(is_file)

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
            files = self.tagger.get_files_from_objects(objects)
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
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes)
            if ret == QtWidgets.QMessageBox.Yes:
                self.tagger.mb_login(self.on_mb_login_finished)
        else:
            dialog = PasswordDialog(authenticator, reply, parent=self)
            dialog.exec_()

    @classmethod
    def on_mb_login_finished(self, successful):
        log.debug('MusicBrainz authentication finished: %s', successful)

    def show_proxy_dialog(self, proxy, authenticator):
        dialog = ProxyDialog(authenticator, proxy, parent=self)
        dialog.exec_()

    def autotag(self):
        self.tagger.autotag(self.selected_objects)

    def cut(self):
        self.tagger.copy_files(self.selected_objects)
        self.paste_action.setEnabled(bool(self.selected_objects))

    def paste(self):
        selected_objects = self.selected_objects
        if not selected_objects:
            target = self.tagger.unclustered_files
        else:
            target = selected_objects[0]
        self.tagger.paste_files(target)
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
        log.debug('{check_status} start-up check for program updates.  Today: {today_date}, Last check: {last_check} (Check interval: {check_interval} days), Update level: {update_level} ({update_level_name})'.format(
            check_status='Initiating' if do_auto_update_check else 'Skipping',
            today_date=datetime.date.today(),
            last_check=str(datetime.date.fromordinal(last_update_check)) if last_update_check > 0 else 'never',
            check_interval=update_check_days,
            update_level=update_level,
            update_level_name=PROGRAM_UPDATE_LEVELS[update_level]['name'] if update_level in PROGRAM_UPDATE_LEVELS else 'unknown',
        ))
        if do_auto_update_check:
            self.check_for_update(False)

    def check_for_update(self, show_always):
        config = get_config()
        self.tagger.updatecheckmanager.check_update(
            show_always=show_always,
            update_level=config.setting['update_level'],
            callback=update_last_check_date
        )

    def check_and_repair_profiles(self):
        """Check the profiles and profile settings and repair the values if required.
        Checks that there is a settings dictionary for each profile, and that no profiles
        reference a non-existant file naming script.
        """
        script_id_key = "selected_file_naming_script_id"
        config = get_config()
        naming_scripts = config.setting["file_renaming_scripts"]
        naming_script_ids = set(naming_scripts.keys())
        naming_script_ids |= set(item["id"] for item in get_file_naming_script_presets())
        profile_settings = deepcopy(config.profiles[SettingConfigSection.SETTINGS_KEY])
        for profile in config.profiles[SettingConfigSection.PROFILES_KEY]:
            p_id = profile["id"]
            # Add empty settings if none found for a profile
            if p_id not in profile_settings:
                log.warning(
                    "No settings dict found for profile '%s' (\"%s\").  Adding empty dict.",
                    p_id,
                    profile["title"],
                )
                profile_settings[p_id] = {}
            # Remove any invalid naming script ids from profiles
            if script_id_key in profile_settings[p_id]:
                if profile_settings[p_id][script_id_key] not in naming_script_ids:
                    log.warning(
                        "Removing invalid naming script id '%s' from profile '%s' (\"%s\")",
                        profile_settings[p_id][script_id_key],
                        p_id,
                        profile["title"],
                    )
                    profile_settings[p_id][script_id_key] = None
        config.profiles[SettingConfigSection.SETTINGS_KEY] = profile_settings

    def make_script_selector_menu(self):
        """Update the sub-menu of available file naming scripts.
        """
        config = get_config()
        naming_scripts = config.setting["file_renaming_scripts"]
        selected_script_id = config.setting["selected_file_naming_script_id"]

        self.script_quick_selector_menu.clear()

        group = QtWidgets.QActionGroup(self.script_quick_selector_menu)
        group.setExclusive(True)

        def _add_menu_item(title, id):
            script_action = QtWidgets.QAction(title, self.script_quick_selector_menu)
            script_action.triggered.connect(partial(self.select_new_naming_script, id))
            script_action.setCheckable(True)
            script_action.setChecked(id == selected_script_id)
            self.script_quick_selector_menu.addAction(script_action)
            group.addAction(script_action)

        for (id, naming_script) in sorted(naming_scripts.items(), key=lambda item: item[1]['title']):
            _add_menu_item(user_script_title(naming_script['title']), id)

        # Add preset scripts not provided in the user-defined scripts list.
        for script_item in get_file_naming_script_presets():
            _add_menu_item(script_item['title'], script_item['id'])

    def select_new_naming_script(self, id):
        """Update the currently selected naming script ID in the settings.

        Args:
            id (str): ID of the selected file naming script
        """
        config = get_config()
        log.debug("Setting naming script to: %s", id)
        config.setting["selected_file_naming_script_id"] = id
        self.make_script_selector_menu()
        if self.script_editor_dialog:
            self.script_editor_dialog.set_selected_script_id(id, skip_check=False)

    def open_file_naming_script_editor(self):
        """Open the file naming script editor / manager in a new window.
        """
        if self.script_editor_dialog:
            self.script_editor_dialog.load()
        else:
            self.examples = ScriptEditorExamples(tagger=self.tagger)
            self.create_script_editor_dialog()
        self.script_editor_dialog.show()
        self.script_editor_dialog.raise_()
        self.script_editor_dialog.activateWindow()
        self.examples.update_sample_example_files()
        self.show_script_editor_action.setEnabled(False)
        self.options_action.setEnabled(False)

    def create_script_editor_dialog(self):
        """Create the file naming script editor manager window.
        """
        self.script_editor_dialog = ScriptEditorDialog(parent=self, examples=self.examples)
        self.script_editor_dialog.signal_save.connect(self.script_editor_save)
        self.script_editor_dialog.signal_selection_changed.connect(self.update_selector_from_script_editor)
        self.script_editor_dialog.signal_update_scripts_list.connect(self.update_scripts_list_from_editor)
        self.script_editor_dialog.signal_index_changed.connect(self.script_editor_index_changed)
        self.script_editor_dialog.finished.connect(self.script_editor_closed)

    def script_editor_save(self):
        """Process "signal_save" signal from the script editor.
        """
        config = get_config()
        config.setting["file_renaming_scripts"] = self.script_editor_dialog.naming_scripts
        script_item = self.script_editor_dialog.get_selected_item()
        config.setting["selected_file_naming_script_id"] = script_item["id"]
        self.make_script_selector_menu()

    def script_editor_closed(self):
        """Process "finished" signal from the script editor.
        """
        self.show_script_editor_action.setEnabled(True)
        self.options_action.setEnabled(True)

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

    def update_scripts_list_from_editor(self):
        """Process "signal_update_scripts_list" signal from the script editor.
        """
        self.script_editor_save()

    def open_profile_editor(self):
        self.profile_editor_dialog = ProfileEditorDialog.show_instance(self)
        self.profile_editor_dialog.finished.connect(self.profile_editor_dialog_finished)

    def profile_editor_dialog_finished(self):
        """Update menu bar entries to reflect any changes in profile selection.
        """
        config = get_config()
        self.profile_editor_dialog.finished.disconnect()
        self.profile_editor_dialog = None
        self.enable_renaming_action.setChecked(config.setting["rename_files"])
        self.enable_moving_action.setChecked(config.setting["move_files"])
        self.enable_tag_saving_action.setChecked(not config.setting["dont_write_tags"])
        self.make_script_selector_menu()
        if self.script_editor_dialog:
            self.script_editor_dialog.reload_after_profile()


def update_last_check_date(is_success):
    if is_success:
        config = get_config()
        config.persist['last_update_check'] = datetime.date.today().toordinal()
    else:
        log.debug('The update check was unsuccessful. The last update date will not be changed.')
