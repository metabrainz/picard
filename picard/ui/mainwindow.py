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
import sys

from picard.album import Album
from picard.file import File
from picard.track import Track
from picard.util import decode_filename, encode_filename
from picard.config import Option, BoolOption, TextOption
from picard.ui.coverartbox import CoverArtBox
from picard.ui.metadatabox import MetadataBox
from picard.ui.itemviews import FileTreeView, AlbumTreeView
from picard.ui.options import OptionsDialog, OptionsDialogProvider
from picard.ui.tageditor import TagEditor

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
        self.options_action = QtGui.QAction(QtGui.QIcon(":/images/ToolbarOptions.png"), "&Options...", self)
        self.connect(self.options_action, QtCore.SIGNAL("triggered()"),
                     self.show_options)
        
        self.help_action = QtGui.QAction(_("&Help..."), self)
        self.help_action.setShortcut(QtGui.QKeySequence(_("Ctrl+H")))
        self.connect(self.help_action, QtCore.SIGNAL("triggered()"),
                     self.show_help)

        self.about_action = QtGui.QAction(_("&About..."), self)
        self.connect(self.about_action, QtCore.SIGNAL("triggered()"),
                     self.show_about)

        self.add_files_action = QtGui.QAction(QtGui.QIcon(":/images/ToolbarAddFiles.png"), _("&Add Files..."), self)
        self.add_files_action.setStatusTip(_("Add files to the tagger"))
        # TR: Keyboard shortcut for "Add Files..."
        self.add_files_action.setShortcut(QtGui.QKeySequence(_("Ctrl+O")))
        self.connect(self.add_files_action, QtCore.SIGNAL("triggered()"), self.add_files)
        
        self.add_directory_action = QtGui.QAction(QtGui.QIcon(":/images/ToolbarAddDir.png"), _("A&dd Directory..."), self)
        self.add_directory_action.setStatusTip(_("Add a directory to the tagger"))
        # TR: Keyboard shortcut for "Add Directory..."
        self.add_directory_action.setShortcut(QtGui.QKeySequence(_("Ctrl+D")))
        self.connect(self.add_directory_action, QtCore.SIGNAL("triggered()"), self.addDirectory)
        
        self.save_action = QtGui.QAction(QtGui.QIcon(":/images/ToolbarSave.png"), _("&Save"), self)
        self.add_directory_action.setStatusTip(_("Save selected files"))
        # TR: Keyboard shortcut for "Save"
        self.save_action.setShortcut(QtGui.QKeySequence(_("Ctrl+S")))
        self.save_action.setEnabled(False)
        self.connect(self.save_action, QtCore.SIGNAL("triggered()"), self.save)
        
        self.submit_action = QtGui.QAction(QtGui.QIcon(":/images/ToolbarSubmit.png"), _("S&ubmit PUIDs to MusicBrainz"), self)
        self.submit_action.setEnabled(False)
        self.connect(self.submit_action, QtCore.SIGNAL("triggered()"), self.submit)
        
        self.exitAct = QtGui.QAction(_("E&xit"), self)
        self.exitAct.setShortcut(QtGui.QKeySequence(_("Ctrl+Q")))
        self.connect(self.exitAct, QtCore.SIGNAL("triggered()"), self.close)

        self.remove_action = QtGui.QAction(QtGui.QIcon(":/images/remove.png"), _("&Remove"), self)
        self.remove_action.setShortcut(QtGui.QKeySequence(_("Del")))
        self.remove_action.setEnabled(False)
        self.connect(self.remove_action, QtCore.SIGNAL("triggered()"), self.remove)

        self.show_file_browser_action = QtGui.QAction(_("File &Browser"), self)
        self.show_file_browser_action.setCheckable(True)
        #if self.config.persi.value("persist/viewFileBrowser").toBool():
        #    self.show_file_browser_action.setChecked(True)
 #       self.connect(self.show_file_browser_action, QtCore.SIGNAL("triggered()"), self.showFileBrowser)
        
        self.show_cover_art_action = QtGui.QAction(_("&Cover Art"), self)
        self.show_cover_art_action.setCheckable(True)
        if self.config.persist["view_cover_art"]:
            self.show_cover_art_action.setChecked(True)
        self.connect(self.show_cover_art_action, QtCore.SIGNAL("triggered()"), self.showCoverArt)

        self.search_action = QtGui.QAction(QtGui.QIcon(":/images/search.png"), _("Search"), self)
        self.connect(self.search_action, QtCore.SIGNAL("triggered()"), self.search)

        self.cd_lookup_action = QtGui.QAction(QtGui.QIcon(":/images/ToolbarLookup.png"), _("&Lookup CD"), self)
        self.cd_lookup_action.setEnabled(False)
        self.cd_lookup_action.setShortcut(QtGui.QKeySequence(_("Ctrl+L")))
        
        self.analyze_action = QtGui.QAction(QtGui.QIcon(":/images/analyze.png"), _("Anal&yze"), self)
        self.analyze_action.setEnabled(False)
        self.analyze_action.setShortcut(QtGui.QKeySequence(_("Ctrl+Y")))
        
        self.cluster_action = QtGui.QAction(QtGui.QIcon(":/images/ToolbarCluster.png"), _("Cluster"), self)
        self.cluster_action.setEnabled(False)
        self.cluster_action.setShortcut(QtGui.QKeySequence(_("Ctrl+U")))

        self.auto_tag_action = QtGui.QAction(QtGui.QIcon(":/images/magic-wand.png"), _("Auto Tag"), self)
        self.auto_tag_action.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
        self.connect(self.auto_tag_action, QtCore.SIGNAL("triggered()"), self.autoTag)
        
        self.edit_tags_action = QtGui.QAction(QtGui.QIcon(":/images/tag.png"),
                                              _("Edit &Tags..."), self)
        self.edit_tags_action.setEnabled(False)
        self.connect(self.edit_tags_action, QtCore.SIGNAL("triggered()"),
                     self.edit_tags)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu(_("&File"))
        self.fileMenu.addAction(self.add_files_action)
        self.fileMenu.addAction(self.add_directory_action)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.save_action)
        self.fileMenu.addAction(self.submit_action)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        
        self.editMenu = self.menuBar().addMenu(_("&Edit"))
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.options_action)
        
        self.viewMenu = self.menuBar().addMenu(_("&View"))
        self.viewMenu.addAction(self.show_file_browser_action)
        self.viewMenu.addAction(self.show_cover_art_action)
        
        self.menuBar().addSeparator()
        
        self.helpMenu = self.menuBar().addMenu(_("&Help"))
        self.helpMenu.addAction(self.help_action)         
        self.helpMenu.addAction(self.about_action)

    def createToolBar(self):
        self.mainToolBar = self.addToolBar(self.tr("File"))
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
        #self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.edit_tags_action)
        self.mainToolBar.addAction(self.remove_action)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.options_action)
        #self.mainToolBar.addSeparator()

        self.searchToolBar = self.addToolBar(_("Search"))
        self.searchToolBar.setObjectName("searchToolbar")
        
        searchPanel = QtGui.QWidget(self.searchToolBar)
        hbox = QtGui.QHBoxLayout(searchPanel) 
        
        self.searchEdit = QtGui.QLineEdit(searchPanel)
        self.connect(self.searchEdit, QtCore.SIGNAL("returnPressed()"), self.search)
        hbox.addWidget(self.searchEdit, 0)
        
        self.searchCombo = QtGui.QComboBox(searchPanel)
        self.searchCombo.addItem(_("Album"), QtCore.QVariant("album"))
        self.searchCombo.addItem(_("Artist"), QtCore.QVariant("artist"))
        self.searchCombo.addItem(_("Track"), QtCore.QVariant("track"))
        hbox.addWidget(self.searchCombo, 0)
            
        #button = QtGui.QPushButton(_("&Search"), searchPanel)
        #self.connect(button, QtCore.SIGNAL("clicked()"), self.search)
        #hbox.addWidget(button, 0)
        
        self.searchToolBar.addWidget(searchPanel)
        self.searchToolBar.addAction(self.search_action)        
        
    def set_status_bar_message(self, message):
        """Set the status bar message."""
        self.statusBar().showMessage(message)         

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
        pass

    def edit_tags(self, obj=None):
        if not obj:
            obj = self.selected_objects[0]
        if isinstance(obj, Track):
            obj = obj.linked_file
        tagedit = TagEditor(obj, self)
        tagedit.exec_()

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
        for obj in self.selected_objects:
            if obj.can_save():
                can_save = True
            if obj.can_remove():
                can_remove = True
            if obj.can_edit_tags():
                can_edit_tags = True
            if can_save and can_remove and can_edit_tags:
                break
        if len(self.selected_objects) != 1:
            can_edit_tags = False
        self.remove_action.setEnabled(can_remove)
        self.save_action.setEnabled(can_save)
        self.edit_tags_action.setEnabled(can_edit_tags)

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
            elif isinstance(obj, Album):
                orig_metadata = obj.metadata
                metadata = obj.metadata
                is_album = True

        self.orig_metadata_box.set_metadata(orig_metadata, is_album)
        self.metadata_box.set_metadata(metadata, is_album, file=file)
        self.cover_art_box.set_metadata(metadata)
        self.set_status_bar_message(statusBar)

    def showCoverArt(self):
        """Show/hide the cover art box."""
        if self.show_cover_art_action.isChecked():
            self.cover_art_box.show()
        else:
            self.cover_art_box.hide()

    def autoTag(self):
        files = [obj for obj in self.selected_objects if isinstance(obj, File)]
        self.tagger.autoTag(files)

        
