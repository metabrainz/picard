# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_general.ui'
#
# Created: Sat Mar  3 19:09:31 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_GeneralOptionsPage(object):
    def setupUi(self, GeneralOptionsPage):
        GeneralOptionsPage.setObjectName("GeneralOptionsPage")
        GeneralOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,232,275).size()).expandedTo(GeneralOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(GeneralOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.groupBox = QtGui.QGroupBox(GeneralOptionsPage)
        self.groupBox.setObjectName("groupBox")

        self.gridlayout = QtGui.QGridLayout(self.groupBox)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        self.server_host = QtGui.QComboBox(self.groupBox)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.server_host.sizePolicy().hasHeightForWidth())
        self.server_host.setSizePolicy(sizePolicy)
        self.server_host.setEditable(True)
        self.server_host.setObjectName("server_host")
        self.gridlayout.addWidget(self.server_host,1,0,1,1)

        self.label_7 = QtGui.QLabel(self.groupBox)
        self.label_7.setObjectName("label_7")
        self.gridlayout.addWidget(self.label_7,0,1,1,1)

        self.server_port = QtGui.QSpinBox(self.groupBox)
        self.server_port.setMaximum(65535)
        self.server_port.setMinimum(1)
        self.server_port.setProperty("value",QtCore.QVariant(80))
        self.server_port.setObjectName("server_port")
        self.gridlayout.addWidget(self.server_port,1,1,1,1)

        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label,0,0,1,1)
        self.vboxlayout.addWidget(self.groupBox)

        self.rename_files_2 = QtGui.QGroupBox(GeneralOptionsPage)
        self.rename_files_2.setObjectName("rename_files_2")

        self.gridlayout1 = QtGui.QGridLayout(self.rename_files_2)
        self.gridlayout1.setMargin(9)
        self.gridlayout1.setSpacing(2)
        self.gridlayout1.setObjectName("gridlayout1")

        self.username = QtGui.QLineEdit(self.rename_files_2)
        self.username.setObjectName("username")
        self.gridlayout1.addWidget(self.username,1,0,1,1)

        self.label_5 = QtGui.QLabel(self.rename_files_2)
        self.label_5.setObjectName("label_5")
        self.gridlayout1.addWidget(self.label_5,2,0,1,1)

        self.password = QtGui.QLineEdit(self.rename_files_2)
        self.password.setEchoMode(QtGui.QLineEdit.Password)
        self.password.setObjectName("password")
        self.gridlayout1.addWidget(self.password,3,0,1,1)

        self.label_6 = QtGui.QLabel(self.rename_files_2)
        self.label_6.setObjectName("label_6")
        self.gridlayout1.addWidget(self.label_6,0,0,1,1)
        self.vboxlayout.addWidget(self.rename_files_2)

        spacerItem = QtGui.QSpacerItem(201,92,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_5.setBuddy(self.password)
        self.label_6.setBuddy(self.username)

        self.retranslateUi(GeneralOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(GeneralOptionsPage)
        GeneralOptionsPage.setTabOrder(self.server_host,self.server_port)
        GeneralOptionsPage.setTabOrder(self.server_port,self.username)
        GeneralOptionsPage.setTabOrder(self.username,self.password)

    def retranslateUi(self, GeneralOptionsPage):
        self.groupBox.setTitle(_(u"MusicBrainz Server"))
        self.label_7.setText(_(u"Port:"))
        self.label.setText(_(u"Server address:"))
        self.rename_files_2.setTitle(_(u"Account Information"))
        self.label_5.setText(_(u"Password:"))
        self.label_6.setText(_(u"Username:"))

