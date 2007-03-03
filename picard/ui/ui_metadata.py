# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/metadata.ui'
#
# Created: Sat Mar  3 19:09:31 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,331,117).size()).expandedTo(Form.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Form)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.gridlayout = QtGui.QGridLayout()
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        self.title = QtGui.QLineEdit(Form)
        self.title.setObjectName("title")
        self.gridlayout.addWidget(self.title,0,1,1,6)

        self.lookup = QtGui.QPushButton(Form)
        self.lookup.setObjectName("lookup")
        self.gridlayout.addWidget(self.lookup,3,6,1,1)

        self.artist = QtGui.QLineEdit(Form)
        self.artist.setObjectName("artist")
        self.gridlayout.addWidget(self.artist,1,1,1,6)

        self.length = QtGui.QLineEdit(Form)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.length.sizePolicy().hasHeightForWidth())
        self.length.setSizePolicy(sizePolicy)
        self.length.setMinimumSize(QtCore.QSize(35,0))
        self.length.setReadOnly(True)
        self.length.setObjectName("length")
        self.gridlayout.addWidget(self.length,3,3,1,1)

        self.label = QtGui.QLabel(Form)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label,0,0,1,1)

        self.label_6 = QtGui.QLabel(Form)
        self.label_6.setObjectName("label_6")
        self.gridlayout.addWidget(self.label_6,3,4,1,1)

        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.gridlayout.addWidget(self.label_2,1,0,1,1)

        self.album = QtGui.QLineEdit(Form)
        self.album.setObjectName("album")
        self.gridlayout.addWidget(self.album,2,1,1,6)

        self.tracknumber = QtGui.QLineEdit(Form)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tracknumber.sizePolicy().hasHeightForWidth())
        self.tracknumber.setSizePolicy(sizePolicy)
        self.tracknumber.setMinimumSize(QtCore.QSize(25,0))
        self.tracknumber.setObjectName("tracknumber")
        self.gridlayout.addWidget(self.tracknumber,3,1,1,1)

        self.label_4 = QtGui.QLabel(Form)
        self.label_4.setObjectName("label_4")
        self.gridlayout.addWidget(self.label_4,3,0,1,1)

        self.date = QtGui.QLineEdit(Form)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(5)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.date.sizePolicy().hasHeightForWidth())
        self.date.setSizePolicy(sizePolicy)
        self.date.setMinimumSize(QtCore.QSize(65,0))
        self.date.setObjectName("date")
        self.gridlayout.addWidget(self.date,3,5,1,1)

        self.label_5 = QtGui.QLabel(Form)
        self.label_5.setObjectName("label_5")
        self.gridlayout.addWidget(self.label_5,3,2,1,1)

        self.label_3 = QtGui.QLabel(Form)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3,2,0,1,1)
        self.vboxlayout.addLayout(self.gridlayout)

        spacerItem = QtGui.QSpacerItem(20,0,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label.setBuddy(self.title)
        self.label_6.setBuddy(self.date)
        self.label_2.setBuddy(self.artist)
        self.label_4.setBuddy(self.tracknumber)
        self.label_5.setBuddy(self.length)
        self.label_3.setBuddy(self.album)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.title,self.artist)
        Form.setTabOrder(self.artist,self.album)
        Form.setTabOrder(self.album,self.tracknumber)
        Form.setTabOrder(self.tracknumber,self.length)
        Form.setTabOrder(self.length,self.date)
        Form.setTabOrder(self.date,self.lookup)

    def retranslateUi(self, Form):
        self.lookup.setText(_(u"Lookup"))
        self.label.setText(_(u"Title:"))
        self.label_6.setText(_(u"Date:"))
        self.label_2.setText(_(u"Artist:"))
        self.label_4.setText(_(u"Track:"))
        self.date.setInputMask(_(u"0000-00-00; "))
        self.label_5.setText(_(u"Length:"))
        self.label_3.setText(_(u"Album:"))

