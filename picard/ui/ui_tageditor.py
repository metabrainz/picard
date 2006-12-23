# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/tageditor.ui'
#
# Created: Sat Dec 23 15:19:19 2006
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,455,355).size()).expandedTo(Dialog.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Dialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.tabWidget = QtGui.QTabWidget(Dialog)
        self.tabWidget.setObjectName("tabWidget")

        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")

        self.gridlayout = QtGui.QGridLayout(self.tab)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        spacerItem = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem,7,0,1,2)

        self.label_7 = QtGui.QLabel(self.tab)
        self.label_7.setObjectName("label_7")
        self.gridlayout.addWidget(self.label_7,5,0,1,1)

        self.label_4 = QtGui.QLabel(self.tab)
        self.label_4.setObjectName("label_4")
        self.gridlayout.addWidget(self.label_4,4,0,1,1)

        self.albumartist = QtGui.QLineEdit(self.tab)
        self.albumartist.setObjectName("albumartist")
        self.gridlayout.addWidget(self.albumartist,3,1,1,1)

        self.label_2 = QtGui.QLabel(self.tab)
        self.label_2.setObjectName("label_2")
        self.gridlayout.addWidget(self.label_2,3,0,1,1)

        self.label_3 = QtGui.QLabel(self.tab)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3,1,0,1,1)

        self.title = QtGui.QLineEdit(self.tab)
        self.title.setObjectName("title")
        self.gridlayout.addWidget(self.title,0,1,1,1)

        self.artist = QtGui.QLineEdit(self.tab)
        self.artist.setObjectName("artist")
        self.gridlayout.addWidget(self.artist,1,1,1,1)

        self.album = QtGui.QLineEdit(self.tab)
        self.album.setObjectName("album")
        self.gridlayout.addWidget(self.album,2,1,1,1)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(2)
        self.hboxlayout.setObjectName("hboxlayout")

        self.tracknumber = QtGui.QLineEdit(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tracknumber.sizePolicy().hasHeightForWidth())
        self.tracknumber.setSizePolicy(sizePolicy)
        self.tracknumber.setMaximumSize(QtCore.QSize(40,16777215))
        self.tracknumber.setObjectName("tracknumber")
        self.hboxlayout.addWidget(self.tracknumber)

        self.label_5 = QtGui.QLabel(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName("label_5")
        self.hboxlayout.addWidget(self.label_5)

        self.totaltracks = QtGui.QLineEdit(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.totaltracks.sizePolicy().hasHeightForWidth())
        self.totaltracks.setSizePolicy(sizePolicy)
        self.totaltracks.setMaximumSize(QtCore.QSize(40,16777215))
        self.totaltracks.setObjectName("totaltracks")
        self.hboxlayout.addWidget(self.totaltracks)

        spacerItem1 = QtGui.QSpacerItem(241,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem1)
        self.gridlayout.addLayout(self.hboxlayout,4,1,1,1)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(2)
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.discnumber = QtGui.QLineEdit(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.discnumber.sizePolicy().hasHeightForWidth())
        self.discnumber.setSizePolicy(sizePolicy)
        self.discnumber.setMaximumSize(QtCore.QSize(40,16777215))
        self.discnumber.setBaseSize(QtCore.QSize(50,0))
        self.discnumber.setObjectName("discnumber")
        self.hboxlayout1.addWidget(self.discnumber)

        self.label_6 = QtGui.QLabel(self.tab)
        self.label_6.setObjectName("label_6")
        self.hboxlayout1.addWidget(self.label_6)

        self.totaldiscs = QtGui.QLineEdit(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.totaldiscs.sizePolicy().hasHeightForWidth())
        self.totaldiscs.setSizePolicy(sizePolicy)
        self.totaldiscs.setMaximumSize(QtCore.QSize(40,16777215))
        self.totaldiscs.setBaseSize(QtCore.QSize(50,0))
        self.totaldiscs.setObjectName("totaldiscs")
        self.hboxlayout1.addWidget(self.totaldiscs)

        spacerItem2 = QtGui.QSpacerItem(241,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem2)
        self.gridlayout.addLayout(self.hboxlayout1,5,1,1,1)

        self.hboxlayout2 = QtGui.QHBoxLayout()
        self.hboxlayout2.setMargin(0)
        self.hboxlayout2.setSpacing(2)
        self.hboxlayout2.setObjectName("hboxlayout2")

        self.date = QtGui.QLineEdit(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.date.sizePolicy().hasHeightForWidth())
        self.date.setSizePolicy(sizePolicy)
        self.date.setMaximumSize(QtCore.QSize(80,16777215))
        self.date.setObjectName("date")
        self.hboxlayout2.addWidget(self.date)

        spacerItem3 = QtGui.QSpacerItem(61,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout2.addItem(spacerItem3)
        self.gridlayout.addLayout(self.hboxlayout2,6,1,1,1)

        self.label_9 = QtGui.QLabel(self.tab)
        self.label_9.setObjectName("label_9")
        self.gridlayout.addWidget(self.label_9,2,0,1,1)

        self.label_8 = QtGui.QLabel(self.tab)
        self.label_8.setObjectName("label_8")
        self.gridlayout.addWidget(self.label_8,6,0,1,1)

        self.label = QtGui.QLabel(self.tab)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label,0,0,1,1)
        self.tabWidget.addTab(self.tab,"")

        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.tab_4)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.tags = QtGui.QTreeWidget(self.tab_4)
        self.tags.setRootIsDecorated(False)
        self.tags.setObjectName("tags")
        self.vboxlayout1.addWidget(self.tags)

        self.hboxlayout3 = QtGui.QHBoxLayout()
        self.hboxlayout3.setMargin(0)
        self.hboxlayout3.setSpacing(6)
        self.hboxlayout3.setObjectName("hboxlayout3")

        self.tags_add = QtGui.QPushButton(self.tab_4)
        self.tags_add.setObjectName("tags_add")
        self.hboxlayout3.addWidget(self.tags_add)

        self.tags_delete = QtGui.QPushButton(self.tab_4)
        self.tags_delete.setObjectName("tags_delete")
        self.hboxlayout3.addWidget(self.tags_delete)

        spacerItem4 = QtGui.QSpacerItem(151,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout3.addItem(spacerItem4)
        self.vboxlayout1.addLayout(self.hboxlayout3)
        self.tabWidget.addTab(self.tab_4,"")

        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.tab_2)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.artwork_list = QtGui.QListWidget(self.tab_2)
        self.artwork_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.artwork_list.setIconSize(QtCore.QSize(170,170))
        self.artwork_list.setMovement(QtGui.QListView.Static)
        self.artwork_list.setFlow(QtGui.QListView.LeftToRight)
        self.artwork_list.setWrapping(False)
        self.artwork_list.setResizeMode(QtGui.QListView.Fixed)
        self.artwork_list.setSpacing(10)
        self.artwork_list.setViewMode(QtGui.QListView.IconMode)
        self.artwork_list.setObjectName("artwork_list")
        self.vboxlayout2.addWidget(self.artwork_list)

        self.hboxlayout4 = QtGui.QHBoxLayout()
        self.hboxlayout4.setMargin(0)
        self.hboxlayout4.setSpacing(6)
        self.hboxlayout4.setObjectName("hboxlayout4")

        self.artwork_add = QtGui.QPushButton(self.tab_2)
        self.artwork_add.setObjectName("artwork_add")
        self.hboxlayout4.addWidget(self.artwork_add)

        self.artwork_delete = QtGui.QPushButton(self.tab_2)
        self.artwork_delete.setObjectName("artwork_delete")
        self.hboxlayout4.addWidget(self.artwork_delete)

        spacerItem5 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout4.addItem(spacerItem5)
        self.vboxlayout2.addLayout(self.hboxlayout4)
        self.tabWidget.addTab(self.tab_2,"")

        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")

        self.vboxlayout3 = QtGui.QVBoxLayout(self.tab_3)
        self.vboxlayout3.setMargin(9)
        self.vboxlayout3.setSpacing(6)
        self.vboxlayout3.setObjectName("vboxlayout3")

        self.gridlayout1 = QtGui.QGridLayout()
        self.gridlayout1.setMargin(0)
        self.gridlayout1.setSpacing(2)
        self.gridlayout1.setObjectName("gridlayout1")

        self.musicip_puid = QtGui.QLineEdit(self.tab_3)
        self.musicip_puid.setReadOnly(True)
        self.musicip_puid.setObjectName("musicip_puid")
        self.gridlayout1.addWidget(self.musicip_puid,4,1,1,1)

        self.musicbrainz_albumartistid = QtGui.QLineEdit(self.tab_3)
        self.musicbrainz_albumartistid.setReadOnly(True)
        self.musicbrainz_albumartistid.setObjectName("musicbrainz_albumartistid")
        self.gridlayout1.addWidget(self.musicbrainz_albumartistid,3,1,1,1)

        self.label_20 = QtGui.QLabel(self.tab_3)
        self.label_20.setObjectName("label_20")
        self.gridlayout1.addWidget(self.label_20,2,0,1,1)

        self.musicbrainz_albumid = QtGui.QLineEdit(self.tab_3)
        self.musicbrainz_albumid.setReadOnly(True)
        self.musicbrainz_albumid.setObjectName("musicbrainz_albumid")
        self.gridlayout1.addWidget(self.musicbrainz_albumid,1,1,1,1)

        self.label_22 = QtGui.QLabel(self.tab_3)
        self.label_22.setObjectName("label_22")
        self.gridlayout1.addWidget(self.label_22,4,0,1,1)

        self.label_21 = QtGui.QLabel(self.tab_3)
        self.label_21.setObjectName("label_21")
        self.gridlayout1.addWidget(self.label_21,3,0,1,1)

        self.musicbrainz_artistid = QtGui.QLineEdit(self.tab_3)
        self.musicbrainz_artistid.setReadOnly(True)
        self.musicbrainz_artistid.setObjectName("musicbrainz_artistid")
        self.gridlayout1.addWidget(self.musicbrainz_artistid,2,1,1,1)

        self.label_19 = QtGui.QLabel(self.tab_3)
        self.label_19.setObjectName("label_19")
        self.gridlayout1.addWidget(self.label_19,1,0,1,1)

        self.label_18 = QtGui.QLabel(self.tab_3)
        self.label_18.setObjectName("label_18")
        self.gridlayout1.addWidget(self.label_18,0,0,1,1)

        self.musicbrainz_trackid = QtGui.QLineEdit(self.tab_3)
        self.musicbrainz_trackid.setReadOnly(True)
        self.musicbrainz_trackid.setObjectName("musicbrainz_trackid")
        self.gridlayout1.addWidget(self.musicbrainz_trackid,0,1,1,1)
        self.vboxlayout3.addLayout(self.gridlayout1)

        spacerItem6 = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout3.addItem(spacerItem6)
        self.tabWidget.addTab(self.tab_3,"")

        self.tab_5 = QtGui.QWidget()
        self.tab_5.setObjectName("tab_5")

        self.vboxlayout4 = QtGui.QVBoxLayout(self.tab_5)
        self.vboxlayout4.setMargin(9)
        self.vboxlayout4.setSpacing(6)
        self.vboxlayout4.setObjectName("vboxlayout4")

        self.info = QtGui.QLabel(self.tab_5)
        self.info.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.info.setWordWrap(True)
        self.info.setObjectName("info")
        self.vboxlayout4.addWidget(self.info)
        self.tabWidget.addTab(self.tab_5,"")
        self.vboxlayout.addWidget(self.tabWidget)

        self.hboxlayout5 = QtGui.QHBoxLayout()
        self.hboxlayout5.setMargin(0)
        self.hboxlayout5.setSpacing(6)
        self.hboxlayout5.setObjectName("hboxlayout5")

        spacerItem7 = QtGui.QSpacerItem(131,31,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout5.addItem(spacerItem7)

        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setDefault(True)
        self.okButton.setObjectName("okButton")
        self.hboxlayout5.addWidget(self.okButton)

        self.cancelButton = QtGui.QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")
        self.hboxlayout5.addWidget(self.cancelButton)
        self.vboxlayout.addLayout(self.hboxlayout5)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.okButton,QtCore.SIGNAL("clicked()"),Dialog.accept)
        QtCore.QObject.connect(self.cancelButton,QtCore.SIGNAL("clicked()"),Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.title,self.artist)
        Dialog.setTabOrder(self.artist,self.album)
        Dialog.setTabOrder(self.album,self.albumartist)
        Dialog.setTabOrder(self.albumartist,self.tracknumber)
        Dialog.setTabOrder(self.tracknumber,self.totaltracks)
        Dialog.setTabOrder(self.totaltracks,self.discnumber)
        Dialog.setTabOrder(self.discnumber,self.totaldiscs)
        Dialog.setTabOrder(self.totaldiscs,self.date)
        Dialog.setTabOrder(self.date,self.tags)
        Dialog.setTabOrder(self.tags,self.tags_add)
        Dialog.setTabOrder(self.tags_add,self.tags_delete)
        Dialog.setTabOrder(self.tags_delete,self.musicbrainz_trackid)
        Dialog.setTabOrder(self.musicbrainz_trackid,self.musicbrainz_albumid)
        Dialog.setTabOrder(self.musicbrainz_albumid,self.musicbrainz_artistid)
        Dialog.setTabOrder(self.musicbrainz_artistid,self.musicbrainz_albumartistid)
        Dialog.setTabOrder(self.musicbrainz_albumartistid,self.musicip_puid)
        Dialog.setTabOrder(self.musicip_puid,self.cancelButton)
        Dialog.setTabOrder(self.cancelButton,self.tabWidget)
        Dialog.setTabOrder(self.tabWidget,self.artwork_delete)
        Dialog.setTabOrder(self.artwork_delete,self.artwork_add)
        Dialog.setTabOrder(self.artwork_add,self.artwork_list)
        Dialog.setTabOrder(self.artwork_list,self.okButton)

    def retranslateUi(self, Dialog):
        self.label_7.setText(_(u"Disc:"))
        self.label_4.setText(_(u"Track:"))
        self.label_2.setText(_(u"Album artist:"))
        self.label_3.setText(_(u"Artist:"))
        self.tracknumber.setInputMask(_(u"000; "))
        self.label_5.setText(_(u"of"))
        self.totaltracks.setInputMask(_(u"000; "))
        self.discnumber.setInputMask(_(u"000; "))
        self.label_6.setText(_(u"of"))
        self.totaldiscs.setInputMask(_(u"000; "))
        self.date.setInputMask(_(u"0000-00-00; "))
        self.label_9.setText(_(u"Album:"))
        self.label_8.setText(_(u"Date:"))
        self.label.setText(_(u"Title:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _(u"&Basic"))
        self.tags_add.setText(_(u"&Add..."))
        self.tags_delete.setText(_(u"Delete"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _(u"&Advanced"))
        self.artwork_add.setText(_(u"&Add..."))
        self.artwork_delete.setText(_(u"Delete"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _(u"A&rtwork"))
        self.label_20.setText(_(u"Artist ID:"))
        self.label_22.setText(_(u"PUID:"))
        self.label_21.setText(_(u"Release artist ID:"))
        self.label_19.setText(_(u"Release ID:"))
        self.label_18.setText(_(u"Track ID:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _(u"&MusicBrainz"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), _(u"&Info"))
        self.okButton.setText(_(u"OK"))
        self.cancelButton.setText(_(u"Cancel"))

