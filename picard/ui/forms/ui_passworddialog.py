# Form implementation generated from reading ui file 'ui/passworddialog.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PySide6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_PasswordDialog(object):
    def setupUi(self, PasswordDialog):
        PasswordDialog.setObjectName("PasswordDialog")
        PasswordDialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        PasswordDialog.resize(378, 246)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PasswordDialog.sizePolicy().hasHeightForWidth())
        PasswordDialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(PasswordDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.info_text = QtWidgets.QLabel(parent=PasswordDialog)
        self.info_text.setText("")
        self.info_text.setWordWrap(True)
        self.info_text.setObjectName("info_text")
        self.verticalLayout.addWidget(self.info_text)
        spacerItem = QtWidgets.QSpacerItem(20, 60, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.label = QtWidgets.QLabel(parent=PasswordDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.username = QtWidgets.QLineEdit(parent=PasswordDialog)
        self.username.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.username.sizePolicy().hasHeightForWidth())
        self.username.setSizePolicy(sizePolicy)
        self.username.setObjectName("username")
        self.verticalLayout.addWidget(self.username)
        self.label_2 = QtWidgets.QLabel(parent=PasswordDialog)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.password = QtWidgets.QLineEdit(parent=PasswordDialog)
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password.setObjectName("password")
        self.verticalLayout.addWidget(self.password)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.buttonbox = QtWidgets.QDialogButtonBox(parent=PasswordDialog)
        self.buttonbox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonbox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonbox.setObjectName("buttonbox")
        self.verticalLayout.addWidget(self.buttonbox)

        self.retranslateUi(PasswordDialog)
        self.buttonbox.rejected.connect(PasswordDialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(PasswordDialog)

    def retranslateUi(self, PasswordDialog):
        PasswordDialog.setWindowTitle(_("Authentication required"))
        self.label.setText(_("Username:"))
        self.label_2.setText(_("Password:"))
