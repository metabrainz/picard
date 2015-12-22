# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PasswordDialog(object):
    def setupUi(self, PasswordDialog):
        PasswordDialog.setObjectName("PasswordDialog")
        PasswordDialog.setWindowModality(QtCore.Qt.WindowModal)
        PasswordDialog.resize(378, 246)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PasswordDialog.sizePolicy().hasHeightForWidth())
        PasswordDialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(PasswordDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.info_text = QtWidgets.QLabel(PasswordDialog)
        self.info_text.setText("")
        self.info_text.setWordWrap(True)
        self.info_text.setObjectName("info_text")
        self.verticalLayout.addWidget(self.info_text)
        spacerItem = QtWidgets.QSpacerItem(20, 60, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.label = QtWidgets.QLabel(PasswordDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.username = QtWidgets.QLineEdit(PasswordDialog)
        self.username.setWindowModality(QtCore.Qt.NonModal)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.username.sizePolicy().hasHeightForWidth())
        self.username.setSizePolicy(sizePolicy)
        self.username.setObjectName("username")
        self.verticalLayout.addWidget(self.username)
        self.label_2 = QtWidgets.QLabel(PasswordDialog)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.password = QtWidgets.QLineEdit(PasswordDialog)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setObjectName("password")
        self.verticalLayout.addWidget(self.password)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.buttonbox = QtWidgets.QDialogButtonBox(PasswordDialog)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonbox.setObjectName("buttonbox")
        self.verticalLayout.addWidget(self.buttonbox)

        self.retranslateUi(PasswordDialog)
        self.buttonbox.rejected.connect(PasswordDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PasswordDialog)

    def retranslateUi(self, PasswordDialog):
        _translate = QtCore.QCoreApplication.translate
        PasswordDialog.setWindowTitle(_("Authentication required"))
        self.label.setText(_("Username:"))
        self.label_2.setText(_("Password:"))

