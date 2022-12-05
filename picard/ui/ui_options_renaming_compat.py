# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_RenamingCompatOptionsPage(object):
    def setupUi(self, RenamingCompatOptionsPage):
        RenamingCompatOptionsPage.setObjectName("RenamingCompatOptionsPage")
        RenamingCompatOptionsPage.setEnabled(True)
        RenamingCompatOptionsPage.resize(453, 332)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RenamingCompatOptionsPage.sizePolicy().hasHeightForWidth())
        RenamingCompatOptionsPage.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(RenamingCompatOptionsPage)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.ascii_filenames = QtWidgets.QCheckBox(RenamingCompatOptionsPage)
        self.ascii_filenames.setObjectName("ascii_filenames")
        self.verticalLayout_5.addWidget(self.ascii_filenames)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.windows_compatibility = QtWidgets.QCheckBox(RenamingCompatOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.windows_compatibility.sizePolicy().hasHeightForWidth())
        self.windows_compatibility.setSizePolicy(sizePolicy)
        self.windows_compatibility.setObjectName("windows_compatibility")
        self.horizontalLayout.addWidget(self.windows_compatibility)
        self.btn_windows_compatibility_change = QtWidgets.QPushButton(RenamingCompatOptionsPage)
        self.btn_windows_compatibility_change.setEnabled(False)
        self.btn_windows_compatibility_change.setObjectName("btn_windows_compatibility_change")
        self.horizontalLayout.addWidget(self.btn_windows_compatibility_change)
        self.verticalLayout_5.addLayout(self.horizontalLayout)
        self.windows_long_paths = QtWidgets.QCheckBox(RenamingCompatOptionsPage)
        self.windows_long_paths.setEnabled(False)
        self.windows_long_paths.setObjectName("windows_long_paths")
        self.verticalLayout_5.addWidget(self.windows_long_paths)
        self.replace_spaces_with_underscores = QtWidgets.QCheckBox(RenamingCompatOptionsPage)
        self.replace_spaces_with_underscores.setObjectName("replace_spaces_with_underscores")
        self.verticalLayout_5.addWidget(self.replace_spaces_with_underscores)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem)
        self.example_selection_note = QtWidgets.QLabel(RenamingCompatOptionsPage)
        self.example_selection_note.setText("")
        self.example_selection_note.setWordWrap(True)
        self.example_selection_note.setObjectName("example_selection_note")
        self.verticalLayout_5.addWidget(self.example_selection_note)

        self.retranslateUi(RenamingCompatOptionsPage)
        self.windows_compatibility.toggled['bool'].connect(self.windows_long_paths.setEnabled) # type: ignore
        self.windows_compatibility.toggled['bool'].connect(self.btn_windows_compatibility_change.setEnabled) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(RenamingCompatOptionsPage)
        RenamingCompatOptionsPage.setTabOrder(self.ascii_filenames, self.windows_long_paths)

    def retranslateUi(self, RenamingCompatOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.ascii_filenames.setText(_("Replace non-ASCII characters"))
        self.windows_compatibility.setText(_("Windows compatibility"))
        self.btn_windows_compatibility_change.setText(_("Customize..."))
        self.windows_long_paths.setText(_("Allow paths longer than 259 characters"))
        self.replace_spaces_with_underscores.setText(_("Replace spaces with underscores"))
