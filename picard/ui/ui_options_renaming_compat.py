# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_RenamingCompatOptionsPage(object):
    def setupUi(self, RenamingCompatOptionsPage):
        RenamingCompatOptionsPage.setObjectName("RenamingCompatOptionsPage")
        RenamingCompatOptionsPage.setEnabled(True)
        RenamingCompatOptionsPage.resize(453, 374)
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
        self.windows_compatibility = QtWidgets.QCheckBox(RenamingCompatOptionsPage)
        self.windows_compatibility.setObjectName("windows_compatibility")
        self.verticalLayout_5.addWidget(self.windows_compatibility)
        self.windows_long_paths = QtWidgets.QCheckBox(RenamingCompatOptionsPage)
        self.windows_long_paths.setEnabled(False)
        self.windows_long_paths.setObjectName("windows_long_paths")
        self.verticalLayout_5.addWidget(self.windows_long_paths)
        self.replace_spaces_with_underscores = QtWidgets.QCheckBox(RenamingCompatOptionsPage)
        self.replace_spaces_with_underscores.setObjectName("replace_spaces_with_underscores")
        self.verticalLayout_5.addWidget(self.replace_spaces_with_underscores)
        self.example_selection_note = QtWidgets.QLabel(RenamingCompatOptionsPage)
        self.example_selection_note.setText("")
        self.example_selection_note.setWordWrap(True)
        self.example_selection_note.setObjectName("example_selection_note")
        self.verticalLayout_5.addWidget(self.example_selection_note)

        self.retranslateUi(RenamingCompatOptionsPage)
        self.windows_compatibility.toggled['bool'].connect(self.windows_long_paths.setEnabled) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(RenamingCompatOptionsPage)
        RenamingCompatOptionsPage.setTabOrder(self.ascii_filenames, self.windows_compatibility)
        RenamingCompatOptionsPage.setTabOrder(self.windows_compatibility, self.windows_long_paths)

    def retranslateUi(self, RenamingCompatOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.ascii_filenames.setText(_("Replace non-ASCII characters"))
        self.windows_compatibility.setText(_("Windows compatibility"))
        self.windows_long_paths.setText(_("Allow paths longer than 259 characters"))
        self.replace_spaces_with_underscores.setText(_("Replace spaces with underscores"))
