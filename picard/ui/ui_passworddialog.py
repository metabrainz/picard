# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/passworddialog.ui'
#
# Created: Mon Jun 23 03:16:18 2008
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_PasswordDialog(object):
    def setupUi(self, PasswordDialog):
        PasswordDialog.setObjectName("PasswordDialog")
        PasswordDialog.setWindowModality(QtCore.Qt.WindowModal)
        PasswordDialog.resize(QtCore.QSize(QtCore.QRect(0,0,378,246).size()).expandedTo(PasswordDialog.minimumSizeHint()))

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PasswordDialog.sizePolicy().hasHeightForWidth())
        PasswordDialog.setSizePolicy(sizePolicy)

        self.vboxlayout = QtGui.QVBoxLayout(PasswordDialog)
        self.vboxlayout.setObjectName("vboxlayout")

        self.info_text = QtGui.QLabel(PasswordDialog)
        self.info_text.setWordWrap(True)
        self.info_text.setObjectName("info_text")
        self.vboxlayout.addWidget(self.info_text)

        spacerItem = QtGui.QSpacerItem(20,60,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.label = QtGui.QLabel(PasswordDialog)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)

        self.username = QtGui.QLineEdit(PasswordDialog)
        self.username.setWindowModality(QtCore.Qt.NonModal)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.username.sizePolicy().hasHeightForWidth())
        self.username.setSizePolicy(sizePolicy)
        self.username.setObjectName("username")
        self.vboxlayout.addWidget(self.username)

        self.label_2 = QtGui.QLabel(PasswordDialog)
        self.label_2.setObjectName("label_2")
        self.vboxlayout.addWidget(self.label_2)

        self.password = QtGui.QLineEdit(PasswordDialog)
        self.password.setEchoMode(QtGui.QLineEdit.Password)
        self.password.setObjectName("password")
        self.vboxlayout.addWidget(self.password)

        self.save_authentication = QtGui.QCheckBox(PasswordDialog)
        self.save_authentication.setChecked(True)
        self.save_authentication.setObjectName("save_authentication")
        self.vboxlayout.addWidget(self.save_authentication)

        spacerItem1 = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)

        self.buttonbox = QtGui.QDialogButtonBox(PasswordDialog)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonbox.setObjectName("buttonbox")
        self.vboxlayout.addWidget(self.buttonbox)

        self.retranslateUi(PasswordDialog)
        QtCore.QObject.connect(self.buttonbox,QtCore.SIGNAL("rejected()"),PasswordDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PasswordDialog)

    def retranslateUi(self, PasswordDialog):
        PasswordDialog.setWindowTitle(_("Authentication required"))
        self.label.setText(_("Username:"))
        self.label_2.setText(_("Password:"))
        self.save_authentication.setText(_("Save username and password"))

