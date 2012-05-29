# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/tagsfromfilenames.ui'
#
# Created: Tue May 29 19:44:15 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_TagsFromFileNamesDialog(object):
    def setupUi(self, TagsFromFileNamesDialog):
        TagsFromFileNamesDialog.setObjectName(_fromUtf8("TagsFromFileNamesDialog"))
        TagsFromFileNamesDialog.resize(487, 368)
        self.gridlayout = QtGui.QGridLayout(TagsFromFileNamesDialog)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.files = QtGui.QTreeWidget(TagsFromFileNamesDialog)
        self.files.setAlternatingRowColors(True)
        self.files.setRootIsDecorated(False)
        self.files.setObjectName(_fromUtf8("files"))
        self.gridlayout.addWidget(self.files, 1, 0, 1, 2)
        self.replace_underscores = QtGui.QCheckBox(TagsFromFileNamesDialog)
        self.replace_underscores.setObjectName(_fromUtf8("replace_underscores"))
        self.gridlayout.addWidget(self.replace_underscores, 2, 0, 1, 2)
        self.buttonbox = QtGui.QDialogButtonBox(TagsFromFileNamesDialog)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setObjectName(_fromUtf8("buttonbox"))
        self.gridlayout.addWidget(self.buttonbox, 3, 0, 1, 2)
        self.preview = QtGui.QPushButton(TagsFromFileNamesDialog)
        self.preview.setObjectName(_fromUtf8("preview"))
        self.gridlayout.addWidget(self.preview, 0, 1, 1, 1)
        self.format = QtGui.QComboBox(TagsFromFileNamesDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7), QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.format.sizePolicy().hasHeightForWidth())
        self.format.setSizePolicy(sizePolicy)
        self.format.setEditable(True)
        self.format.setObjectName(_fromUtf8("format"))
        self.gridlayout.addWidget(self.format, 0, 0, 1, 1)

        self.retranslateUi(TagsFromFileNamesDialog)
        QtCore.QMetaObject.connectSlotsByName(TagsFromFileNamesDialog)

    def retranslateUi(self, TagsFromFileNamesDialog):
        TagsFromFileNamesDialog.setWindowTitle(_("Convert File Names to Tags"))
        self.replace_underscores.setText(_("Replace underscores with spaces"))
        self.preview.setText(_("&Preview"))

