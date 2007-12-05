# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_lastfm.ui'
#
# Created: Sun May 13 11:18:12 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_LastfmOptionsPage(object):
    def setupUi(self, LastfmOptionsPage):
        LastfmOptionsPage.setObjectName("LastfmOptionsPage")
        LastfmOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,305,317).size()).expandedTo(LastfmOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(LastfmOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.rename_files = QtGui.QGroupBox(LastfmOptionsPage)
        self.rename_files.setObjectName("rename_files")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.rename_files)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.use_track_tags = QtGui.QCheckBox(self.rename_files)
        self.use_track_tags.setObjectName("use_track_tags")
        self.vboxlayout1.addWidget(self.use_track_tags)

        self.use_artist_tags = QtGui.QCheckBox(self.rename_files)
        self.use_artist_tags.setObjectName("use_artist_tags")
        self.vboxlayout1.addWidget(self.use_artist_tags)
        self.vboxlayout.addWidget(self.rename_files)

        self.rename_files_2 = QtGui.QGroupBox(LastfmOptionsPage)
        self.rename_files_2.setObjectName("rename_files_2")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.rename_files_2)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(2)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.ignore_tags_2 = QtGui.QLabel(self.rename_files_2)
        self.ignore_tags_2.setObjectName("ignore_tags_2")
        self.vboxlayout2.addWidget(self.ignore_tags_2)

        self.ignore_tags = QtGui.QLineEdit(self.rename_files_2)
        self.ignore_tags.setObjectName("ignore_tags")
        self.vboxlayout2.addWidget(self.ignore_tags)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.ignore_tags_4 = QtGui.QLabel(self.rename_files_2)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(5),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(4)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ignore_tags_4.sizePolicy().hasHeightForWidth())
        self.ignore_tags_4.setSizePolicy(sizePolicy)
        self.ignore_tags_4.setObjectName("ignore_tags_4")
        self.hboxlayout.addWidget(self.ignore_tags_4)

        self.join_tags = QtGui.QComboBox(self.rename_files_2)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(5),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.join_tags.sizePolicy().hasHeightForWidth())
        self.join_tags.setSizePolicy(sizePolicy)
        self.join_tags.setEditable(True)
        self.join_tags.setObjectName("join_tags")
        self.join_tags.addItem("")
        self.hboxlayout.addWidget(self.join_tags)
        self.vboxlayout2.addLayout(self.hboxlayout)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.label_4 = QtGui.QLabel(self.rename_files_2)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName("label_4")
        self.hboxlayout1.addWidget(self.label_4)

        self.min_tag_usage = QtGui.QSpinBox(self.rename_files_2)
        self.min_tag_usage.setMaximum(100)
        self.min_tag_usage.setObjectName("min_tag_usage")
        self.hboxlayout1.addWidget(self.min_tag_usage)
        self.vboxlayout2.addLayout(self.hboxlayout1)
        self.vboxlayout.addWidget(self.rename_files_2)

        spacerItem = QtGui.QSpacerItem(263,21,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_4.setBuddy(self.min_tag_usage)

        self.retranslateUi(LastfmOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(LastfmOptionsPage)
        LastfmOptionsPage.setTabOrder(self.use_track_tags,self.ignore_tags)

    def retranslateUi(self, LastfmOptionsPage):
        self.rename_files.setTitle(_("Last.fm"))
        self.use_track_tags.setText(_("Use track tags"))
        self.use_artist_tags.setText(_("Use artist tags"))
        self.rename_files_2.setTitle(_("Tags"))
        self.ignore_tags_2.setText(_("Ignore tags:"))
        self.ignore_tags_4.setText(_("Join multiple tags with:"))
        self.join_tags.addItem(_(" / "))
        self.join_tags.addItem(_(", "))
        self.label_4.setText(_("Minimal tag usage:"))
        self.min_tag_usage.setSuffix(_(" %"))

