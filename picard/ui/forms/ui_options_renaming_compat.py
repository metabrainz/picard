# Form implementation generated from reading ui file 'ui/options_renaming_compat.ui'
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


class Ui_RenamingCompatOptionsPage(object):
    def setupUi(self, RenamingCompatOptionsPage):
        RenamingCompatOptionsPage.setObjectName("RenamingCompatOptionsPage")
        RenamingCompatOptionsPage.setEnabled(True)
        RenamingCompatOptionsPage.resize(453, 332)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RenamingCompatOptionsPage.sizePolicy().hasHeightForWidth())
        RenamingCompatOptionsPage.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(RenamingCompatOptionsPage)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.ascii_filenames = QtWidgets.QCheckBox(parent=RenamingCompatOptionsPage)
        self.ascii_filenames.setObjectName("ascii_filenames")
        self.verticalLayout_5.addWidget(self.ascii_filenames)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.windows_compatibility = QtWidgets.QCheckBox(parent=RenamingCompatOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.windows_compatibility.sizePolicy().hasHeightForWidth())
        self.windows_compatibility.setSizePolicy(sizePolicy)
        self.windows_compatibility.setObjectName("windows_compatibility")
        self.horizontalLayout.addWidget(self.windows_compatibility)
        self.btn_windows_compatibility_change = QtWidgets.QPushButton(parent=RenamingCompatOptionsPage)
        self.btn_windows_compatibility_change.setEnabled(False)
        self.btn_windows_compatibility_change.setObjectName("btn_windows_compatibility_change")
        self.horizontalLayout.addWidget(self.btn_windows_compatibility_change)
        self.verticalLayout_5.addLayout(self.horizontalLayout)
        self.windows_long_paths = QtWidgets.QCheckBox(parent=RenamingCompatOptionsPage)
        self.windows_long_paths.setEnabled(False)
        self.windows_long_paths.setObjectName("windows_long_paths")
        self.verticalLayout_5.addWidget(self.windows_long_paths)
        self.replace_spaces_with_underscores = QtWidgets.QCheckBox(parent=RenamingCompatOptionsPage)
        self.replace_spaces_with_underscores.setObjectName("replace_spaces_with_underscores")
        self.verticalLayout_5.addWidget(self.replace_spaces_with_underscores)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_replace_dir_separator = QtWidgets.QLabel(parent=RenamingCompatOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_replace_dir_separator.sizePolicy().hasHeightForWidth())
        self.label_replace_dir_separator.setSizePolicy(sizePolicy)
        self.label_replace_dir_separator.setObjectName("label_replace_dir_separator")
        self.horizontalLayout_2.addWidget(self.label_replace_dir_separator)
        self.replace_dir_separator = QtWidgets.QLineEdit(parent=RenamingCompatOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.replace_dir_separator.sizePolicy().hasHeightForWidth())
        self.replace_dir_separator.setSizePolicy(sizePolicy)
        self.replace_dir_separator.setMaximumSize(QtCore.QSize(20, 16777215))
        self.replace_dir_separator.setText("_")
        self.replace_dir_separator.setMaxLength(1)
        self.replace_dir_separator.setObjectName("replace_dir_separator")
        self.horizontalLayout_2.addWidget(self.replace_dir_separator)
        self.verticalLayout_5.addLayout(self.horizontalLayout_2)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_5.addItem(spacerItem)
        self.example_selection_note = QtWidgets.QLabel(parent=RenamingCompatOptionsPage)
        self.example_selection_note.setText("")
        self.example_selection_note.setWordWrap(True)
        self.example_selection_note.setObjectName("example_selection_note")
        self.verticalLayout_5.addWidget(self.example_selection_note)

        self.retranslateUi(RenamingCompatOptionsPage)
        self.windows_compatibility.toggled['bool'].connect(self.windows_long_paths.setEnabled) # type: ignore
        self.windows_compatibility.toggled['bool'].connect(self.btn_windows_compatibility_change.setEnabled) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(RenamingCompatOptionsPage)
        RenamingCompatOptionsPage.setTabOrder(self.ascii_filenames, self.windows_compatibility)
        RenamingCompatOptionsPage.setTabOrder(self.windows_compatibility, self.btn_windows_compatibility_change)
        RenamingCompatOptionsPage.setTabOrder(self.btn_windows_compatibility_change, self.windows_long_paths)
        RenamingCompatOptionsPage.setTabOrder(self.windows_long_paths, self.replace_spaces_with_underscores)
        RenamingCompatOptionsPage.setTabOrder(self.replace_spaces_with_underscores, self.replace_dir_separator)

    def retranslateUi(self, RenamingCompatOptionsPage):
        self.ascii_filenames.setText(_("Replace non-ASCII characters"))
        self.windows_compatibility.setText(_("Windows compatibility"))
        self.btn_windows_compatibility_change.setText(_("Customize…"))
        self.windows_long_paths.setText(_("Allow paths longer than 259 characters"))
        self.replace_spaces_with_underscores.setText(_("Replace spaces with underscores"))
        self.label_replace_dir_separator.setText(_("Replace directory separators with:"))
