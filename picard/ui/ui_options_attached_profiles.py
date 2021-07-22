# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AttachedProfilesDialog(object):
    def setupUi(self, AttachedProfilesDialog):
        AttachedProfilesDialog.setObjectName("AttachedProfilesDialog")
        AttachedProfilesDialog.resize(800, 450)
        self.vboxlayout = QtWidgets.QVBoxLayout(AttachedProfilesDialog)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.options_list = QtWidgets.QTableView(AttachedProfilesDialog)
        self.options_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.options_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.options_list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.options_list.setObjectName("options_list")
        self.vboxlayout.addWidget(self.options_list)
        self.buttonBox = QtWidgets.QDialogButtonBox(AttachedProfilesDialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.NoButton)
        self.buttonBox.setObjectName("buttonBox")
        self.vboxlayout.addWidget(self.buttonBox)

        self.retranslateUi(AttachedProfilesDialog)
        QtCore.QMetaObject.connectSlotsByName(AttachedProfilesDialog)

    def retranslateUi(self, AttachedProfilesDialog):
        _translate = QtCore.QCoreApplication.translate
        AttachedProfilesDialog.setWindowTitle(_("Profiles Attached to Options"))
