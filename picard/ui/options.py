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
from picard.component import *

class GeneralOptionsPage(QtCore.QObject):

    def getName(self):
        return _(u"General")

    def getPageWidget(self, parent=None):
        page = QtGui.QWidget(parent)
        vbox = QtGui.QVBoxLayout(page)

        title = QtGui.QLabel(u"General", page)
        font = title.font()
        font.setPointSize(11)
        font.setBold(True)
        title.setFont(font)
        vbox.addWidget(title, 0)

        line = QtGui.QFrame(page)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Plain)
        vbox.addWidget(line, 0)

        groupBox = QtGui.QGroupBox(_(u"MusicBrainz Server"), page)
        grid = QtGui.QGridLayout(groupBox)
        grid.addWidget(QtGui.QLabel(_(u"Host:"), groupBox), 0, 0)
        self.serverHostEdit = QtGui.QLineEdit(groupBox)
        self.serverHostEdit.setText(self.config.setting.getString("serverHost", ""))
        grid.addWidget(self.serverHostEdit, 0, 1)
        grid.addWidget(QtGui.QLabel(_(u"Port:"), groupBox), 0, 2)
        self.serverPortEdit = QtGui.QLineEdit(groupBox)
        self.serverPortEdit.setText(self.config.setting.getString("serverPort", ""))
        grid.addWidget(self.serverPortEdit, 0, 3)
        grid.setColumnStretch(1, 5)
        grid.setColumnStretch(3, 1)
        vbox.addWidget(groupBox)
        
        groupBox = QtGui.QGroupBox(_(u"MusicBrainz Account"), page)
        grid = QtGui.QGridLayout(groupBox)
        grid.addWidget(QtGui.QLabel(_(u"Username:"), groupBox), 0, 0)
        self.usernameEdit = QtGui.QLineEdit(groupBox)
        self.usernameEdit.setText(self.config.setting.getString("username", ""))
        grid.addWidget(self.usernameEdit, 0, 1)
        grid.addWidget(QtGui.QLabel(_(u"Password:"), groupBox), 1, 0)
        self.passwordEdit = QtGui.QLineEdit(groupBox)
        self.passwordEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.passwordEdit.setText(self.config.setting.getString("password", ""))
        grid.addWidget(self.passwordEdit, 1, 1)
        vbox.addWidget(groupBox)
        
        vbox.addStretch(1)
        
        return page

    def saveSettings(self):
        self.config.setting.set("serverHost", self.serverHostEdit.text())
        self.config.setting.set("serverPort", self.serverPortEdit.text())
        self.config.setting.set("username", self.usernameEdit.text())
        self.config.setting.set("password", self.passwordEdit.text())

class AboutOptionsPage(QtCore.QObject):

    def getName(self):
        return _(u"About")

    def getPageWidget(self, parent=None):
        page = QtGui.QWidget(parent)
        vbox = QtGui.QVBoxLayout(page)
        
        title = QtGui.QLabel(u"About", page)
        font = title.font()
        font.setPointSize(11)
        font.setBold(True)
        title.setFont(font)
        vbox.addWidget(title, 0)
        
        line = QtGui.QFrame(page)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Plain)
        vbox.addWidget(line, 0)
        
        vbox.addStretch(1)
        
        return page

    def saveSettings(self):
        pass

class OptionsDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi()
        
    def setupUi(self):
        self.setWindowTitle(_("Options"))
        
        self.splitter = QtGui.QSplitter(self)
        
        self.pagesTree = QtGui.QTreeWidget(self.splitter)
        self.pagesTree.setHeaderLabels([u"Name"])
        self.pagesTree.header().hide()
        self.connect(self.pagesTree, QtCore.SIGNAL("itemSelectionChanged()"),
            self.switchPage)
        self.splitter.addWidget(self.pagesTree)
        
        self.pagesStackWidget = QtGui.QWidget(self.splitter)
        self.pagesStack = QtGui.QStackedLayout(self.pagesStackWidget)
        self.splitter.addWidget(self.pagesStackWidget)
        
        self.okButton = QtGui.QPushButton(_("OK"), self)
        self.connect(self.okButton, QtCore.SIGNAL("clicked()"), self.accept)
        self.cancelButton = QtGui.QPushButton(_("Cancel"), self)
        self.connect(self.cancelButton, QtCore.SIGNAL("clicked()"), self.reject)
        
        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton, 0)
        buttonLayout.addWidget(self.cancelButton, 0)
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.splitter)
        mainLayout.addLayout(buttonLayout)
        
        self.setLayout(mainLayout)
        
        self.pageProviders = [
            GeneralOptionsPage(),
            AboutOptionsPage(),
        ]
        self.items = []
        self.itemToPage = {}
        
        for pageProvider in self.pageProviders:
            name = pageProvider.getName()
            page = pageProvider.getPageWidget()
            item = QtGui.QTreeWidgetItem(self.pagesTree)
            item.setText(0, name)
            self.itemToPage[item] = page
            self.pagesStack.addWidget(page)

        self.restoreWindowState()
            
    def switchPage(self):
        item = self.pagesTree.selectedItems()[0]
        page = self.itemToPage[item]
        self.pagesStack.setCurrentWidget(page)

    def accept(self):
        for pageProvider in self.pageProviders:
            pageProvider.saveSettings()
        QtGui.QDialog.accept(self)

    def closeEvent(self, event):
        self.saveWindowState()
        event.accept()

    def saveWindowState(self):
        self.config.persist.set("optionsDialogPosition", self.pos())
        self.config.persist.set("optionsDialogSize", self.size())
        self.config.persist.set("optionsDialogSplitter", self.splitter.saveState())

    def restoreWindowState(self):
        self.move(self.config.persist.get("optionsDialogPosition").toPoint())
        self.resize(self.config.persist.get("optionsDialogSize").toSize())
        self.splitter.restoreState(
            self.config.persist.get("optionsDialogSplitter").toByteArray())

