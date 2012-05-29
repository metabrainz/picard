# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/passworddialog.ui'
#
# Created: Tue May 29 19:44:14 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_PasswordDialog(object):
    def setupUi(self, PasswordDialog):
        PasswordDialog.setObjectName(_fromUtf8("PasswordDialog"))
        PasswordDialog.setWindowModality(QtCore.Qt.WindowModal)
        PasswordDialog.resize(378, 246)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PasswordDialog.sizePolicy().hasHeightForWidth())
        PasswordDialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(PasswordDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.info_text = QtGui.QLabel(PasswordDialog)
        self.info_text.setText(_fromUtf8(""))
        self.info_text.setWordWrap(True)
        self.info_text.setObjectName(_fromUtf8("info_text"))
        self.verticalLayout.addWidget(self.info_text)
        spacerItem = QtGui.QSpacerItem(20, 60, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.label = QtGui.QLabel(PasswordDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.username = QtGui.QLineEdit(PasswordDialog)
        self.username.setWindowModality(QtCore.Qt.NonModal)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.username.sizePolicy().hasHeightForWidth())
        self.username.setSizePolicy(sizePolicy)
        self.username.setObjectName(_fromUtf8("username"))
        self.verticalLayout.addWidget(self.username)
        self.label_2 = QtGui.QLabel(PasswordDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.password = QtGui.QLineEdit(PasswordDialog)
        self.password.setEchoMode(QtGui.QLineEdit.Password)
        self.password.setObjectName(_fromUtf8("password"))
        self.verticalLayout.addWidget(self.password)
        self.save_authentication = QtGui.QCheckBox(PasswordDialog)
        self.save_authentication.setChecked(True)
        self.save_authentication.setObjectName(_fromUtf8("save_authentication"))
        self.verticalLayout.addWidget(self.save_authentication)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.buttonbox = QtGui.QDialogButtonBox(PasswordDialog)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonbox.setObjectName(_fromUtf8("buttonbox"))
        self.verticalLayout.addWidget(self.buttonbox)

        self.retranslateUi(PasswordDialog)
        QtCore.QObject.connect(self.buttonbox, QtCore.SIGNAL(_fromUtf8("rejected()")), PasswordDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PasswordDialog)

    def retranslateUi(self, PasswordDialog):
        PasswordDialog.setWindowTitle(_("Authentication required"))
        self.label.setText(_("Username:"))
        self.label_2.setText(_("Password:"))
        self.save_authentication.setText(_("Save username and password"))

