# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tageditor.ui'
#
# Created: Fri Sep 15 12:54:45 2006
#      by: PyQt4 UI code generator 4.0
#          E:\projects\picard-qt\ui\compile.py
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,464,369).size()).expandedTo(Dialog.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Dialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.tabWidget = QtGui.QTabWidget(Dialog)
        self.tabWidget.setObjectName("tabWidget")

        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.tab)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.gridlayout = QtGui.QGridLayout()
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.discnumber = QtGui.QLineEdit(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.discnumber.sizePolicy().hasHeightForWidth())
        self.discnumber.setSizePolicy(sizePolicy)
        self.discnumber.setMinimumSize(QtCore.QSize(25,0))
        self.discnumber.setObjectName("discnumber")
        self.hboxlayout.addWidget(self.discnumber)

        self.label_6 = QtGui.QLabel(self.tab)
        self.label_6.setObjectName("label_6")
        self.hboxlayout.addWidget(self.label_6)

        self.totaldiscs = QtGui.QLineEdit(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.totaldiscs.sizePolicy().hasHeightForWidth())
        self.totaldiscs.setSizePolicy(sizePolicy)
        self.totaldiscs.setMinimumSize(QtCore.QSize(25,0))
        self.totaldiscs.setObjectName("totaldiscs")
        self.hboxlayout.addWidget(self.totaldiscs)

        spacerItem = QtGui.QSpacerItem(241,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.gridlayout.addLayout(self.hboxlayout,4,1,1,1)

        self.label_2 = QtGui.QLabel(self.tab)
        self.label_2.setObjectName("label_2")
        self.gridlayout.addWidget(self.label_2,1,0,1,1)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.tracknumber = QtGui.QLineEdit(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tracknumber.sizePolicy().hasHeightForWidth())
        self.tracknumber.setSizePolicy(sizePolicy)
        self.tracknumber.setMinimumSize(QtCore.QSize(25,0))
        self.tracknumber.setObjectName("tracknumber")
        self.hboxlayout1.addWidget(self.tracknumber)

        self.label_5 = QtGui.QLabel(self.tab)
        self.label_5.setObjectName("label_5")
        self.hboxlayout1.addWidget(self.label_5)

        self.totaltracks = QtGui.QLineEdit(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.totaltracks.sizePolicy().hasHeightForWidth())
        self.totaltracks.setSizePolicy(sizePolicy)
        self.totaltracks.setMinimumSize(QtCore.QSize(25,0))
        self.totaltracks.setObjectName("totaltracks")
        self.hboxlayout1.addWidget(self.totaltracks)

        spacerItem1 = QtGui.QSpacerItem(241,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem1)
        self.gridlayout.addLayout(self.hboxlayout1,3,1,1,1)

        self.label = QtGui.QLabel(self.tab)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label,0,0,1,1)

        self.artist = QtGui.QLineEdit(self.tab)
        self.artist.setObjectName("artist")
        self.gridlayout.addWidget(self.artist,2,1,1,1)

        self.label_4 = QtGui.QLabel(self.tab)
        self.label_4.setObjectName("label_4")
        self.gridlayout.addWidget(self.label_4,3,0,1,1)

        self.label_8 = QtGui.QLabel(self.tab)
        self.label_8.setObjectName("label_8")
        self.gridlayout.addWidget(self.label_8,5,0,1,1)

        self.label_7 = QtGui.QLabel(self.tab)
        self.label_7.setObjectName("label_7")
        self.gridlayout.addWidget(self.label_7,4,0,1,1)

        self.album = QtGui.QLineEdit(self.tab)
        self.album.setObjectName("album")
        self.gridlayout.addWidget(self.album,1,1,1,1)

        self.title = QtGui.QLineEdit(self.tab)
        self.title.setObjectName("title")
        self.gridlayout.addWidget(self.title,0,1,1,1)

        self.label_3 = QtGui.QLabel(self.tab)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3,2,0,1,1)

        self.hboxlayout2 = QtGui.QHBoxLayout()
        self.hboxlayout2.setMargin(0)
        self.hboxlayout2.setSpacing(6)
        self.hboxlayout2.setObjectName("hboxlayout2")

        self.date = QtGui.QLineEdit(self.tab)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.date.sizePolicy().hasHeightForWidth())
        self.date.setSizePolicy(sizePolicy)
        self.date.setObjectName("date")
        self.hboxlayout2.addWidget(self.date)

        spacerItem2 = QtGui.QSpacerItem(61,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout2.addItem(spacerItem2)
        self.gridlayout.addLayout(self.hboxlayout2,5,1,1,1)
        self.vboxlayout1.addLayout(self.gridlayout)

        spacerItem3 = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout1.addItem(spacerItem3)
        self.tabWidget.addTab(self.tab, "")

        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.tab_4)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.gridlayout1 = QtGui.QGridLayout()
        self.gridlayout1.setMargin(0)
        self.gridlayout1.setSpacing(2)
        self.gridlayout1.setObjectName("gridlayout1")

        self.remixer = QtGui.QLineEdit(self.tab_4)
        self.remixer.setObjectName("remixer")
        self.gridlayout1.addWidget(self.remixer,8,1,1,1)

        self.arranger = QtGui.QLineEdit(self.tab_4)
        self.arranger.setObjectName("arranger")
        self.gridlayout1.addWidget(self.arranger,5,1,1,1)

        self.composer = QtGui.QLineEdit(self.tab_4)
        self.composer.setObjectName("composer")
        self.gridlayout1.addWidget(self.composer,1,1,1,1)

        self.producer = QtGui.QLineEdit(self.tab_4)
        self.producer.setObjectName("producer")
        self.gridlayout1.addWidget(self.producer,6,1,1,1)

        self.conductor = QtGui.QLineEdit(self.tab_4)
        self.conductor.setObjectName("conductor")
        self.gridlayout1.addWidget(self.conductor,2,1,1,1)

        self.label_16 = QtGui.QLabel(self.tab_4)
        self.label_16.setObjectName("label_16")
        self.gridlayout1.addWidget(self.label_16,7,0,1,1)

        self.label_17 = QtGui.QLabel(self.tab_4)
        self.label_17.setObjectName("label_17")
        self.gridlayout1.addWidget(self.label_17,8,0,1,1)

        self.label_11 = QtGui.QLabel(self.tab_4)
        self.label_11.setObjectName("label_11")
        self.gridlayout1.addWidget(self.label_11,2,0,1,1)

        self.label_14 = QtGui.QLabel(self.tab_4)
        self.label_14.setObjectName("label_14")
        self.gridlayout1.addWidget(self.label_14,5,0,1,1)

        self.label_12 = QtGui.QLabel(self.tab_4)
        self.label_12.setObjectName("label_12")
        self.gridlayout1.addWidget(self.label_12,3,0,1,1)

        self.engineer = QtGui.QLineEdit(self.tab_4)
        self.engineer.setObjectName("engineer")
        self.gridlayout1.addWidget(self.engineer,7,1,1,1)

        self.lyricist = QtGui.QLineEdit(self.tab_4)
        self.lyricist.setObjectName("lyricist")
        self.gridlayout1.addWidget(self.lyricist,4,1,1,1)

        self.label_13 = QtGui.QLabel(self.tab_4)
        self.label_13.setObjectName("label_13")
        self.gridlayout1.addWidget(self.label_13,4,0,1,1)

        self.label_15 = QtGui.QLabel(self.tab_4)
        self.label_15.setObjectName("label_15")
        self.gridlayout1.addWidget(self.label_15,6,0,1,1)

        self.label_10 = QtGui.QLabel(self.tab_4)
        self.label_10.setObjectName("label_10")
        self.gridlayout1.addWidget(self.label_10,1,0,1,1)

        self.label_9 = QtGui.QLabel(self.tab_4)
        self.label_9.setObjectName("label_9")
        self.gridlayout1.addWidget(self.label_9,0,0,1,1)

        self.albumartist = QtGui.QLineEdit(self.tab_4)
        self.albumartist.setObjectName("albumartist")
        self.gridlayout1.addWidget(self.albumartist,0,1,1,1)

        self.ensemble = QtGui.QLineEdit(self.tab_4)
        self.ensemble.setObjectName("ensemble")
        self.gridlayout1.addWidget(self.ensemble,3,1,1,1)
        self.vboxlayout2.addLayout(self.gridlayout1)

        spacerItem4 = QtGui.QSpacerItem(20,21,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout2.addItem(spacerItem4)
        self.tabWidget.addTab(self.tab_4, "")

        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.vboxlayout3 = QtGui.QVBoxLayout(self.tab_2)
        self.vboxlayout3.setMargin(9)
        self.vboxlayout3.setSpacing(6)
        self.vboxlayout3.setObjectName("vboxlayout3")

        self.vboxlayout4 = QtGui.QVBoxLayout()
        self.vboxlayout4.setMargin(0)
        self.vboxlayout4.setSpacing(6)
        self.vboxlayout4.setObjectName("vboxlayout4")

        self.listView = QtGui.QListView(self.tab_2)
        self.listView.setObjectName("listView")
        self.vboxlayout4.addWidget(self.listView)

        self.hboxlayout3 = QtGui.QHBoxLayout()
        self.hboxlayout3.setMargin(0)
        self.hboxlayout3.setSpacing(6)
        self.hboxlayout3.setObjectName("hboxlayout3")

        self.pushButton = QtGui.QPushButton(self.tab_2)
        self.pushButton.setObjectName("pushButton")
        self.hboxlayout3.addWidget(self.pushButton)

        self.pushButton_2 = QtGui.QPushButton(self.tab_2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.hboxlayout3.addWidget(self.pushButton_2)

        spacerItem5 = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout3.addItem(spacerItem5)
        self.vboxlayout4.addLayout(self.hboxlayout3)
        self.vboxlayout3.addLayout(self.vboxlayout4)
        self.tabWidget.addTab(self.tab_2, "")
        self.vboxlayout.addWidget(self.tabWidget)

        self.hboxlayout4 = QtGui.QHBoxLayout()
        self.hboxlayout4.setMargin(0)
        self.hboxlayout4.setSpacing(6)
        self.hboxlayout4.setObjectName("hboxlayout4")

        spacerItem6 = QtGui.QSpacerItem(131,31,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout4.addItem(spacerItem6)

        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setObjectName("okButton")
        self.hboxlayout4.addWidget(self.okButton)

        self.cancelButton = QtGui.QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")
        self.hboxlayout4.addWidget(self.cancelButton)
        self.vboxlayout.addLayout(self.hboxlayout4)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QObject.connect(self.okButton,QtCore.SIGNAL("clicked()"),Dialog.accept)
        QtCore.QObject.connect(self.cancelButton,QtCore.SIGNAL("clicked()"),Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_("Tag Editor"))
        self.discnumber.setInputMask(_("000; "))
        self.label_6.setText(_("of"))
        self.totaldiscs.setInputMask(_("000; "))
        self.label_2.setText(_("Album:"))
        self.tracknumber.setInputMask(_("000; "))
        self.label_5.setText(_("of"))
        self.totaltracks.setInputMask(_("000; "))
        self.label.setText(_("Title:"))
        self.label_4.setText(_("Track:"))
        self.label_8.setText(_("Date:"))
        self.label_7.setText(_("Disc:"))
        self.label_3.setText(_("Artist:"))
        self.date.setInputMask(_("0000-00-00; "))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _("&Basic"))
        self.label_16.setText(_("Engineer:"))
        self.label_17.setText(_("Remixer:"))
        self.label_11.setText(_("Conductor:"))
        self.label_14.setText(_("Arranger:"))
        self.label_12.setText(_("Ensemble:"))
        self.label_13.setText(_("Lyricist:"))
        self.label_15.setText(_("Producer:"))
        self.label_10.setText(_("Composer:"))
        self.label_9.setText(_("Album artist:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _("&Advanced"))
        self.pushButton.setText(_("&Add..."))
        self.pushButton_2.setText(_("Delete"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _("A&rtwork"))
        self.okButton.setText(_("OK"))
        self.cancelButton.setText(_("Cancel"))
