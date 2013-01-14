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

from PyQt4 import QtCore, QtGui

import sys
import os.path

from picard.file import File
from picard.track import Track
from picard.album import Album, NatAlbum
from picard.config import Option, BoolOption, TextOption
from picard.formats import supported_formats
from picard.ui.coverartbox import CoverArtBox
from picard.ui.itemviews import MainPanel
from picard.ui.metadatabox import MetadataBox
from picard.ui.filebrowser import FileBrowser
from picard.ui.tagsfromfilenames import TagsFromFileNamesDialog
from picard.ui.options.dialog import OptionsDialog
from picard.ui.infodialog import InfoDialog
from picard.ui.albuminfodialog import AlbumInfoDialog
from picard.ui.passworddialog import PasswordDialog
from picard.util import icontheme, webbrowser2, find_existing_path
from picard.util.cdrom import get_cdrom_drives
from picard.plugin import ExtensionPoint

ui_init = ExtensionPoint()
def register_ui_init (function):
    ui_init.register(function.__module__, function)

class MainWindow(QtGui.QMainWindow):

    options = [
        Option("persist", "window_state", QtCore.QByteArray(),
               QtCore.QVariant.toByteArray),
        Option("persist", "window_position", QtCore.QPoint(),
               QtCore.QVariant.toPoint),
        Option("persist", "window_size", QtCore.QSize(780, 560),
               QtCore.QVariant.toSize),
        Option("persist", "bottom_splitter_state", QtCore.QByteArray(),
               QtCore.QVariant.toByteArray),
        BoolOption("persist", "window_maximized", False),
        BoolOption("persist", "view_cover_art", False),
        BoolOption("persist", "view_file_browser", False),
        TextOption("persist", "current_directory", ""),
    ]

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.selected_objects = []
        self.ignore_selection_changes = False
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(_("MusicBrainz Picard"))
        icon = QtGui.QIcon()
        icon.addFile(":/images/16x16/picard.png", QtCore.QSize(16, 16))
        icon.addFile(":/images/24x24/picard.png", QtCore.QSize(24, 24))
        icon.addFile(":/images/32x32/picard.png", QtCore.QSize(32, 32))
        icon.addFile(":/images/48x48/picard.png", QtCore.QSize(48, 48))
        icon.addFile(":/images/128x128/picard.png", QtCore.QSize(128, 128))
        icon.addFile(":/images/256x256/picard.png", QtCore.QSize(256, 256))
        self.setWindowIcon(icon)

        self.create_actions()
        self.create_statusbar()
        self.create_toolbar()
        self.create_menus()

        mainLayout = QtGui.QSplitter(QtCore.Qt.Vertical)
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

        bottomLayout = QtGui.QHBoxLayout()
        bottomLayout.setContentsMargins(0, 0, 0, 0)
        bottomLayout.setSpacing(0)
        bottomLayout.addWidget(self.metadata_box, 1)
        bottomLayout.addWidget(self.cover_art_box, 0)
        bottom = QtGui.QWidget()
        bottom.setLayout(bottomLayout)

        mainLayout.addWidget(self.panel)
        mainLayout.addWidget(bottom)
        self.setCentralWidget(mainLayout)

        # FIXME: use QApplication's clipboard
        self._clipboard = []

        for function in ui_init:
            function(self)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Delete):
            if self.metadata_box.hasFocus():
                self.metadata_box.remove_selected_tags()
            else:
                self.remove()
        else:
            QtGui.QMainWindow.keyPressEvent(self, event)

    def show(self):
        self.restoreWindowState()
        QtGui.QMainWindow.show(self)
        self.metadata_box.restore_state()

    def closeEvent(self, event):
        if self.config.setting["quit_confirmation"] and not self.show_quit_confirmation():
            event.ignore()
            return
        self.saveWindowState()
        event.accept()

    def show_quit_confirmation(self):
        unsaved_files = sum(a.get_num_unsaved_files() for a in self.tagger.albums.itervalues())
        QMessageBox = QtGui.QMessageBox

        if unsaved_files > 0:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowModality(QtCore.Qt.WindowModal)
            msg.setWindowTitle(_(u"Unsaved Changes"))
            msg.setText(_(u"Are you sure you want to quit Picard?"))
            txt = ungettext(
                "There is %d unsaved file. Closing Picard will lose all unsaved changes.",
                "There are %d unsaved files. Closing Picard will lose all unsaved changes.",
                unsaved_files) % unsaved_files
            msg.setInformativeText(txt)
            cancel = msg.addButton(QMessageBox.Cancel)
            msg.setDefaultButton(cancel)
            msg.addButton(_(u"&Quit Picard"), QMessageBox.YesRole)
            ret = msg.exec_()

            if ret == QMessageBox.Cancel:
                return False

        return True

    def saveWindowState(self):
        self.config.persist["window_state"] = self.saveState()
        isMaximized = int(self.windowState()) & QtCore.Qt.WindowMaximized != 0
        if isMaximized:
            # FIXME: this doesn't include the window frame
            geom = self.normalGeometry()
            self.config.persist["window_position"] = geom.topLeft()
            self.config.persist["window_size"] = geom.size()
        else:
            pos = self.pos()
            if not pos.isNull():
                self.config.persist["window_position"] = pos
            self.config.persist["window_size"] = self.size()
        self.config.persist["window_maximized"] = isMaximized
        self.config.persist["view_cover_art"] = self.show_cover_art_action.isChecked()
        self.config.persist["view_file_browser"] = self.show_file_browser_action.isChecked()
        self.config.persist["bottom_splitter_state"] = self.centralWidget().saveState()
        self.file_browser.save_state()
        self.panel.save_state()
        self.metadata_box.save_state()

    def restoreWindowState(self):
        self.restoreState(self.config.persist["window_state"])
        pos = self.config.persist["window_position"]
        size = self.config.persist["window_size"]
        self._desktopgeo = self.tagger.desktop().screenGeometry()
        if pos.x() > 0 and pos.y() > 0 and pos.x()+size.width() < self._desktopgeo.width() and pos.y()+size.height() < self._desktopgeo.height():
            self.move(pos)
        if size.width() <= 0 or size.height() <= 0:
            size = QtCore.QSize(780, 560)
        self.resize(size)
        if self.config.persist["window_maximized"]:
            self.setWindowState(QtCore.Qt.WindowMaximized)
        bottom_splitter_state = self.config.persist["bottom_splitter_state"]
        if bottom_splitter_state.isEmpty():
            self.centralWidget().setSizes([366, 194])
        else:
            self.centralWidget().restoreState(bottom_splitter_state)
        self.file_browser.restore_state()

    def create_statusbar(self):
        """Creates a new status bar."""
        self.statusBar().showMessage(_("Ready"))
        self.file_counts_label = QtGui.QLabel()
        self.listening_label = QtGui.QLabel()
        self.listening_label.setVisible(False)
        self.listening_label.setToolTip(_("Picard listens on a port to integrate with your browser and downloads release"
                                          " information when you click the \"Tagger\" buttons on the MusicBrainz website"))
        self.statusBar().addPermanentWidget(self.file_counts_label)
        self.statusBar().addPermanentWidget(self.listening_label)
        self.tagger.file_state_changed.connect(self.update_statusbar_files)
        self.tagger.listen_port_changed.connect(self.update_statusbar_listen_port)
        self.update_statusbar_files(0)

    def update_statusbar_files(self, num_pending_files):
        """Updates the status bar information."""
        self.file_counts_label.setText(_(" Files: %(files)d, Pending Files: %(pending)d ")
            % {"files": self.tagger.num_files(), "pending": num_pending_files})

    def update_statusbar_listen_port(self, listen_port):
        self.listening_label.setVisible(True)
        self.listening_label.setText(_(" Listening on port %(port)d ") % {"port": listen_port})

    def set_statusbar_message(self, message, *args, **kwargs):
        """Set the status bar message."""
        try:
            if message:
                self.log.debug(repr(message.replace('%%s', '%%r')), *args)
        except:
            pass
        self.tagger.thread_pool.call_from_thread(
            self._set_statusbar_message, message, *args, **kwargs)

    def _set_statusbar_message(self, message, *args, **kwargs):
        if message:
            if args:
                message = _(message) % args
            else:
                message = _(message)
        self.statusBar().showMessage(message, kwargs.get('timeout', 0))

    def _on_submit(self):
        if self.tagger.use_acoustid:
            if not self.config.setting["acoustid_apikey"]:
                QtGui.QMessageBox.warning(self,
                    _(u"Submission Error"),
                    _(u"You need to configure your AcoustID API key before you can submit fingerprints."))
            else:
                self.tagger.acoustidmanager.submit()

    def create_actions(self):
        self.options_action = QtGui.QAction(icontheme.lookup('preferences-desktop'), _("&Options..."), self)
        self.options_action.setMenuRole(QtGui.QAction.PreferencesRole)
        self.options_action.triggered.connect(self.show_options)

        self.cut_action = QtGui.QAction(icontheme.lookup('edit-cut', icontheme.ICON_SIZE_MENU), _(u"&Cut"), self)
        self.cut_action.setShortcut(QtGui.QKeySequence.Cut)
        self.cut_action.setEnabled(False)
        self.cut_action.triggered.connect(self.cut)

        self.paste_action = QtGui.QAction(icontheme.lookup('edit-paste', icontheme.ICON_SIZE_MENU), _(u"&Paste"), self)
        self.paste_action.setShortcut(QtGui.QKeySequence.Paste)
        self.paste_action.setEnabled(False)
        self.paste_action.triggered.connect(self.paste)

        self.help_action = QtGui.QAction(_("&Help..."), self)

        self.help_action.setShortcut(QtGui.QKeySequence.HelpContents)
        self.help_action.triggered.connect(self.show_help)

        self.about_action = QtGui.QAction(_("&About..."), self)
        self.about_action.setMenuRole(QtGui.QAction.AboutRole)
        self.about_action.triggered.connect(self.show_about)

        self.donate_action = QtGui.QAction(_("&Donate..."), self)
        self.donate_action.triggered.connect(self.open_donation_page)

        self.report_bug_action = QtGui.QAction(_("&Report a Bug..."), self)
        self.report_bug_action.triggered.connect(self.open_bug_report)

        self.support_forum_action = QtGui.QAction(_("&Support Forum..."), self)
        self.support_forum_action.triggered.connect(self.open_support_forum)

        self.add_files_action = QtGui.QAction(icontheme.lookup('document-open'), _(u"&Add Files..."), self)
        self.add_files_action.setStatusTip(_(u"Add files to the tagger"))
        # TR: Keyboard shortcut for "Add Files..."
        self.add_files_action.setShortcut(QtGui.QKeySequence.Open)
        self.add_files_action.triggered.connect(self.add_files)

        self.add_directory_action = QtGui.QAction(icontheme.lookup('folder'), _(u"A&dd Folder..."), self)
        self.add_directory_action.setStatusTip(_(u"Add a folder to the tagger"))
        # TR: Keyboard shortcut for "Add Directory..."
        self.add_directory_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+D")))
        self.add_directory_action.triggered.connect(self.add_directory)

        self.save_action = QtGui.QAction(icontheme.lookup('document-save'), _(u"&Save"), self)
        self.save_action.setStatusTip(_(u"Save selected files"))
        # TR: Keyboard shortcut for "Save"
        self.save_action.setShortcut(QtGui.QKeySequence.Save)
        self.save_action.setEnabled(False)
        self.save_action.triggered.connect(self.save)

        self.submit_action = QtGui.QAction(icontheme.lookup('picard-submit'), _(u"S&ubmit"), self)
        self.submit_action.setStatusTip(_(u"Submit fingerprints"))
        self.submit_action.setEnabled(False)
        self.submit_action.triggered.connect(self._on_submit)

        self.exit_action = QtGui.QAction(_(u"E&xit"), self)
        self.exit_action.setMenuRole(QtGui.QAction.QuitRole)
        # TR: Keyboard shortcut for "Exit"
        self.exit_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+Q")))
        self.exit_action.triggered.connect(self.close)

        self.remove_action = QtGui.QAction(icontheme.lookup('list-remove'), _(u"&Remove"), self)
        self.remove_action.setStatusTip(_(u"Remove selected files/albums"))
        self.remove_action.setEnabled(False)
        self.remove_action.triggered.connect(self.remove)

        self.browser_lookup_action = QtGui.QAction(icontheme.lookup('lookup-musicbrainz'), _(u"Lookup in &Browser"), self)
        self.browser_lookup_action.setStatusTip(_(u"Lookup selected item on MusicBrainz website"))
        self.browser_lookup_action.setEnabled(False)
        self.browser_lookup_action.triggered.connect(self.browser_lookup)

        self.show_file_browser_action = QtGui.QAction(_(u"File &Browser"), self)
        self.show_file_browser_action.setCheckable(True)
        if self.config.persist["view_file_browser"]:
            self.show_file_browser_action.setChecked(True)
        self.show_file_browser_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+B")))
        self.show_file_browser_action.triggered.connect(self.show_file_browser)

        self.show_cover_art_action = QtGui.QAction(_(u"&Cover Art"), self)
        self.show_cover_art_action.setCheckable(True)
        if self.config.persist["view_cover_art"]:
            self.show_cover_art_action.setChecked(True)
        self.show_cover_art_action.triggered.connect(self.show_cover_art)

        self.search_action = QtGui.QAction(icontheme.lookup('system-search'), _(u"Search"), self)
        self.search_action.triggered.connect(self.search)

        self.cd_lookup_action = QtGui.QAction(icontheme.lookup('media-optical'), _(u"&CD Lookup..."), self)
        self.cd_lookup_action.setToolTip(_(u"Lookup CD"))
        self.cd_lookup_action.setStatusTip(_(u"Lookup CD"))
        # TR: Keyboard shortcut for "Lookup CD"
        self.cd_lookup_action.setShortcut(QtGui.QKeySequence(_("Ctrl+K")))
        self.cd_lookup_action.triggered.connect(self.tagger.lookup_cd)

        self.analyze_action = QtGui.QAction(icontheme.lookup('picard-analyze'), _(u"&Scan"), self)
        self.analyze_action.setEnabled(False)
        # TR: Keyboard shortcut for "Analyze"
        self.analyze_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+Y")))
        self.analyze_action.triggered.connect(self.analyze)

        self.cluster_action = QtGui.QAction(icontheme.lookup('picard-cluster'), _(u"Cl&uster"), self)
        self.cluster_action.setEnabled(False)
        # TR: Keyboard shortcut for "Cluster"
        self.cluster_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+U")))
        self.cluster_action.triggered.connect(self.cluster)

        self.autotag_action = QtGui.QAction(icontheme.lookup('picard-auto-tag'), _(u"&Lookup"), self)
        self.autotag_action.setToolTip(_(u"Lookup metadata"))
        self.autotag_action.setStatusTip(_(u"Lookup metadata"))
        self.autotag_action.setEnabled(False)
        # TR: Keyboard shortcut for "Lookup"
        self.autotag_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+L")))
        self.autotag_action.triggered.connect(self.autotag)

        self.view_info_action = QtGui.QAction(icontheme.lookup('picard-edit-tags'), _(u"&Info..."), self)
        self.view_info_action.setEnabled(False)
        # TR: Keyboard shortcut for "Info"
        self.view_info_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+I")))
        self.view_info_action.triggered.connect(self.view_info)

        self.refresh_action = QtGui.QAction(icontheme.lookup('view-refresh', icontheme.ICON_SIZE_MENU), _("&Refresh"), self)
        self.refresh_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+R")))
        self.refresh_action.triggered.connect(self.refresh)

        self.enable_renaming_action = QtGui.QAction(_(u"&Rename Files"), self)
        self.enable_renaming_action.setCheckable(True)
        self.enable_renaming_action.setChecked(self.config.setting["rename_files"])
        self.enable_renaming_action.triggered.connect(self.toggle_rename_files)

        self.enable_moving_action = QtGui.QAction(_(u"&Move Files"), self)
        self.enable_moving_action.setCheckable(True)
        self.enable_moving_action.setChecked(self.config.setting["move_files"])
        self.enable_moving_action.triggered.connect(self.toggle_move_files)

        self.enable_tag_saving_action = QtGui.QAction(_(u"Save &Tags"), self)
        self.enable_tag_saving_action.setCheckable(True)
        self.enable_tag_saving_action.setChecked(not self.config.setting["dont_write_tags"])
        self.enable_tag_saving_action.triggered.connect(self.toggle_tag_saving)

        self.tags_from_filenames_action = QtGui.QAction(_(u"Tags From &File Names..."), self)
        self.tags_from_filenames_action.triggered.connect(self.open_tags_from_filenames)

        self.view_log_action = QtGui.QAction(_(u"View &Log..."), self)
        self.view_log_action.triggered.connect(self.show_log)

        xmlws_manager = self.tagger.xmlws.manager
        xmlws_manager.authenticationRequired.connect(self.show_password_dialog)
        xmlws_manager.proxyAuthenticationRequired.connect(self.show_proxy_dialog)

        self.open_file_action = QtGui.QAction(_(u"&Open..."), self)
        self.open_file_action.setStatusTip(_(u"Open the file"))
        self.open_file_action.triggered.connect(self.open_file)

        self.open_folder_action = QtGui.QAction(_(u"Open &Folder..."), self)
        self.open_folder_action.setStatusTip(_(u"Open the containing folder"))
        self.open_folder_action.triggered.connect(self.open_folder)

    def toggle_rename_files(self, checked):
        self.config.setting["rename_files"] = checked

    def toggle_move_files(self, checked):
        self.config.setting["move_files"] = checked

    def toggle_tag_saving(self, checked):
        self.config.setting["dont_write_tags"] = not checked

    def open_tags_from_filenames(self):
        files = self.tagger.get_files_from_objects(self.selected_objects)
        if not files:
            files = self.tagger.unmatched_files.files
        if files:
            dialog = TagsFromFileNamesDialog(files, self)
            dialog.exec_()

    def create_menus(self):
        menu = self.menuBar().addMenu(_(u"&File"))
        menu.addAction(self.add_files_action)
        menu.addAction(self.add_directory_action)
        menu.addSeparator()
        menu.addAction(self.save_action)
        menu.addAction(self.submit_action)
        menu.addSeparator()
        menu.addAction(self.exit_action)
        menu = self.menuBar().addMenu(_(u"&Edit"))
        menu.addAction(self.cut_action)
        menu.addAction(self.paste_action)
        menu.addSeparator()
        menu.addAction(self.view_info_action)
        menu.addAction(self.remove_action)
        menu = self.menuBar().addMenu(_(u"&View"))
        menu.addAction(self.show_file_browser_action)
        menu.addAction(self.show_cover_art_action)
        menu.addSeparator()
        menu.addAction(self.toolbar.toggleViewAction())
        menu.addAction(self.search_toolbar.toggleViewAction())
        menu.addSeparator()
        menu.addAction(self.refresh_action)
        menu = self.menuBar().addMenu(_(u"&Options"))
        menu.addAction(self.enable_renaming_action)
        menu.addAction(self.enable_moving_action)
        menu.addAction(self.enable_tag_saving_action)
        menu.addSeparator()
        menu.addAction(self.options_action)
        menu = self.menuBar().addMenu(_(u"&Tools"))
        menu.addAction(self.cd_lookup_action)
        menu.addAction(self.autotag_action)
        menu.addAction(self.analyze_action)
        menu.addAction(self.cluster_action)
        menu.addAction(self.browser_lookup_action)
        menu.addSeparator()
        menu.addAction(self.tags_from_filenames_action)
        self.menuBar().addSeparator()
        menu = self.menuBar().addMenu(_(u"&Help"))
        menu.addAction(self.help_action)
        menu.addSeparator()
        menu.addAction(self.support_forum_action)
        menu.addAction(self.report_bug_action)
        menu.addAction(self.view_log_action)
        menu.addSeparator()
        menu.addAction(self.donate_action)
        menu.addAction(self.about_action)

    def update_toolbar_style(self):
        if self.config.setting["toolbar_show_labels"]:
            self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        else:
            self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.cd_lookup_action.setEnabled(len(get_cdrom_drives()) > 0)

    def create_toolbar(self):
        self.toolbar = toolbar = self.addToolBar(_(u"&Toolbar"))
        self.update_toolbar_style()
        toolbar.setObjectName("main_toolbar")
        toolbar.addAction(self.add_files_action)
        toolbar.addAction(self.add_directory_action)
        toolbar.addSeparator()
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.submit_action)
        toolbar.addSeparator()

        toolbar.addAction(self.cd_lookup_action)
        drives = get_cdrom_drives()
        if len(drives) > 1:
            self.cd_lookup_menu = QtGui.QMenu()
            for drive in drives:
                self.cd_lookup_menu.addAction(drive)
            self.cd_lookup_menu.triggered.connect(self.tagger.lookup_cd)
            button = toolbar.widgetForAction(self.cd_lookup_action)
            button.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
            button.setMenu(self.cd_lookup_menu)

        toolbar.addAction(self.cluster_action)
        toolbar.addAction(self.autotag_action)
        toolbar.addAction(self.analyze_action)
        toolbar.addAction(self.view_info_action)
        toolbar.addAction(self.remove_action)
        toolbar.addAction(self.browser_lookup_action)
        self.search_toolbar = toolbar = self.addToolBar(_(u"&Search Bar"))
        toolbar.setObjectName("search_toolbar")
        search_panel = QtGui.QWidget(toolbar)
        hbox = QtGui.QHBoxLayout(search_panel)
        self.search_combo = QtGui.QComboBox(search_panel)
        self.search_combo.addItem(_(u"Album"), QtCore.QVariant("album"))
        self.search_combo.addItem(_(u"Artist"), QtCore.QVariant("artist"))
        self.search_combo.addItem(_(u"Track"), QtCore.QVariant("track"))
        hbox.addWidget(self.search_combo, 0)
        self.search_edit = QtGui.QLineEdit(search_panel)
        self.search_edit.returnPressed.connect(self.search)
        hbox.addWidget(self.search_edit, 0)
        self.search_button = QtGui.QToolButton(search_panel)
        self.search_button.setAutoRaise(True)
        self.search_button.setDefaultAction(self.search_action)
        self.search_button.setIconSize(QtCore.QSize(22, 22))
        hbox.addWidget(self.search_button)
        toolbar.addWidget(search_panel)

    def enable_submit(self, enabled):
        """Enable/disable the 'Submit fingerprints' action."""
        self.submit_action.setEnabled(enabled)

    def enable_cluster(self, enabled):
        """Enable/disable the 'Cluster' action."""
        self.cluster_action.setEnabled(enabled)

    def search(self):
        """Search for album, artist or track on the MusicBrainz website."""
        text = unicode(self.search_edit.text())
        type = unicode(self.search_combo.itemData(
                       self.search_combo.currentIndex()).toString())
        self.tagger.search(text, type, self.config.setting["use_adv_search_syntax"])

    def add_files(self):
        """Add files to the tagger."""
        current_directory = self.config.persist["current_directory"] or QtCore.QDir.homePath()
        current_directory = find_existing_path(unicode(current_directory))
        formats = []
        extensions = []
        for exts, name in supported_formats():
            exts = ["*" + e for e in exts]
            formats.append("%s (%s)" % (name, " ".join(exts)))
            extensions.extend(exts)
        formats.sort()
        extensions.sort()
        formats.insert(0, _("All Supported Formats") + " (%s)" % " ".join(extensions))
        files = QtGui.QFileDialog.getOpenFileNames(self, "", current_directory, u";;".join(formats))
        if files:
            files = map(unicode, files)
            self.config.persist["current_directory"] = os.path.dirname(files[0])
            self.tagger.add_files(files)

    def add_directory(self):
        """Add directory to the tagger."""
        current_directory = self.config.persist["current_directory"] or QtCore.QDir.homePath()
        current_directory = find_existing_path(unicode(current_directory))

        dir_list = []
        if not self.config.setting["toolbar_multiselect"]:
            directory = QtGui.QFileDialog.getExistingDirectory(self, "", current_directory)
            if directory:
                dir_list.append(directory)
        else:
            # Use a custom file selection dialog to allow the selection of multiple directories
            file_dialog = QtGui.QFileDialog(self, "", current_directory)
            file_dialog.setFileMode(QtGui.QFileDialog.DirectoryOnly)
            if sys.platform == "darwin": # The native dialog doesn't allow selecting >1 directory
                file_dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog)
            tree_view = file_dialog.findChild(QtGui.QTreeView)
            tree_view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            list_view = file_dialog.findChild(QtGui.QListView, "listView")
            list_view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

            if file_dialog.exec_() == QtGui.QDialog.Accepted:
                dir_list = file_dialog.selectedFiles()

        if len(dir_list) == 1:
            self.config.persist["current_directory"] = dir_list[0]
        elif len(dir_list) > 1:
            (parent, dir) = os.path.split(str(dir_list[0]))
            self.config.persist["current_directory"] = parent

        for directory in dir_list:
            directory = unicode(directory)
            self.tagger.add_directory(directory)

    def show_about(self):
        self.show_options("about")

    def show_options(self, page=None):
        dialog = OptionsDialog(page, self)
        dialog.exec_()

    def show_help(self):
        webbrowser2.open("http://musicbrainz.org/doc/Picard_Documentation")

    def show_log(self):
        from picard.ui.logview import LogView
        w = LogView(self)
        w.show()

    def confirm_va_removal(self):
        return QtGui.QMessageBox.question(self,
                _("Various Artists file naming scheme removal"),
_("""The separate file naming scheme for various artists albums has been
removed in this version of Picard. You currently do not use the this option,
but have a separate file naming scheme defined. Do you want to remove it or
merge it with your file naming scheme for single artist albums?"""),
            _("Merge"), _("Remove"))

    def show_va_removal_notice(self):
        QtGui.QMessageBox.information(self,
            _("Various Artists file naming scheme removal"),
_("""The separate file naming scheme for various artists albums has been
removed in this version of Picard. Your file naming scheme has automatically
been merged with that of single artist albums."""),
            QtGui.QMessageBox.Ok)


    def open_bug_report(self):
        webbrowser2.open("http://musicbrainz.org/doc/Picard_Troubleshooting")

    def open_support_forum(self):
        webbrowser2.open("http://forums.musicbrainz.org/viewforum.php?id=2")

    def open_donation_page(self):
        webbrowser2.open('http://metabrainz.org/donate')

    def save(self):
        """Tell the tagger to save the selected objects."""
        self.tagger.save(self.selected_objects)

    def remove(self):
        """Tell the tagger to remove the selected objects."""
        self.panel.remove(self.selected_objects)

    def analyze(self):
        if not self.config.setting['fingerprinting_system']:
            if self.show_analyze_settings_info():
                self.show_options("fingerprinting")
            if not self.config.setting['fingerprinting_system']:
                return
        return self.tagger.analyze(self.selected_objects)

    def open_file(self):
        files = self.tagger.get_files_from_objects(self.selected_objects)
        for file in files:
            url = QtCore.QUrl.fromLocalFile(file.filename)
            QtGui.QDesktopServices.openUrl(url)

    def open_folder(self):
        files = self.tagger.get_files_from_objects(self.selected_objects)
        for file in files:
            url = QtCore.QUrl.fromLocalFile(os.path.dirname(file.filename))
            QtGui.QDesktopServices.openUrl(url)

    def show_analyze_settings_info(self):
        ret = QtGui.QMessageBox.question(self,
            _(u"Configuration Required"),
            _(u"Audio fingerprinting is not yet configured. Would you like to configure it now?"),
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.Yes)
        return ret == QtGui.QMessageBox.Yes

    def view_info(self):
        if isinstance(self.selected_objects[0], Album):
            album = self.selected_objects[0]
            dialog = AlbumInfoDialog(album, self)
        else:
            file = self.tagger.get_files_from_objects(self.selected_objects)[0]
            dialog = InfoDialog(file, self)
        dialog.exec_()

    def cluster(self):
        self.tagger.cluster(self.selected_objects)

    def refresh(self):
        self.tagger.refresh(self.selected_objects)

    def browser_lookup(self):
        self.tagger.browser_lookup(self.selected_objects[0])

    def update_actions(self):
        can_remove = False
        can_save = False
        can_analyze = False
        can_refresh = False
        can_autotag = False
        single = self.selected_objects[0] if len(self.selected_objects) == 1 else None
        can_view_info = bool(single and single.can_view_info())
        can_browser_lookup = bool(single and single.can_browser_lookup())
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
            if can_save and can_remove and can_refresh and can_autotag:
                break
        self.remove_action.setEnabled(can_remove)
        self.save_action.setEnabled(can_save)
        self.view_info_action.setEnabled(can_view_info)
        self.analyze_action.setEnabled(can_analyze)
        self.refresh_action.setEnabled(can_refresh)
        self.autotag_action.setEnabled(can_autotag)
        self.browser_lookup_action.setEnabled(can_browser_lookup)
        self.cut_action.setEnabled(bool(self.selected_objects))

    def update_selection(self, objects=None):
        if self.ignore_selection_changes:
            return

        if objects is not None:
            self.selected_objects = objects
        else:
            objects = self.selected_objects

        self.update_actions()

        metadata = None
        statusbar = u""
        obj = None

        if len(objects) == 1:
            obj = list(objects)[0]
            if isinstance(obj, File):
                metadata = obj.metadata
                statusbar = obj.filename
                if obj.state == obj.ERROR:
                    statusbar += _(" (Error: %s)") % obj.error
            elif isinstance(obj, Track):
                metadata = obj.metadata
                if obj.num_linked_files == 1:
                    file = obj.linked_files[0]
                    statusbar = "%s (%d%%)" % (file.filename, file.similarity * 100)
                    if file.state == File.ERROR:
                        statusbar += _(" (Error: %s)") % file.error
            elif obj.can_edit_tags():
                metadata = obj.metadata

        self.metadata_box.update_selection()
        self.metadata_box.update()
        self.cover_art_box.set_metadata(metadata, obj)
        self.set_statusbar_message(statusbar)

    def show_cover_art(self):
        """Show/hide the cover art box."""
        if self.show_cover_art_action.isChecked():
            self.cover_art_box.show()
            self.metadata_box.shrink_columns()
        else:
            self.cover_art_box.hide()

    def show_file_browser(self):
        """Show/hide the file browser."""
        if self.show_file_browser_action.isChecked():
            sizes = self.panel.sizes()
            if sizes[0] == 0:
                sizes[0] = sum(sizes) / 4
                self.panel.setSizes(sizes)
            self.file_browser.show()
        else:
            self.file_browser.hide()

    def show_password_dialog(self, reply, authenticator):
        dialog = PasswordDialog(authenticator, reply, parent=self)
        dialog.exec_()

    def show_proxy_dialog(self, proxy, authenticator):
        dialog = ProxyDialog(authenticator, proxy, parent=self)
        dialog.exec_()

    def autotag(self):
        self.tagger.autotag(self.selected_objects)

    def cut(self):
        self._clipboard = self.selected_objects
        self.paste_action.setEnabled(bool(self._clipboard))

    def paste(self):
        selected_objects = self.selected_objects
        if not selected_objects:
            target = self.tagger.unmatched_files
        else:
            target = selected_objects[0]
        self.tagger.move_files(self.tagger.get_files_from_objects(self._clipboard), target)
        self._clipboard = []
        self.paste_action.setEnabled(False)
