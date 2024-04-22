# Form implementation generated from reading ui file 'ui/options_profiles.ui'
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


class Ui_ProfileEditorDialog(object):
    def setupUi(self, ProfileEditorDialog):
        ProfileEditorDialog.setObjectName("ProfileEditorDialog")
        ProfileEditorDialog.resize(430, 551)
        self.vboxlayout = QtWidgets.QVBoxLayout(ProfileEditorDialog)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.option_profiles_groupbox = QtWidgets.QGroupBox(parent=ProfileEditorDialog)
        self.option_profiles_groupbox.setCheckable(False)
        self.option_profiles_groupbox.setObjectName("option_profiles_groupbox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.option_profiles_groupbox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.profile_editor_splitter = QtWidgets.QSplitter(parent=self.option_profiles_groupbox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.profile_editor_splitter.sizePolicy().hasHeightForWidth())
        self.profile_editor_splitter.setSizePolicy(sizePolicy)
        self.profile_editor_splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.profile_editor_splitter.setChildrenCollapsible(False)
        self.profile_editor_splitter.setObjectName("profile_editor_splitter")
        self.profile_list = ProfileListWidget(parent=self.profile_editor_splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.profile_list.sizePolicy().hasHeightForWidth())
        self.profile_list.setSizePolicy(sizePolicy)
        self.profile_list.setMinimumSize(QtCore.QSize(120, 0))
        self.profile_list.setObjectName("profile_list")
        self.settings_tree = QtWidgets.QTreeWidget(parent=self.profile_editor_splitter)
        self.settings_tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        self.settings_tree.setColumnCount(1)
        self.settings_tree.setObjectName("settings_tree")
        self.settings_tree.headerItem().setText(0, "1")
        self.settings_tree.header().setVisible(True)
        self.verticalLayout.addWidget(self.profile_editor_splitter)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.move_up_button = QtWidgets.QToolButton(parent=self.option_profiles_groupbox)
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-up.png")
        self.move_up_button.setIcon(icon)
        self.move_up_button.setObjectName("move_up_button")
        self.horizontalLayout.addWidget(self.move_up_button)
        self.move_down_button = QtWidgets.QToolButton(parent=self.option_profiles_groupbox)
        icon = QtGui.QIcon.fromTheme(":/images/16x16/go-down.png")
        self.move_down_button.setIcon(icon)
        self.move_down_button.setObjectName("move_down_button")
        self.horizontalLayout.addWidget(self.move_down_button)
        self.profile_list_buttonbox = QtWidgets.QDialogButtonBox(parent=self.option_profiles_groupbox)
        self.profile_list_buttonbox.setMinimumSize(QtCore.QSize(0, 10))
        self.profile_list_buttonbox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.NoButton)
        self.profile_list_buttonbox.setObjectName("profile_list_buttonbox")
        self.horizontalLayout.addWidget(self.profile_list_buttonbox)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.vboxlayout.addWidget(self.option_profiles_groupbox)

        self.retranslateUi(ProfileEditorDialog)
        QtCore.QMetaObject.connectSlotsByName(ProfileEditorDialog)

    def retranslateUi(self, ProfileEditorDialog):
        self.option_profiles_groupbox.setTitle(_("Option Profile(s)"))
        self.move_up_button.setToolTip(_("Move profile up"))
        self.move_down_button.setToolTip(_("Move profile down"))
from picard.ui.widgets.profilelistwidget import ProfileListWidget
