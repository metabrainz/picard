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

class TagEditor(QtGui.QDialog):
    
    def __init__(self, metadata, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.metadata = metadata
        self.setupUi()
        self.load()
        
    def setupUi(self):
        self.setWindowTitle(_("Tag Editor"))

        self.tabs = QtGui.QTabWidget(self)
        
        self.gridlayout1 = QtGui.QGridLayout()
        self.gridlayout1.setSpacing(2)
        
        row = 0
        
        self.gridlayout1.addWidget(QtGui.QLabel(_("Title:")), row, 0, QtCore.Qt.AlignLeft)
        self.titleEdit = QtGui.QLineEdit(self.tabs)
        self.gridlayout1.addWidget(self.titleEdit, row, 1)
        
        row += 1
        
        self.gridlayout1.addWidget(QtGui.QLabel(_("Album:")), row, 0, QtCore.Qt.AlignLeft)
        self.albumEdit = QtGui.QLineEdit(self.tabs)
        self.gridlayout1.addWidget(self.albumEdit, row, 1)
        
        row += 1
        
        self.gridlayout1.addWidget(QtGui.QLabel(_("Artist:")), row, 0, QtCore.Qt.AlignLeft)
        self.artistEdit = QtGui.QLineEdit(self.tabs)
        self.gridlayout1.addWidget(self.artistEdit, row, 1)
        
        row += 1
        
        self.gridlayout1.addWidget(QtGui.QLabel(_("Track:")), row, 0, QtCore.Qt.AlignLeft)
        
        self.trackNumberEdit = QtGui.QLineEdit(self.tabs)
        self.totalTracksEdit = QtGui.QLineEdit(self.tabs)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.trackNumberEdit, 1)
        hbox.addWidget(QtGui.QLabel(_(u" of ")))
        hbox.addWidget(self.totalTracksEdit, 1)
        hbox.addStretch(9)
        
        self.gridlayout1.addLayout(hbox, row, 1)
        
        row += 1
        
        self.gridlayout1.addWidget(QtGui.QLabel(_("Disc:")), row, 0, QtCore.Qt.AlignLeft)
        
        self.discNumberEdit = QtGui.QLineEdit(self.tabs)
        self.totalDiscsEdit = QtGui.QLineEdit(self.tabs)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.discNumberEdit, 1)
        hbox.addWidget(QtGui.QLabel(_(u" of ")))
        hbox.addWidget(self.totalDiscsEdit, 1)
        hbox.addStretch(9)
        
        self.gridlayout1.addLayout(hbox, row, 1)
        
        row += 1
        
        self.gridlayout1.addWidget(QtGui.QLabel(_("Release date:")), row, 0, QtCore.Qt.AlignLeft)
        
        self.releaseDateEdit = QtGui.QLineEdit(self.tabs)
        self.releaseDateEdit.setInputMask("0000-00-00")
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.releaseDateEdit, 1)
        hbox.addStretch(4)
        
        self.gridlayout1.addLayout(hbox, row, 1)
        
        row += 1
        
        #self.gridlayout1.addWidget(QtGui.QLabel(_(u"Release date:")), row, 0, QtCore.Qt.AlignLeft)
        #self.gridlayout1.addWidget(self.discNumberEdit, row, 1)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(self.gridlayout1)
        vbox.addStretch()
        
        self.basicTags = QtGui.QWidget()
        self.basicTags.setLayout(vbox)
        
        self.tabs.addTab(self.basicTags, _("&Basic"))
        
        self.gridlayout2 = QtGui.QGridLayout()
        self.gridlayout2.setSpacing(2)
        
        details = [
            ["sortnameEdit", _("Artist sortname:")],
            ["albumArtistEdit", _("Album artist:")],
            ["albumArtistSortnameEdit", _("Album artist sortname:")],
            ["composerEdit", _("Composer:")],
            ["conductorEdit", _("Conductor:")],
            ["ensembleEdit", _("Ensemble:")],
            ["lyricistEdit", _("Lyricist:")],
            ["arrangerEdit", _("Arranger:")],
            ["producerEdit", _("Producer:")],
            ["engineerEdit", _("Engineer:")],
            ["remixerEdit", _("Remixer:")],
            ["mixDjEdit", _("Mix DJ:")],
        ]
        i = 0
        for item in details:
            self.gridlayout2.addWidget(QtGui.QLabel(item[1]), i, 0, QtCore.Qt.AlignLeft)
            edit = QtGui.QLineEdit(self.tabs)
            self.gridlayout2.addWidget(edit, i, 1)
            setattr(self, item[0], edit)
            i += 1
        
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(self.gridlayout2)
        vbox.addStretch()
        
        self.detailsTags = QtGui.QWidget()
        self.detailsTags.setLayout(vbox)
        
        self.tabs.addTab(self.detailsTags, _("&Details"))
        self.tabs.addTab(QtGui.QWidget(), _("&MusicBrainz"))
        self.tabs.addTab(QtGui.QWidget(), _("&Album Art"))
        self.tabs.addTab(QtGui.QWidget(), _("&Info"))
        
        self.okButton = QtGui.QPushButton(_("OK"), self)
        self.connect(self.okButton, QtCore.SIGNAL("clicked()"), self.onOk)
        self.cancelButton = QtGui.QPushButton(_("Cancel"), self)
        self.connect(self.cancelButton, QtCore.SIGNAL("clicked()"), self.onCancel)
        
        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton, 0)
        buttonLayout.addWidget(self.cancelButton, 0)
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.tabs)
        mainLayout.addLayout(buttonLayout)
        
        self.setLayout(mainLayout)
        self.resize(QtCore.QSize(500, 350))
        
    def onOk(self):
        self.save()
        self.close()
        
    def onCancel(self):
        self.close()

    def loadField(self, name, edit):
        text = self.metadata.get(name, u"")
        edit.setText(text)
        
    def load(self):
        self.loadField(u"TITLE", self.titleEdit)
        self.loadField(u"ALBUM", self.albumEdit)
        self.loadField(u"ARTIST", self.artistEdit)
        self.loadField(u"ALBUMARTIST", self.albumArtistEdit)
        self.loadField(u"TRACKNUMBER", self.trackNumberEdit)
        self.loadField(u"TOTALTRACKS", self.totalTracksEdit)
        self.loadField(u"DISCNUMBER", self.discNumberEdit)
        self.loadField(u"TOTALDISCS", self.totalDiscsEdit)
        # TODO: DATE
        self.loadField(u"COMPOSER", self.composerEdit)
        self.loadField(u"CONDUCTOR", self.conductorEdit)
        self.loadField(u"ENSEMBLE", self.ensembleEdit)
        self.loadField(u"LYRICIST", self.lyricistEdit)
        self.loadField(u"ARRANGER", self.arrangerEdit)
        self.loadField(u"PRODUCER", self.producerEdit)
        self.loadField(u"ENGINEER", self.engineerEdit)
        self.loadField(u"REMIXER", self.remixerEdit)
        self.loadField(u"MIXDJ", self.mixDjEdit)
        
    def saveField(self, name, edit):    
        text = unicode(edit.text())
        if text or name in self.metadata:
            self.metadata.set(name, text)
    
    def save(self):
        self.saveField(u"TITLE", self.titleEdit)
        self.saveField(u"ALBUM", self.albumEdit)
        self.saveField(u"ARTIST", self.artistEdit)
        self.saveField(u"ALBUMARTIST", self.albumArtistEdit)
        self.saveField(u"TRACKNUMBER", self.trackNumberEdit)
        self.saveField(u"TOTALTRACKS", self.totalTracksEdit)
        self.saveField(u"DISCNUMBER", self.discNumberEdit)
        self.saveField(u"TOTALDISCS", self.totalDiscsEdit)
        # TODO: DATE
        self.saveField(u"COMPOSER", self.composerEdit)
        self.saveField(u"CONDUCTOR", self.conductorEdit)
        self.saveField(u"ENSEMBLE", self.ensembleEdit)
        self.saveField(u"LYRICIST", self.lyricistEdit)
        self.saveField(u"ARRANGER", self.arrangerEdit)
        self.saveField(u"PRODUCER", self.producerEdit)
        self.saveField(u"ENGINEER", self.engineerEdit)
        self.saveField(u"REMIXER", self.remixerEdit)
        self.saveField(u"MIXDJ", self.mixDjEdit)

