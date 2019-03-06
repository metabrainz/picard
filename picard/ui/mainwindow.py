# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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

from collections import OrderedDict
import datetime
from functools import partial
import os.path

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import (
    config,
    log,
)
from picard.album import Album
from picard.cluster import Cluster
from picard.const import PROGRAM_UPDATE_LEVELS
from picard.const.sys import (
    IS_MACOS,
)
from picard.file import File
from picard.formats import supported_formats
from picard.plugin import ExtensionPoint
from picard.track import Track
from picard.util import (
    icontheme,
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
from picard.ui.searchdialog.album import AlbumSearchDialog
from picard.ui.searchdialog.track import TrackSearchDialog
from picard.ui.tagsfromfilenames import TagsFromFileNamesDialog
from picard.ui.util import (
    MultiDirsSelectDialog,
    find_starting_directory,
)

ui_init = ExtensionPoint()


def register_ui_init(function):
    ui_init.register(function.__module__, function)


class MainWindow(QtWidgets.QMainWindow, PreserveGeometry):

    defaultsize = QtCore.QSize(780, 560)
    autorestore = False
    selection_updated = QtCore.pyqtSignal(object)

    options = [
        config.Option("persist", "window_state", QtCore.QByteArray()),
        config.Option("persist", "bottom_splitter_state", QtCore.QByteArray()),
        config.BoolOption("persist", "window_maximized", False),
        config.BoolOption("persist", "view_cover_art", True),
        config.BoolOption("persist", "view_toolbar", True),
        config.BoolOption("persist", "view_file_browser", False),
        config.TextOption("persist", "current_directory", ""),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_objects = []
        self.ignore_selection_changes = False
        self.toolbar = None
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(_("MusicBrainz Picard"))
        icon = QtGui.QIcon()
        icon.addFile(":/images/16x16/org.musicbrainz.Picard.png", QtCore.QSize(16, 16))
        icon.addFile(":/images/24x24/org.musicbrainz.Picard.png", QtCore.QSize(24, 24))
        icon.addFile(":/images/32x32/org.musicbrainz.Picard.png", QtCore.QSize(32, 32))
        icon.addFile(":/images/48x48/org.musicbrainz.Picard.png", QtCore.QSize(48, 48))
        icon.addFile(":/images/128x128/org.musicbrainz.Picard.png", QtCore.QSize(128, 128))
        icon.addFile(":/images/256x256/org.musicbrainz.Picard.png", QtCore.QSize(256, 256))
        self.setWindowIcon(icon)

        self.show_close_window = IS_MACOS

        self.create_actions()
        self.create_statusbar()
        self.create_toolbar()
        self.create_menus()

        if IS_MACOS:
            self.setUnifiedTitleAndToolBarOnMac(True)
            self.toolbar.setMovable(False)
            self.search_toolbar.setMovable(False)

        mainLayout = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setHandleWidth(1)

        self.panel = MainPanel(self, mainLayout)
        self.file_browser = FileBrowser(self.panel)
        if not self.show_file_browser_action.isChecked():
            self.file_browser.hide()
        self.panel.insertWidget(0, self.file_browser)
        self.panel.restore_state()

        self.metadata_box = MetadataBox(self)
        self.cover_art_box = CoverArtBox(self)
        if not self.show_cover_art_action.isChecked():
            self.cover_art_box.hide()

        self.logDialog = LogView(self)
        self.historyDialog = HistoryView(self)

        bottomLayout = QtWidgets.QHBoxLayout()
        bottomLayout.setContentsMargins(0, 0, 0, 0)
        bottomLayout.setSpacing(0)
        bottomLayout.addWidget(self.metadata_box, 1)
        bottomLayout.addWidget(self.cover_art_box, 0)
        bottom = QtWidgets.QWidget()
        bottom.setLayout(bottomLayout)

        mainLayout.addWidget(self.panel)
        mainLayout.addWidget(bottom)
        self.setCentralWidget(mainLayout)

        # accessibility
        self.set_tab_order()

        for function in ui_init:
            function(self)

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
        else:
            super().keyPressEvent(event)

    def show(self):
        self.restoreWindowState()
        super().show()
        if self.tagger.autoupdate_enabled:
            self.auto_update_check()
        self.metadata_box.restore_state()

    def closeEvent(self, event):
        if config.setting["quit_confirmation"] and not self.show_quit_confirmation():
            event.ignore()
            return
        self.saveWindowState()
        event.accept()

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
        config.persist["window_state"] = self.saveState()
        isMaximized = int(self.windowState()) & QtCore.Qt.WindowMaximized != 0
        self.save_geometry()
        config.persist["window_maximized"] = isMaximized
        config.persist["view_cover_art"] = self.show_cover_art_action.isChecked()
        config.persist["view_toolbar"] = self.show_toolbar_action.isChecked()
        config.persist["view_file_browser"] = self.show_file_browser_action.isChecked()
        config.persist["bottom_splitter_state"] = self.centralWidget().saveState()
        self.file_browser.save_state()
        self.panel.save_state()
        self.metadata_box.save_state()

    @restore_method
    def restoreWindowState(self):
        self.restoreState(config.persist["window_state"])
        self.restore_geometry()
        if config.persist["window_maximized"]:
            self.setWindowState(QtCore.Qt.WindowMaximized)
        bottom_splitter_state = config.persist["bottom_splitter_state"]
        if bottom_splitter_state.isEmpty():
            self.centralWidget().setSizes([366, 194])
        else:
            self.centralWidget().restoreState(bottom_splitter_state)
        self.file_browser.restore_state()

    def create_statusbar(self):
        """Creates a new status bar."""
        self.statusBar().showMessage(_("Ready"))
        self.infostatus = InfoStatus(self)
        self.listening_label = QtWidgets.QLabel()
        self.listening_label.setVisible(False)
        self.listening_label.setToolTip("<qt/>" + _(
            "Picard listens on this port to integrate with your browser. When "
            "you \"Search\" or \"Open in Browser\" from Picard, clicking the "
            "\"Tagger\" button on the web page loads the release into Picard."
        ))
        self.statusBar().addPermanentWidget(self.infostatus)
        self.statusBar().addPermanentWidget(self.listening_label)
        self.tagger.tagger_stats_changed.connect(self.update_statusbar_stats)
        self.tagger.listen_port_changed.connect(self.update_statusbar_listen_port)
        self.update_statusbar_stats()

    @throttle(100)
    def update_statusbar_stats(self):
        """Updates the status bar information."""
        self.infostatus.setFiles(len(self.tagger.files))
        self.infostatus.setAlbums(len(self.tagger.albums))
        self.infostatus.setPendingFiles(File.num_pending_files)
        ws = self.tagger.webservice
        self.infostatus.setPendingRequests(ws.num_pending_web_requests)

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
        # _ is defined using builtins.__dict__, so setting it as default named argument
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
            if not config.setting["acoustid_apikey"]:
                QtWidgets.QMessageBox.warning(self,
                    _("Submission Error"),
                    _("You need to configure your AcoustID API key before you can submit fingerprints."))
            else:
                self.tagger.acoustidmanager.submit()

    def create_actions(self):
        self.options_action = QtWidgets.QAction(icontheme.lookup('preferences-desktop'), _("&Options..."), self)
        self.options_action.setMenuRole(QtWidgets.QAction.PreferencesRole)
        self.options_action.triggered.connect(self.show_options)

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

        self.add_directory_action = QtWidgets.QAction(icontheme.lookup('folder'), _("A&dd Folder..."), self)
        self.add_directory_action.setStatusTip(_("Add a folder to the tagger"))
        # TR: Keyboard shortcut for "Add Directory..."
        self.add_directory_action.setShortcut(QtGui.QKeySequence(_("Ctrl+D")))
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

        self.album_search_action = QtWidgets.QAction(icontheme.lookup('system-search'), _("Search for similar albums..."), self)
        self.album_search_action.setStatusTip(_("View similar releases and optionally choose a different release"))
        self.album_search_action.triggered.connect(self.show_more_albums)

        self.track_search_action = QtWidgets.QAction(icontheme.lookup('system-search'), _("Search for similar tracks..."), self)
        self.track_search_action.setStatusTip(_("View similar tracks and optionally choose a different release"))
        self.track_search_action.triggered.connect(self.show_more_tracks)

        self.show_file_browser_action = QtWidgets.QAction(_("File &Browser"), self)
        self.show_file_browser_action.setCheckable(True)
        if config.persist["view_file_browser"]:
            self.show_file_browser_action.setChecked(True)
        self.show_file_browser_action.setShortcut(QtGui.QKeySequence(_("Ctrl+B")))
        self.show_file_browser_action.triggered.connect(self.show_file_browser)

        self.show_cover_art_action = QtWidgets.QAction(_("&Cover Art"), self)
        self.show_cover_art_action.setCheckable(True)
        if config.persist["view_cover_art"]:
            self.show_cover_art_action.setChecked(True)
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
            drives = get_cdrom_drives()
            if not drives:
                log.warning("CDROM: No CD-ROM drives found - Lookup CD functionality disabled")
            else:
                shortcut_drive = config.setting["cd_lookup_device"].split(",")[0] if len(drives) > 1 else ""
                self.cd_lookup_action.setEnabled(True)
                for drive in drives:
                    action = self.cd_lookup_menu.addAction(drive)
                    if drive == shortcut_drive:
                        # Clear existing shortcode on main action and assign it to sub-action
                        self.cd_lookup_action.setShortcut(QtGui.QKeySequence())
                        action.setShortcut(QtGui.QKeySequence(_("Ctrl+K")))

        self.analyze_action = QtWidgets.QAction(icontheme.lookup('picard-analyze'), _("&Scan"), self)
        self.analyze_action.setStatusTip(_("Use AcoustID audio fingerprint to identify the files by the actual music, even if they have no metadata"))
        self.analyze_action.setEnabled(False)
        self.analyze_action.setToolTip(_('Identify the file using its AcoustID audio fingerprint'))
        # TR: Keyboard shortcut for "Analyze"
        self.analyze_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Y")))
        self.analyze_action.triggered.connect(self.analyze)

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

        self.tags_from_filenames_action = QtWidgets.QAction(_("Tags From &File Names..."), self)
        self.tags_from_filenames_action.triggered.connect(self.open_tags_from_filenames)
        self.tags_from_filenames_action.setEnabled(False)

        self.open_collection_in_browser_action = QtWidgets.QAction(_("&Open My Collections in Browser"), self)
        self.open_collection_in_browser_action.triggered.connect(self.open_collection_in_browser)
        self.open_collection_in_browser_action.setEnabled(config.setting["username"] != '')

        self.view_log_action = QtWidgets.QAction(_("View &Error/Debug Log"), self)
        self.view_log_action.triggered.connect(self.show_log)
        # TR: Keyboard shortcut for "View Error/Debug Log"
        self.view_log_action.setShortcut(QtGui.QKeySequence(_("Ctrl+E")))

        self.view_history_action = QtWidgets.QAction(_("View Activity &History"), self)
        self.view_history_action.triggered.connect(self.show_history)
        # TR: Keyboard shortcut for "View Activity History"
        self.view_history_action.setShortcut(QtGui.QKeySequence(_("Ctrl+H")))

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

    def toggle_rename_files(self, checked):
        config.setting["rename_files"] = checked

    def toggle_move_files(self, checked):
        config.setting["move_files"] = checked

    def toggle_tag_saving(self, checked):
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
        menu.addAction(self.show_cover_art_action)
        menu.addSeparator()
        menu.addAction(self.show_toolbar_action)
        menu.addAction(self.search_toolbar_toggle_action)
        menu = self.menuBar().addMenu(_("&Options"))
        menu.addAction(self.enable_renaming_action)
        menu.addAction(self.enable_moving_action)
        menu.addAction(self.enable_tag_saving_action)
        menu.addSeparator()
        menu.addAction(self.options_action)
        menu = self.menuBar().addMenu(_("&Tools"))
        menu.addAction(self.refresh_action)
        if len(self.cd_lookup_menu.actions()) > 1:
            menu.addMenu(self.cd_lookup_menu)
        else:
            menu.addAction(self.cd_lookup_action)
        menu.addAction(self.autotag_action)
        menu.addAction(self.analyze_action)
        menu.addAction(self.cluster_action)
        menu.addAction(self.browser_lookup_action)
        menu.addSeparator()
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
        if config.setting["toolbar_show_labels"]:
            self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        else:
            self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)

    def create_toolbar(self):
        self.create_search_toolbar()
        self.create_action_toolbar()

    def create_action_toolbar(self):
        if self.toolbar:
            self.toolbar.clear()
            self.removeToolBar(self.toolbar)
        self.toolbar = toolbar = QtWidgets.QToolBar(_("Actions"))
        self.insertToolBar(self.search_toolbar, self.toolbar)
        self.update_toolbar_style()
        toolbar.setObjectName("main_toolbar")

        def add_toolbar_action(action):
            toolbar.addAction(action)
            widget = toolbar.widgetForAction(action)
            widget.setFocusPolicy(QtCore.Qt.TabFocus)
            widget.setAttribute(QtCore.Qt.WA_MacShowFocusRect)

        for action in config.setting['toolbar_layout']:
            if action == 'cd_lookup_action':
                add_toolbar_action(self.cd_lookup_action)
                if len(self.cd_lookup_menu.actions()) > 1:
                    button = toolbar.widgetForAction(self.cd_lookup_action)
                    button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
                    button.setMenu(self.cd_lookup_menu)
            elif action == 'separator':
                toolbar.addSeparator()
            else:
                try:
                    add_toolbar_action(getattr(self, action))
                except AttributeError:
                    log.warning('Warning: Unknown action name "%r" found in config. Ignored.', action)
        self.show_toolbar()

    def create_search_toolbar(self):
        self.search_toolbar = toolbar = self.addToolBar(_("Search"))
        self.search_toolbar_toggle_action = self.search_toolbar.toggleViewAction()
        toolbar.setObjectName("search_toolbar")
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
        tab_order(self.file_browser, self.panel.views[0])
        tab_order(self.panel.views[0], self.panel.views[1])
        tab_order(self.panel.views[1], self.metadata_box)

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
        self.tagger.search(text, entity,
                           config.setting["use_adv_search_syntax"],
                           mbid_matched_callback=self.search_mbid_found)

    def add_files(self):
        """Add files to the tagger."""
        current_directory = find_starting_directory()
        formats = []
        extensions = []
        for exts, name in supported_formats():
            exts = ["*" + e for e in exts]
            formats.append("%s (%s)" % (name, " ".join(exts)))
            extensions.extend(exts)
        formats.sort()
        extensions.sort()
        formats.insert(0, _("All Supported Formats") + " (%s)" % " ".join(extensions))
        files, _filter = QtWidgets.QFileDialog.getOpenFileNames(self, "", current_directory, ";;".join(formats))
        if files:
            config.persist["current_directory"] = os.path.dirname(files[0])
            self.tagger.add_files(files)

    def add_directory(self):
        """Add directory to the tagger."""
        current_directory = find_starting_directory()

        dir_list = []
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

            for directory in dir_list:
                self.tagger.add_directory(directory)

    def close_active_window(self):
        self.tagger.activeWindow().close()

    def show_about(self):
        self.show_options("about")

    def show_options(self, page=None):
        dialog = OptionsDialog(page, self)
        dialog.exec_()

    def show_help(self):
        webbrowser2.goto('documentation')

    def show_log(self):
        self.logDialog.show()
        self.logDialog.raise_()
        self.logDialog.activateWindow()

    def show_history(self):
        self.historyDialog.show()
        self.historyDialog.raise_()
        self.historyDialog.activateWindow()

    def open_bug_report(self):
        webbrowser2.goto('troubleshooting')

    def open_support_forum(self):
        webbrowser2.goto('forum')

    def open_donation_page(self):
        webbrowser2.goto('donate')

    def save(self):
        """Tell the tagger to save the selected objects."""
        self.tagger.save(self.selected_objects)

    def remove(self):
        """Tell the tagger to remove the selected objects."""
        self.panel.remove(self.selected_objects)

    def analyze(self):
        if not config.setting['fingerprinting_system']:
            if self.show_analyze_settings_info():
                self.show_options("fingerprinting")
            if not config.setting['fingerprinting_system']:
                return
        return self.tagger.analyze(self.selected_objects)

    def _openUrl(self, url):
        return QtCore.QUrl.fromLocalFile(url)

    def play_file(self):
        files = self.tagger.get_files_from_objects(self.selected_objects)
        for file in files:
            QtGui.QDesktopServices.openUrl(self._openUrl(file.filename))

    def open_folder(self):
        files = self.tagger.get_files_from_objects(self.selected_objects)
        folders = set([os.path.dirname(f.filename) for f in files])
        for folder in folders:
            QtGui.QDesktopServices.openUrl(self._openUrl(folder))

    def show_analyze_settings_info(self):
        ret = QtWidgets.QMessageBox.question(self,
            _("Configuration Required"),
            _("Audio fingerprinting is not yet configured. Would you like to configure it now?"),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes)
        return ret == QtWidgets.QMessageBox.Yes

    def show_more_tracks(self):
        obj = self.selected_objects[0]
        if isinstance(obj, Track):
            obj = obj.linked_files[0]
        dialog = TrackSearchDialog(self)
        dialog.load_similar_tracks(obj)
        dialog.exec_()

    def show_more_albums(self):
        obj = self.selected_objects[0]
        dialog = AlbumSearchDialog(self)
        dialog.show_similar_albums(obj)
        dialog.exec_()

    def view_info(self, default_tab=0):
        if isinstance(self.selected_objects[0], Album):
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
        self.update_actions()

    def refresh(self):
        self.tagger.refresh(self.selected_objects)

    def browser_lookup(self):
        self.tagger.browser_lookup(self.selected_objects[0])

    @throttle(100)
    def update_actions(self):
        can_remove = False
        can_save = False
        can_analyze = False
        can_refresh = False
        can_autotag = False
        single = self.selected_objects[0] if len(self.selected_objects) == 1 else None
        can_view_info = bool(single and single.can_view_info())
        can_browser_lookup = bool(single and single.can_browser_lookup())
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
            # Skip further loops if all values now True.
            if can_analyze and can_save and can_remove and can_refresh and can_autotag:
                break
        self.remove_action.setEnabled(can_remove)
        self.save_action.setEnabled(can_save)
        self.view_info_action.setEnabled(can_view_info)
        self.analyze_action.setEnabled(can_analyze)
        self.refresh_action.setEnabled(can_refresh)
        self.autotag_action.setEnabled(can_autotag)
        self.browser_lookup_action.setEnabled(can_browser_lookup)
        self.play_file_action.setEnabled(have_files)
        self.open_folder_action.setEnabled(have_files)
        self.cut_action.setEnabled(have_objects)
        files = self.get_selected_or_unmatched_files()
        self.tags_from_filenames_action.setEnabled(bool(files))
        self.track_search_action.setEnabled(have_objects)

    def update_selection(self, objects=None):
        if self.ignore_selection_changes:
            return

        if objects is not None:
            self.selected_objects = objects
        else:
            objects = self.selected_objects

        self.update_actions()

        metadata = None
        orig_metadata = None
        obj = None

        # Clear any existing status bar messages
        self.set_statusbar_message("")

        if len(objects) == 1:
            obj = list(objects)[0]
            if isinstance(obj, File):
                metadata = obj.metadata
                orig_metadata = obj.orig_metadata
                if obj.state == obj.ERROR:
                    msg = N_("%(filename)s (error: %(error)s)")
                    mparms = {
                        'filename': obj.filename,
                        'error': obj.error
                    }
                else:
                    msg = N_("%(filename)s")
                    mparms = {
                        'filename': obj.filename,
                    }
                self.set_statusbar_message(msg, mparms, echo=None, history=None)
            elif isinstance(obj, Track):
                metadata = obj.metadata
                if obj.num_linked_files == 1:
                    file = obj.linked_files[0]
                    orig_metadata = file.orig_metadata
                    if file.state == File.ERROR:
                        msg = N_("%(filename)s (%(similarity)d%%) (error: %(error)s)")
                        mparms = {
                            'filename': file.filename,
                            'similarity': file.similarity * 100,
                            'error': file.error
                        }
                    else:
                        msg = N_("%(filename)s (%(similarity)d%%)")
                        mparms = {
                            'filename': file.filename,
                            'similarity': file.similarity * 100,
                        }
                    self.set_statusbar_message(msg, mparms, echo=None,
                                               history=None)
            elif isinstance(obj, Album):
                metadata = obj.metadata
                orig_metadata = obj.orig_metadata
            elif obj.can_show_coverart:
                metadata = obj.metadata

        self.metadata_box.selection_dirty = True
        self.metadata_box.update()
        self.cover_art_box.set_metadata(metadata, orig_metadata, obj)
        self.selection_updated.emit(objects)

    def show_cover_art(self):
        """Show/hide the cover art box."""
        if self.show_cover_art_action.isChecked():
            self.cover_art_box.show()
        else:
            self.cover_art_box.hide()

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
        self.tagger.updatecheckmanager.check_update(
            show_always=show_always,
            update_level=config.setting['update_level'],
            callback=update_last_check_date
        )


def update_last_check_date(is_success):
    if is_success:
        config.persist['last_update_check'] = datetime.date.today().toordinal()
    else:
        log.debug('The update check was unsuccessful. The last update date will not be changed.')
