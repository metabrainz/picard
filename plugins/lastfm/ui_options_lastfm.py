# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_lastfm.ui'
#
# Created: Sun Jan 28 13:39:17 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_LastfmOptionsPage(object):
    def setupUi(self, LastfmOptionsPage):
        LastfmOptionsPage.setObjectName("LastfmOptionsPage")
        LastfmOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,281,305).size()).expandedTo(LastfmOptionsPage.minimumSizeHint()))

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

        self.use_artist_images = QtGui.QCheckBox(self.rename_files)
        self.use_artist_images.setObjectName("use_artist_images")
        self.vboxlayout1.addWidget(self.use_artist_images)
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

        self.label_4 = QtGui.QLabel(self.rename_files_2)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName("label_4")
        self.hboxlayout.addWidget(self.label_4)

        self.min_tag_usage = QtGui.QSpinBox(self.rename_files_2)
        self.min_tag_usage.setMaximum(100)
        self.min_tag_usage.setObjectName("min_tag_usage")
        self.hboxlayout.addWidget(self.min_tag_usage)
        self.vboxlayout2.addLayout(self.hboxlayout)
        self.vboxlayout.addWidget(self.rename_files_2)

        spacerItem = QtGui.QSpacerItem(121,20,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_4.setBuddy(self.min_tag_usage)

        self.retranslateUi(LastfmOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(LastfmOptionsPage)
        LastfmOptionsPage.setTabOrder(self.use_track_tags,self.ignore_tags)

    def retranslateUi(self, LastfmOptionsPage):
        self.rename_files.setTitle(_(u"Last.fm"))
        self.use_track_tags.setText(_(u"Use track tags"))
        self.use_artist_tags.setText(_(u"Use artist tags"))
        self.use_artist_images.setText(_(u"Use artist images"))
        self.rename_files_2.setTitle(_(u"Tags"))
        self.ignore_tags_2.setText(_(u"Ignore tags:"))
        self.label_4.setText(_(u"Minimal tag usage:"))
        self.min_tag_usage.setSuffix(_(u" %"))

