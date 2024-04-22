# Form implementation generated from reading ui file 'ui/options_attached_profiles.ui'
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


class Ui_AttachedProfilesDialog(object):
    def setupUi(self, AttachedProfilesDialog):
        AttachedProfilesDialog.setObjectName("AttachedProfilesDialog")
        AttachedProfilesDialog.resize(800, 450)
        self.vboxlayout = QtWidgets.QVBoxLayout(AttachedProfilesDialog)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.options_list = QtWidgets.QTableView(parent=AttachedProfilesDialog)
        self.options_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.options_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.options_list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.options_list.setObjectName("options_list")
        self.vboxlayout.addWidget(self.options_list)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=AttachedProfilesDialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.NoButton)
        self.buttonBox.setObjectName("buttonBox")
        self.vboxlayout.addWidget(self.buttonBox)

        self.retranslateUi(AttachedProfilesDialog)
        QtCore.QMetaObject.connectSlotsByName(AttachedProfilesDialog)

    def retranslateUi(self, AttachedProfilesDialog):
        AttachedProfilesDialog.setWindowTitle(_("Profiles Attached to Options"))
