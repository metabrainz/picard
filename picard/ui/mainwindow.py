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
        self.selectedObjects = []
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

        self.orig_metadataBox = MetadataBox(self, _("Local Metadata"), True)
        self.orig_metadataBox.disable()
        self.serverMetadataBox = MetadataBox(self, _("Server Metadata"), False)
        self.serverMetadataBox.disable()

        self.connect(self.orig_metadataBox, QtCore.SIGNAL("lookup"), self, QtCore.SIGNAL("lookup"))
        self.connect(self.orig_metadataBox, QtCore.SIGNAL("file_updated(int)"), self, QtCore.SIGNAL("file_updated(int)"))
        self.connect(self.serverMetadataBox, QtCore.SIGNAL("lookup"), self, QtCore.SIGNAL("lookup"))
        self.connect(self.serverMetadataBox, QtCore.SIGNAL("file_updated(int)"), self, QtCore.SIGNAL("file_updated(int)"))

        self.coverArtBox = CoverArtBox(self)
        if not self.showCoverArtAct.isChecked():
            self.coverArtBox.hide()                    
        
        bottomLayout = QtGui.QHBoxLayout()
        bottomLayout.addWidget(self.orig_metadataBox, 1)
        bottomLayout.addWidget(self.serverMetadataBox, 1)
        bottomLayout.addWidget(self.coverArtBox, 0)        
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.splitter, 1)
        mainLayout.addLayout(bottomLayout, 0)
        
        centralWidget.setLayout(mainLayout)
        
        self.restoreWindowState()
        
    def closeEvent(self, event):
        self.saveWindowState()
        event.accept()        
        
    def saveWindowState(self):
        self.config.persist.window_state = self.saveState()
        isMaximized = int(self.windowState()) & QtCore.Qt.WindowMaximized != 0
        if isMaximized:
            # FIXME: this doesn't include the window frame
            geom = self.normalGeometry()
            self.config.persist.window_position = geom.topLeft()
            self.config.persist.window_size = geom.size()
        else:
            self.config.persist.window_position = self.pos()
            self.config.persist.window_size = self.size()
        self.config.persist.window_maximized = isMaximized
        self.config.persist.view_cover_art = self.showCoverArtAct.isChecked()
        self.fileTreeView.saveState()
        self.albumTreeView.saveState()

    def restoreWindowState(self):
        self.restoreState(self.config.persist.window_state)
        self.move(self.config.persist.window_position)
        self.resize(self.config.persist.window_size)
        if self.config.persist.window_maximized:
            self.setWindowState(QtCore.Qt.WindowMaximized)
        
    def createStatusBar(self):
        self.statusBar().showMessage(_("Ready"))         
        
    def createActions(self):
        self.optionsAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarOptions.png"), "&Options...", self)
        #self.openSettingsAct.setShortcut("Ctrl+O")
        self.connect(self.optionsAct, QtCore.SIGNAL("triggered()"), self.showOptions)
        
        self.helpAct = QtGui.QAction(_("&Help..."), self)
        # TR: Keyboard shortcut for "Help"
        self.helpAct.setShortcut(QtGui.QKeySequence(_("Ctrl+H")))
        #self.connect(self.helpAct, QtCore.SIGNAL("triggered()"), self.showHelp)
        
        self.aboutAct = QtGui.QAction(_("&About..."), self)
        #self.connect(self.aboutAct, QtCore.SIGNAL("triggered()"), self.showAbout)
        
        self.add_filesAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarAddFiles.png"), _("&Add Files..."), self)
        self.add_filesAct.setStatusTip(_("Add files to the tagger"))
        # TR: Keyboard shortcut for "Add Files..."
        self.add_filesAct.setShortcut(QtGui.QKeySequence(_("Ctrl+O")))
        self.connect(self.add_filesAct, QtCore.SIGNAL("triggered()"), self.add_files)
        
        self.addDirectoryAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarAddDir.png"), _("A&dd Directory..."), self)
        self.addDirectoryAct.setStatusTip(_("Add a directory to the tagger"))
        # TR: Keyboard shortcut for "Add Directory..."
        self.addDirectoryAct.setShortcut(QtGui.QKeySequence(_("Ctrl+D")))
        self.connect(self.addDirectoryAct, QtCore.SIGNAL("triggered()"), self.addDirectory)
        
        self.saveAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarSave.png"), _("&Save Selected Files"), self)
        # TR: Keyboard shortcut for "Save files"
        self.saveAct.setShortcut(QtGui.QKeySequence(_("Ctrl+S")))
        self.saveAct.setEnabled(False)
        self.connect(self.saveAct, QtCore.SIGNAL("triggered()"), self.save)
        
        self.submitAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarSubmit.png"), _("S&ubmit PUIDs to MusicBrainz"), self)
        self.submitAct.setEnabled(False)
        self.connect(self.submitAct, QtCore.SIGNAL("triggered()"), self.submit)
        
        self.exitAct = QtGui.QAction(_("E&xit"), self)
        self.exitAct.setShortcut(QtGui.QKeySequence(_("Ctrl+Q")))
        self.connect(self.exitAct, QtCore.SIGNAL("triggered()"), self.close)

        self.removeAct = QtGui.QAction(QtGui.QIcon(":/images/remove.png"), _("&Remove"), self)
        self.removeAct.setShortcut(QtGui.QKeySequence(_("Del")))
        self.removeAct.setEnabled(False)
        self.connect(self.removeAct, QtCore.SIGNAL("triggered()"), self.remove)

        self.showFileBrowserAct = QtGui.QAction(_("File &Browser"), self)
        self.showFileBrowserAct.setCheckable(True)
        #if self.config.persi.value("persist/viewFileBrowser").toBool():
        #    self.showFileBrowserAct.setChecked(True)
 #       self.connect(self.showFileBrowserAct, QtCore.SIGNAL("triggered()"), self.showFileBrowser)
        
        self.showCoverArtAct = QtGui.QAction(_("&Cover Art"), self)
        self.showCoverArtAct.setCheckable(True)
        if self.config.persist.view_cover_art:
            self.showCoverArtAct.setChecked(True)
        self.connect(self.showCoverArtAct, QtCore.SIGNAL("triggered()"), self.showCoverArt)

        self.searchAct = QtGui.QAction(QtGui.QIcon(":/images/search.png"), _("Search"), self)
        self.connect(self.searchAct, QtCore.SIGNAL("triggered()"), self.search)

        self.listenAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarListen.png"), _("Listen"), self)
        self.listenAct.setEnabled(False)
        self.connect(self.listenAct, QtCore.SIGNAL("triggered()"), self.listen)

        self.cdLookupAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarLookup.png"), _("&Lookup CD"), self)
        self.cdLookupAct.setEnabled(False)
        self.cdLookupAct.setShortcut(QtGui.QKeySequence(_("Ctrl+L")))
        
        self.analyzeAct = QtGui.QAction(QtGui.QIcon(":/images/analyze.png"), _("Anal&yze"), self)
        self.analyzeAct.setEnabled(False)
        self.analyzeAct.setShortcut(QtGui.QKeySequence(_("Ctrl+Y")))
        
        self.clusterAct = QtGui.QAction(QtGui.QIcon(":/images/ToolbarCluster.png"), _("Cluster"), self)
        self.clusterAct.setEnabled(False)
        self.clusterAct.setShortcut(QtGui.QKeySequence(_("Ctrl+U")))

        self.autoTagAct = QtGui.QAction(QtGui.QIcon(":/images/magic-wand.png"), _("Auto Tag"), self)
        self.autoTagAct.setShortcut(QtGui.QKeySequence(_("Ctrl+T")))
        self.connect(self.autoTagAct, QtCore.SIGNAL("triggered()"), self.autoTag)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu(_("&File"))
        self.fileMenu.addAction(self.add_filesAct)
        self.fileMenu.addAction(self.addDirectoryAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.submitAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        
        self.editMenu = self.menuBar().addMenu(_("&Edit"))
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.optionsAct)
        
        self.viewMenu = self.menuBar().addMenu(_("&View"))
        self.viewMenu.addAction(self.showFileBrowserAct)
        self.viewMenu.addAction(self.showCoverArtAct)
        
        self.menuBar().addSeparator()
        
        self.helpMenu = self.menuBar().addMenu(_("&Help"))
        self.helpMenu.addAction(self.helpAct)         
        self.helpMenu.addAction(self.aboutAct)

    def createToolBar(self):
        self.mainToolBar = self.addToolBar(self.tr("File"))
        self.mainToolBar.setObjectName("fileToolbar")
        self.mainToolBar.addAction(self.add_filesAct)
        self.mainToolBar.addAction(self.addDirectoryAct)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.saveAct)
        self.mainToolBar.addAction(self.submitAct)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.cdLookupAct)
        self.mainToolBar.addAction(self.analyzeAct)
        self.mainToolBar.addAction(self.clusterAct)
        self.mainToolBar.addAction(self.autoTagAct)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.removeAct)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.optionsAct)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.listenAct)

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
        self.searchToolBar.addAction(self.searchAct)        
        
    def setStatusBarMessage(self, message):
        """Set the status bar message."""
        self.statusBar().showMessage(message)         

    def search(self):
        """Search for album, artist or track on MusicBrainz."""
        text = unicode(self.searchEdit.text())
        type = unicode(self.searchCombo.itemData(self.searchCombo.currentIndex()).toString())
        self.log.debug("Search, '%s', %s", text, type)
        self.emit(QtCore.SIGNAL("search"), text, type)

    def add_files(self):
        """Add files to the tagger."""
        currentDirectory = self.config.persist.current_directory
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
            files = [unicode(f) for f in files]
            self.config.persist.current_directory = os.path.dirname(files[0])
            self.emit(QtCore.SIGNAL("add_files"), files)
        
    def addDirectory(self):
        """Add directory to the tagger."""
        currentDirectory = self.config.persist.current_directory
        directory = QtGui.QFileDialog.getExistingDirectory(self, "", currentDirectory)
        if directory:
            directory = unicode(directory)
            self.config.persist.current_directory = directory
            self.emit(QtCore.SIGNAL("addDirectory"), directory)

    def showOptions(self):
        dlg = OptionsDialogProvider(self.tagger).get_options_dialog(self)
        dlg.exec_()
            
    def save(self):
        files = []
        for obj in self.selectedObjects:
            if isinstance(obj, File):
                files.append(obj)
                
        if files:
            self.tagger.save_files(files)
        
    def listen(self):
        pass
        
    def submit(self):
        pass
        
    def updateFileTreeSelection(self):
        if not self.ignoreSelectionChange:
            objs = self.fileTreeView.selectedObjects()
            if objs:
                self.ignoreSelectionChange = True
                self.albumTreeView.clearSelection()
                self.ignoreSelectionChange = False
            self.updateSelection(objs)
        
    def updateAlbumTreeSelection(self):
        if not self.ignoreSelectionChange:
            objs = self.albumTreeView.selectedObjects()
            if objs:
                self.ignoreSelectionChange = True
                self.fileTreeView.clearSelection()
                self.ignoreSelectionChange = False
            self.updateSelection(objs)
        
    def updateSelection(self, objects=None):
        if objects:
            self.selectedObjects = objects

        objects = self.selectedObjects

        canRemove = False
        canSave = False
        for obj in objects:
            if isinstance(obj, File):
                canRemove = True
                if obj.metadata.changed:
                    canSave = True
            elif isinstance(obj, Album):
                canRemove = True
            elif isinstance(obj, Track):
                if obj.isLinked():
                    canRemove = True
                    if obj.getLinkedFile().metadata.changed:
                        canSave = True
        self.removeAct.setEnabled(canRemove)
        self.saveAct.setEnabled(canSave)
        
        orig_metadata = None
        serverMetadata = None
        isAlbum = False
        statusBar = u""
        file_id = None
        if len(objects) == 1:
            obj = objects[0]
            if isinstance(obj, File):
                orig_metadata = obj.orig_metadata
                serverMetadata = obj.metadata
                statusBar = obj.filename
                file_id = obj.id
            elif isinstance(obj, Track):
                if obj.isLinked():
                    orig_metadata = obj.file.orig_metadata
                    serverMetadata = obj.file.metadata
                    statusBar = obj.file.filename
                    file_id = obj.file.id
                else:
                    orig_metadata = obj.metadata
                    serverMetadata = obj.metadata
            elif isinstance(obj, Album):
                orig_metadata = obj.metadata
                serverMetadata = obj.metadata
                isAlbum = True

        self.orig_metadataBox.setMetadata(orig_metadata, isAlbum)
        self.serverMetadataBox.setMetadata(serverMetadata, isAlbum, file_id=file_id)
        self.setStatusBarMessage(statusBar)

    def remove(self):
        files = []
        albums = []
        for obj in self.selectedObjects:
            if isinstance(obj, File):
                files.append(obj)
            elif isinstance(obj, Track):
                if obj.isLinked():
                    files.append(obj.getLinkedFile())
            elif isinstance(obj, Album):
                albums.append(obj)
                
        if files:
            self.tagger.remove_files(files)
            
        for album in albums:
            self.tagger.removeAlbum(album)
            

    def showCoverArt(self):
        """Show/hide the cover art box."""
        if self.showCoverArtAct.isChecked():
            self.coverArtBox.show()
        else:
            self.coverArtBox.hide()

    def autoTag(self):
        files = [obj for obj in self.selectedObjects if isinstance(obj, File)]
        self.tagger.autoTag(files)

