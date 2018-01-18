# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_TagsFromFileNamesDialog(object):
    def setupUi(self, TagsFromFileNamesDialog):
        TagsFromFileNamesDialog.setObjectName("TagsFromFileNamesDialog")
        TagsFromFileNamesDialog.resize(487, 368)
        self.gridlayout = QtWidgets.QGridLayout(TagsFromFileNamesDialog)
        self.gridlayout.setContentsMargins(9, 9, 9, 9)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")
        self.files = QtWidgets.QTreeWidget(TagsFromFileNamesDialog)
        self.files.setAlternatingRowColors(True)
        self.files.setRootIsDecorated(False)
        self.files.setObjectName("files")
        self.files.headerItem().setText(0, "1")
        self.gridlayout.addWidget(self.files, 1, 0, 1, 2)
        self.replace_underscores = QtWidgets.QCheckBox(TagsFromFileNamesDialog)
        self.replace_underscores.setObjectName("replace_underscores")
        self.gridlayout.addWidget(self.replace_underscores, 2, 0, 1, 2)
        self.buttonbox = QtWidgets.QDialogButtonBox(TagsFromFileNamesDialog)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setObjectName("buttonbox")
        self.gridlayout.addWidget(self.buttonbox, 3, 0, 1, 2)
        self.preview = QtWidgets.QPushButton(TagsFromFileNamesDialog)
        self.preview.setObjectName("preview")
        self.gridlayout.addWidget(self.preview, 0, 1, 1, 1)
        self.format = QtWidgets.QComboBox(TagsFromFileNamesDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.format.sizePolicy().hasHeightForWidth())
        self.format.setSizePolicy(sizePolicy)
        self.format.setEditable(True)
        self.format.setObjectName("format")
        self.gridlayout.addWidget(self.format, 0, 0, 1, 1)

        self.retranslateUi(TagsFromFileNamesDialog)
        QtCore.QMetaObject.connectSlotsByName(TagsFromFileNamesDialog)
        TagsFromFileNamesDialog.setTabOrder(self.format, self.preview)
        TagsFromFileNamesDialog.setTabOrder(self.preview, self.files)
        TagsFromFileNamesDialog.setTabOrder(self.files, self.replace_underscores)
        TagsFromFileNamesDialog.setTabOrder(self.replace_underscores, self.buttonbox)

    def retranslateUi(self, TagsFromFileNamesDialog):
        _translate = QtCore.QCoreApplication.translate
        TagsFromFileNamesDialog.setWindowTitle(_("Convert File Names to Tags"))
        self.replace_underscores.setText(_("Replace underscores with spaces"))
        self.preview.setText(_("&Preview"))

