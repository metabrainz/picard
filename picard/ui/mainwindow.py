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

import os.path

from picard.album import Album
from picard.file import File
from picard.track import Track
from picard.cluster import Cluster
from picard.config import Option, BoolOption, TextOption
from picard.ui.coverartbox import CoverArtBox
from picard.ui.itemviews import FileTreeView, AlbumTreeView
from picard.ui.metadatabox import MetadataBox
from picard.ui.filebrowser import FileBrowser
from picard.ui.options import OptionsDialogProvider
from picard.ui.tageditor import TagEditor
#from picard.ui.advtageditor import AdvancedTagEditor as TagEditor
from picard.ui.puidsubmit import PUIDSubmitDialog

class MainWindow(QtGui.QMainWindow):

    options = [
        Option("persist", "window_state", QtCore.QByteArray(),
               QtCore.QVariant.toByteArray),
        Option("persist", "window_position", QtCore.QPoint(),
               QtCore.QVariant.toPoint),
        Option("persist", "window_size", QtCore.QSize(780, 580),
               QtCore.QVariant.toSize),
        BoolOption("persist", "window_maximized", False),
        BoolOption("persist", "view_cover_art", True),
        BoolOption("persist", "view_file_browser", False),
        TextOption("persist", "current_directory", ""),
    ]

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.selected_objects = []
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(_("MusicBrainz Picard"))
        icon = QtGui.QIcon()
        icon.addFile(":/images/Picard16.png")
        icon.addFile(":/images/Picard32.png")
        self.setWindowIcon(icon)

        self.createActions()
        self.createMenus()
        self.createStatusBar()
        self.createToolBar()

        centralWidget = QtGui.QWidget(self)
        self.setCentralWidget(centralWidget)

        self.splitter = QtGui.QSplitter(centralWidget)

        self.file_browser = FileBrowser(self.splitter)
        if not self.show_file_browser_action.isChecked():
            self.file_browser.hide()
        self.splitter.addWidget(self.file_browser)

        self.fileTreeView = FileTreeView(self, self.splitter)
        self.connect(self.fileTreeView, QtCore.SIGNAL("add_files"), QtCore.SIGNAL("add_files"))
        self.connect(self.fileTreeView, QtCore.SIGNAL("addDirectory"), QtCore.SIGNAL("addDirectory"))

        self.albumTreeView = AlbumTreeView(self, self.splitter)
        self.connect(self.albumTreeView, QtCore.SIGNAL("add_files"), QtCore.SIGNAL("add_files"))
        self.connect(self.albumTreeView, QtCore.SIGNAL("addDirectory"), QtCore.SIGNAL("addDirectory"))

        self.ignoreSelectionChange = False
        self.connect(self.fileTreeView, QtCore.SIGNAL("itemSelectionChanged()"), self.updateFileTreeSelection)
        self.connect(self.albumTreeView, QtCore.SIGNAL("itemSelectionChanged()"), self.updateAlbumTreeSelection)

        self.splitter.addWidget(self.fileTreeView)
        self.splitter.addWidget(self.albumTreeView)

        self.orig_metadata_box = MetadataBox(self, _("Original Metadata"), True)
        self.orig_metadata_box.disable()
        self.metadata_box = MetadataBox(self, _("New Metadata"), False)
        self.metadata_box.disable()

        self.connect(self.orig_metadata_box, QtCore.SIGNAL("file_updated(int)"), self, QtCore.SIGNAL("file_updated(int)"))
        self.connect(self.metadata_box, QtCore.SIGNAL("file_updated(int)"), self, QtCore.SIGNAL("file_updated(int)"))

        self.cover_art_box = CoverArtBox(self)
        if not self.show_cover_art_action.isChecked():
            self.cover_art_box.hide()

        bottomLayout = QtGui.QHBoxLayout()
        bottomLayout.addWidget(self.orig_metadata_box, 1)
        bottomLayout.addWidget(self.metadata_box, 1)
        bottomLayout.addWidget(self.cover_art_box, 0)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.splitter, 1)
        mainLayout.addLayout(bottomLayout, 0)

        centralWidget.setLayout(mainLayout)

        # FIXME: use QApplication's clipboard
        self._clipboard = []

        self.restoreWindowState()

    def closeEvent(self, event):
        self.saveWindowState()
        event.accept()

    def saveWindowState(self):
        self.config.persist["window_state"] = self.saveState()
        isMaximized = int(self.windowState()) & QtCore.Qt.WindowMaximized != 0
        if isMaximized:
            # FIXME: this doesn't include the window frame
            geom = self.normalGeometry()
            self.config.persist["window_position"] = geom.topLeft()
            self.config.persist["window_size"] = geom.size()
        else:
            self.config.persist["window_position"] = self.pos()
            self.config.persist["window_size"] = self.size()
        self.config.persist["window_maximized"] = isMaximized
        self.config.persist["view_cover_art"] = self.show_cover_art_action.isChecked()
        self.fileTreeView.saveState()
        self.albumTreeView.saveState()

    def restoreWindowState(self):
        self.restoreState(self.config.persist["window_state"])
        self.move(self.config.persist["window_position"])
        self.resize(self.config.persist["window_size"])
        if self.config.persist["window_maximized"]:
            self.setWindowState(QtCore.Qt.WindowMaximized)

    def createStatusBar(self):
        self.statusBar().showMessage(_("Ready"))

    def createActions(self):
        
        def get_icon(name, menu=True, toolbar=True):
            icon = QtGui.QIcon()
            if menu:
                icon.addFile(":/images/16x16/%s.png" % name)
            if toolbar:
                icon.addFile(":/images/22x22/%s.png" % name)
            return icon
        
        self.options_action = QtGui.QAction(
            get_icon("preferences-system"), _("&Options..."), self)
        self.connect(self.options_action, QtCore.SIGNAL("triggered()"),
                     self.show_options)

        self.cut_action = QtGui.QAction(
            QtGui.QIcon(":/images/16x16/edit-cut.png"), _(u"&Cut"), self)
        self.cut_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+X")))
        self.cut_action.setEnabled(False)
        self.connect(self.cut_action, QtCore.SIGNAL("triggered()"),
                     self.cut)
        
        self.paste_action = QtGui.QAction(
            QtGui.QIcon(":/images/16x16/edit-paste.png"), _(u"&Paste"), self)
        self.paste_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+V")))
        self.paste_action.setEnabled(False)
        self.connect(self.paste_action, QtCore.SIGNAL("triggered()"),
                     self.paste)
        
        self.help_action = QtGui.QAction(_("&Help..."), self)
        # TR: Keyboard shortcut for "Help..."
        self.help_action.setShortcut(QtGui.QKeySequence(_("Ctrl+H")))
        self.connect(self.help_action, QtCore.SIGNAL("triggered()"),
                     self.show_help)

        self.about_action = QtGui.QAction(_("&About..."), self)
        self.connect(self.about_action, QtCore.SIGNAL("triggered()"),
                     self.show_about)

        self.add_files_action = QtGui.QAction(
            get_icon("document-open"), _(u"&Add Files..."), self)
        self.add_files_action.setStatusTip(_(u"Add files to the tagger"))
        # TR: Keyboard shortcut for "Add Files..."
        self.add_files_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+O")))
        self.connect(self.add_files_action, QtCore.SIGNAL("triggered()"),
                     self.add_files)

        self.add_directory_action = QtGui.QAction(
            get_icon("folder"), _(u"A&dd Directory..."), self)
        self.add_directory_action.setStatusTip(
            _(u"Add a directory to the tagger"))
        # TR: Keyboard shortcut for "Add Directory..."
        self.add_directory_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+D")))
        self.connect(self.add_directory_action, QtCore.SIGNAL("triggered()"),
                     self.addDirectory)

        self.save_action = QtGui.QAction(
            get_icon("document-save"), _(u"&Save"), self)
        self.add_directory_action.setStatusTip(_(u"Save selected files"))
        # TR: Keyboard shortcut for "Save"
        self.save_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+S")))
        self.save_action.setEnabled(False)
        self.connect(self.save_action, QtCore.SIGNAL("triggered()"), self.save)

        self.submit_action = QtGui.QAction(
            QtGui.QIcon(":/images/ToolbarSubmit.png"),
            _(u"S&ubmit PUIDs to MusicBrainz"), self)
        #self.submit_action.setEnabled(False)
        self.connect(self.submit_action, QtCore.SIGNAL("triggered()"),
                     self.submit)

        self.exit_action = QtGui.QAction(_(u"E&xit"), self)
        # TR: Keyboard shortcut for "Exit"
        self.exit_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+Q")))
        self.connect(self.exit_action, QtCore.SIGNAL("triggered()"),
                     self.close)

        self.remove_action = QtGui.QAction(QtGui.QIcon(":/images/remove.png"),
                                           _(u"&Remove"), self)
        self.remove_action.setShortcut(QtGui.QKeySequence("Del"))
        self.remove_action.setEnabled(False)
        self.connect(self.remove_action, QtCore.SIGNAL("triggered()"),
                     self.remove)

        self.show_file_browser_action = QtGui.QAction(_(u"File &Browser"),
                                                      self)
        self.show_file_browser_action.setCheckable(True)
        if self.config.persist["view_file_browser"]:
            self.show_file_browser_action.setChecked(True)
        self.connect(self.show_file_browser_action,
                     QtCore.SIGNAL("triggered()"), self.show_file_browser)

        self.show_cover_art_action = QtGui.QAction(_(u"&Cover Art"), self)
        self.show_cover_art_action.setCheckable(True)
        if self.config.persist["view_cover_art"]:
            self.show_cover_art_action.setChecked(True)
        self.connect(self.show_cover_art_action, QtCore.SIGNAL("triggered()"),
                     self.show_cover_art)

        self.search_action = QtGui.QAction(QtGui.QIcon(":/images/search.png"),
                                           _(u"Search"), self)
        self.connect(self.search_action, QtCore.SIGNAL("triggered()"),
                     self.search)

        self.cd_lookup_action = QtGui.QAction(
            QtGui.QIcon(":/images/ToolbarLookup.png"), _(u"&Lookup CD"), self)
        # TR: Keyboard shortcut for "Lookup CD"
        self.cd_lookup_action.setShortcut(QtGui.QKeySequence(_("Ctrl+L")))
        self.connect(self.cd_lookup_action, QtCore.SIGNAL("triggered()"),
                     self.lookup_cd)

        self.analyze_action = QtGui.QAction(
            QtGui.QIcon(":/images/analyze.png"), _(u"Anal&yze"), self)
        self.analyze_action.setEnabled(False)
        # TR: Keyboard shortcut for "Analyze"
        self.analyze_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+Y")))
        self.connect(self.analyze_action, QtCore.SIGNAL("triggered()"),
                     self.analyze)

        self.cluster_action = QtGui.QAction(
            QtGui.QIcon(":/images/ToolbarCluster.png"), _(u"Cluster"), self)
        #self.cluster_action.setEnabled(False)
        # TR: Keyboard shortcut for "Cluster"
        self.cluster_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+U")))
        self.connect(self.cluster_action, QtCore.SIGNAL("triggered()"),
                     self.cluster)

        self.auto_tag_action = QtGui.QAction(
            QtGui.QIcon(":/images/magic-wand.png"), _(u"Auto Tag"), self)
        # TR: Keyboard shortcut for "Auto Tag"
        self.auto_tag_action.setShortcut(QtGui.QKeySequence(_(u"Ctrl+T")))
        self.connect(self.auto_tag_action, QtCore.SIGNAL("triggered()"),
                     self.auto_tag)

        self.edit_tags_action = QtGui.QAction(QtGui.QIcon(":/images/tag.png"),
                                              _(u"Edit &Tags..."), self)
        self.edit_tags_action.setEnabled(False)
        self.connect(self.edit_tags_action, QtCore.SIGNAL("triggered()"),
                     self.edit_tags)

        self.refresh_action = QtGui.QAction(
            get_icon("view-refresh", toolbar=False), _("&Refresh"), self)
        self.connect(
            self.refresh_action, QtCore.SIGNAL("triggered()"), self.refresh)

        self.generate_cuesheet_action = QtGui.QAction(_("Generate &Cuesheet..."), self)
        self.connect(self.generate_cuesheet_action, QtCore.SIGNAL("triggered()"),
                     self.generate_cuesheet)
        self.generate_playlist_action = QtGui.QAction(_("Generate &Playlist..."), self)
        self.connect(self.generate_playlist_action, QtCore.SIGNAL("triggered()"),
                     self.generate_playlist)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu(_(u"&File"))
        self.fileMenu.addAction(self.add_files_action)
        self.fileMenu.addAction(self.add_directory_action)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.save_action)
        self.fileMenu.addAction(self.submit_action)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exit_action)
        self.editMenu = self.menuBar().addMenu(_(u"&Edit"))
        self.editMenu.addAction(self.cut_action)
        self.editMenu.addAction(self.paste_action)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.options_action)
        self.viewMenu = self.menuBar().addMenu(_(u"&View"))
        self.viewMenu.addAction(self.show_file_browser_action)
        self.viewMenu.addAction(self.show_cover_art_action)
        self.toolsMenu = self.menuBar().addMenu(_(u"&Tools"))
        self.toolsMenu.addAction(self.generate_cuesheet_action)
        self.toolsMenu.addAction(self.generate_playlist_action)
        self.menuBar().addSeparator()
        self.helpMenu = self.menuBar().addMenu(_(u"&Help"))
        self.helpMenu.addAction(self.help_action)
        self.helpMenu.addAction(self.about_action)

    def createToolBar(self):
        self.mainToolBar = self.addToolBar(_(u"&File"))
        self.mainToolBar.setObjectName("fileToolbar")
        self.mainToolBar.addAction(self.add_files_action)
        self.mainToolBar.addAction(self.add_directory_action)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.save_action)
        self.mainToolBar.addAction(self.submit_action)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.cd_lookup_action)
        self.mainToolBar.addAction(self.analyze_action)
        self.mainToolBar.addAction(self.cluster_action)
        self.mainToolBar.addAction(self.auto_tag_action)
        self.mainToolBar.addAction(self.edit_tags_action)
        self.mainToolBar.addAction(self.remove_action)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.options_action)

        self.searchToolBar = self.addToolBar(_(u"&Search"))
        self.searchToolBar.setObjectName("searchToolbar")

        searchPanel = QtGui.QWidget(self.searchToolBar)
        hbox = QtGui.QHBoxLayout(searchPanel)

        self.searchEdit = QtGui.QLineEdit(searchPanel)
        self.connect(self.searchEdit, QtCore.SIGNAL("returnPressed()"), self.search)
        hbox.addWidget(self.searchEdit, 0)

        self.searchCombo = QtGui.QComboBox(searchPanel)
        self.searchCombo.addItem(_(u"Album"), QtCore.QVariant("album"))
        self.searchCombo.addItem(_(u"Artist"), QtCore.QVariant("artist"))
        self.searchCombo.addItem(_(u"Track"), QtCore.QVariant("track"))
        hbox.addWidget(self.searchCombo, 0)

        #button = QtGui.QPushButton(_("&Search"), searchPanel)
        #self.connect(button, QtCore.SIGNAL("clicked()"), self.search)
        #hbox.addWidget(button, 0)

        self.searchToolBar.addWidget(searchPanel)
        self.searchToolBar.addAction(self.search_action)

    def set_status_bar_message(self, message, timeout=0):
        """Set the status bar message."""
        self.statusBar().showMessage(message, timeout)

    def clear_status_bar_message(self):
        """Set the status bar message."""
        self.statusBar().clearMessage()

    def search(self):
        """Search for album, artist or track on the MusicBrainz website."""
        text = unicode(self.searchEdit.text())
        type = unicode(self.searchCombo.itemData(
                       self.searchCombo.currentIndex()).toString())
        self.tagger.search(text, type)

    def add_files(self):
        """Add files to the tagger."""
        currentDirectory = self.config.persist["current_directory"]
        formats = []
        extensions = []
        for format in self.tagger.get_supported_formats():
            ext = u"*%s" % format[0]
            formats.append(u"%s (%s)" % (format[1], ext))
            extensions.append(ext)
        formats.sort()
        extensions.sort()
        formats.insert(0, _(u"All Supported Formats") + u" (%s)" % u" ".join(extensions))
        files = QtGui.QFileDialog.getOpenFileNames(self, "", currentDirectory, u";;".join(formats))
        if files:
            files = map(unicode, files)
            self.config.persist["current_directory"] = os.path.dirname(files[0])
            self.tagger.add_files(files)

    def addDirectory(self):
        """Add directory to the tagger."""
        currentDirectory = self.config.persist["current_directory"]
        directory = QtGui.QFileDialog.getExistingDirectory(self, "", currentDirectory)
        if directory:
            directory = unicode(directory)
            self.config.persist["current_directory"] = directory
            self.tagger.add_directory(directory)

    def generate_cuesheet(self):
        """Generate a cuesheet."""
        #currentDirectory = self.config.persist["current_directory"]
        #formats = _("Cuesheet (*.cue)")
        #selectedFormat = QtCore.QString()
        #filename = QtGui.QFileDialog.getSaveFileName(self, "", currentDirectory, formats, selectedFormat)
        #if filename:
        #    filename = unicode(filename)
        #    self.set_status_bar_message(_("Saving cuesheet %s...") % filename)
        #    self.config.persist["current_directory"] = os.path.dirname(filename)
        #    self.tagger.generate_cuesheet(self.selected_objects, filename)
        #    self.set_status_bar_message(_("Cuesheet %s saved") % filename, 1000)

    def generate_playlist(self):
        """Generate a playlist."""
        from picard.playlist import Playlist
        currentDirectory = self.config.persist["current_directory"]
        formats = [_(f[0]) for f in Playlist.formats]
        selected_format = QtCore.QString()
        filename = QtGui.QFileDialog.getSaveFileName(self, "", currentDirectory, ";;".join(formats), selected_format)
        if filename:
            filename = unicode(filename)
            self.config.persist["current_directory"] = os.path.dirname(filename)
            self.set_status_bar_message(_("Saving playlist %s...") % filename)
            playlist = Playlist(self.selected_objects[0])
            playlist.save(filename, formats.index(unicode(selected_format)))
            self.set_status_bar_message(_("Playlist %s saved") % filename, 1000)

    def show_about(self):
        self.show_options("about")

    def show_options(self, page=None):
        dlg = OptionsDialogProvider(self.tagger).get_options_dialog(self, page)
        dlg.exec_()

    def show_help(self):
        from picard.browser.launch import Launch
        Launch(None).launch("http://musicbrainz.org/doc/PicardDocumentation")

    def save(self):
        """Tell the tagger to save the selected objects."""
        self.tagger.save(self.selected_objects)

    def remove(self):
        """Tell the tagger to remove the selected objects."""
        self.tagger.remove(self.selected_objects)

    def submit(self):
        dialog = PUIDSubmitDialog(self)
        if dialog.exec_():
            self.tagger.submit_puids(dialog.puids_to_submit)

    def lookup_cd(self):
        self.tagger.lookup_cd()

    def analyze(self):
        self.tagger.analyze(self.selected_objects)

    def edit_tags(self, obj=None):
        if not obj:
            obj = self.selected_objects[0]
        if isinstance(obj, Track):
            obj = obj.linked_file
        tagedit = TagEditor(obj, self)
        tagedit.exec_()

    def cluster(self):
        objs = self.selected_objects
        self.tagger.cluster(objs)

    def refresh(self):
        self.tagger.refresh(self.selected_objects)

    def updateFileTreeSelection(self):
        if not self.ignoreSelectionChange:
            objs = self.fileTreeView.selected_objects()
            if objs:
                self.ignoreSelectionChange = True
                self.albumTreeView.clearSelection()
                self.ignoreSelectionChange = False
            self.updateSelection(objs)

    def updateAlbumTreeSelection(self):
        if not self.ignoreSelectionChange:
            objs = self.albumTreeView.selected_objects()
            if objs:
                self.ignoreSelectionChange = True
                self.fileTreeView.clearSelection()
                self.ignoreSelectionChange = False
            self.updateSelection(objs)

    def update_actions(self):
        can_remove = False
        can_save = False
        can_edit_tags = False
        can_analyze = False
        can_refresh = False
        for obj in self.selected_objects:
            if obj.can_analyze():
                can_analyze = True
            if obj.can_save():
                can_save = True
            if obj.can_remove():
                can_remove = True
            if obj.can_edit_tags():
                can_edit_tags = True
            if obj.can_refresh():
                can_refresh = True
            if can_save and can_remove and can_edit_tags and can_refresh:
                break
        self.remove_action.setEnabled(can_remove)
        self.save_action.setEnabled(can_save)
        self.edit_tags_action.setEnabled(can_edit_tags)
        self.analyze_action.setEnabled(can_analyze)
        self.refresh_action.setEnabled(can_refresh)
        self.cut_action.setEnabled(bool(self.selected_objects))

    def updateSelection(self, objects=None):
        if objects is not None:
            self.selected_objects = objects
        else:
            objects = self.selected_objects

        self.update_actions()

        orig_metadata = None
        metadata = None
        is_album = False
        statusBar = u""
        file = None
        if len(objects) == 1:
            obj = objects[0]
            if isinstance(obj, File):
                orig_metadata = obj.orig_metadata
                metadata = obj.metadata
                statusBar = obj.filename
                if obj.state == obj.ERROR:
                    statusBar += _(" (Error: %s)") % obj.error
                file = obj
            elif isinstance(obj, Track):
                if obj.linked_file:
                    orig_metadata = obj.linked_file.orig_metadata
                    metadata = obj.linked_file.metadata
                    statusBar = "%s (%d%%)" % (obj.linked_file.filename, obj.linked_file.similarity * 100)
                    file = obj.linked_file
                else:
                    orig_metadata = obj.metadata
                    metadata = obj.metadata
            elif isinstance(obj, (Cluster, Album)):
                orig_metadata = obj.metadata
                metadata = obj.metadata
                is_album = True

        self.orig_metadata_box.set_metadata(orig_metadata, is_album)
        self.metadata_box.set_metadata(metadata, is_album, file=file)
        self.cover_art_box.set_metadata(metadata)
        self.set_status_bar_message(statusBar)

    def show_cover_art(self):
        """Show/hide the cover art box."""
        if self.show_cover_art_action.isChecked():
            self.cover_art_box.show()
        else:
            self.cover_art_box.hide()

    def show_file_browser(self):
        """Show/hide the file browser."""
        if self.show_file_browser_action.isChecked():
            self.file_browser.show()
        else:
            self.file_browser.hide()

    def auto_tag(self):
        self.tagger.auto_tag(self.selected_objects)

    def cut(self):
        self._clipboard = self.selected_objects
        self.paste_action.setEnabled(bool(self._clipboard))
    
    def paste(self):
        if not self.selected_objects:
            target = self.tagger.unmatched_files
        else:
            target = self.selected_objects[0]
        self.fileTreeView.drop_files(
            self.tagger.get_files_from_objects(self._clipboard),
            target)
        self._clipboard = []
        self.paste_action.setEnabled(False)
