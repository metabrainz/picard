# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_general.ui'
#
# Created: Thu Sep 14 21:17:34 2006
#      by: PyQt4 UI code generator 4.0
#          E:\projects\picard-qt\ui\compile.py
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,400,300).size()).expandedTo(Form.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Form)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.groupBox = QtGui.QGroupBox(Form)
        self.groupBox.setObjectName("groupBox")

        self.gridlayout = QtGui.QGridLayout(self.groupBox)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        self.server_host = QtGui.QLineEdit(self.groupBox)
        self.server_host.setObjectName("server_host")
        self.gridlayout.addWidget(self.server_host,1,0,1,1)

        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label,0,0,1,1)

        self.server_port = QtGui.QSpinBox(self.groupBox)
        self.server_port.setMaximum(65535)
        self.server_port.setMinimum(1)
        self.server_port.setProperty("value",QtCore.QVariant(80))
        self.server_port.setObjectName("server_port")
        self.gridlayout.addWidget(self.server_port,1,1,1,1)

        self.label_7 = QtGui.QLabel(self.groupBox)
        self.label_7.setObjectName("label_7")
        self.gridlayout.addWidget(self.label_7,0,1,1,1)
        self.vboxlayout.addWidget(self.groupBox)

        self.rename_files_2 = QtGui.QGroupBox(Form)
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

        spacerItem = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label.setBuddy(self.server_host)
        self.label_5.setBuddy(self.password)
        self.label_6.setBuddy(self.username)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.server_host,self.server_port)
        Form.setTabOrder(self.server_port,self.username)
        Form.setTabOrder(self.username,self.password)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_("Form"))
        self.groupBox.setTitle(_("MusicBrainz Server"))
        self.label.setText(_("Server address:"))
        self.label_7.setText(_("Port:"))
        self.rename_files_2.setTitle(_("Account Information"))
        self.label_5.setText(_("Password:"))
        self.label_6.setText(_("Username:"))
