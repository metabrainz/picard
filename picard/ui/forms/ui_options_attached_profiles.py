# Form implementation generated from reading ui file 'ui/options_attached_profiles.ui'
#
# Created by: PyQt6 UI code generator 6.11.0
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_AttachedProfilesDialog(object):
    def setupUi(self, AttachedProfilesDialog):
        AttachedProfilesDialog.setObjectName("AttachedProfilesDialog")
        AttachedProfilesDialog.resize(650, 400)
        self.vboxlayout = QtWidgets.QVBoxLayout(AttachedProfilesDialog)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.splitter = QtWidgets.QSplitter(parent=AttachedProfilesDialog)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setObjectName("splitter")
        self.left_panel = QtWidgets.QWidget(parent=self.splitter)
        self.left_panel.setObjectName("left_panel")
        self.left_layout = QtWidgets.QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setObjectName("left_layout")
        self.profiles_label = QtWidgets.QLabel(parent=self.left_panel)
        self.profiles_label.setObjectName("profiles_label")
        self.left_layout.addWidget(self.profiles_label)
        self.profile_list = QtWidgets.QTreeWidget(parent=self.left_panel)
        self.profile_list.setHeaderHidden(True)
        self.profile_list.setRootIsDecorated(False)
        self.profile_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.profile_list.setObjectName("profile_list")
        self.profile_list.headerItem().setText(0, "1")
        self.profile_list.headerItem().setText(1, "2")
        self.left_layout.addWidget(self.profile_list)
        self.right_panel = QtWidgets.QWidget(parent=self.splitter)
        self.right_panel.setObjectName("right_panel")
        self.right_layout = QtWidgets.QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setObjectName("right_layout")
        self.options_label = QtWidgets.QLabel(parent=self.right_panel)
        self.options_label.setObjectName("options_label")
        self.right_layout.addWidget(self.options_label)
        self.settings_tree = QtWidgets.QTreeWidget(parent=self.right_panel)
        self.settings_tree.setHeaderHidden(True)
        self.settings_tree.setObjectName("settings_tree")
        self.settings_tree.headerItem().setText(0, "1")
        self.right_layout.addWidget(self.settings_tree)
        self.vboxlayout.addWidget(self.splitter)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=AttachedProfilesDialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.NoButton)
        self.buttonBox.setObjectName("buttonBox")
        self.vboxlayout.addWidget(self.buttonBox)

        self.retranslateUi(AttachedProfilesDialog)
        QtCore.QMetaObject.connectSlotsByName(AttachedProfilesDialog)

    def retranslateUi(self, AttachedProfilesDialog):
        AttachedProfilesDialog.setWindowTitle(_("Profiles Attached to Options"))
        self.profiles_label.setText(_("Profiles"))
        self.options_label.setText(_("Options in this section"))
