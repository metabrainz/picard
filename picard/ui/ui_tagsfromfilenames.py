# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/tagsfromfilenames.ui'
#
# Created: Wed Feb  7 20:43:14 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_TagsFromFileNamesDialog(object):
    def setupUi(self, TagsFromFileNamesDialog):
        TagsFromFileNamesDialog.setObjectName("TagsFromFileNamesDialog")
        TagsFromFileNamesDialog.resize(QtCore.QSize(QtCore.QRect(0,0,487,368).size()).expandedTo(TagsFromFileNamesDialog.minimumSizeHint()))

        self.gridlayout = QtGui.QGridLayout(TagsFromFileNamesDialog)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")

        self.files = QtGui.QTreeWidget(TagsFromFileNamesDialog)
        self.files.setAlternatingRowColors(True)
        self.files.setRootIsDecorated(False)
        self.files.setObjectName("files")
        self.gridlayout.addWidget(self.files,1,0,1,2)

        self.replace_underscores = QtGui.QCheckBox(TagsFromFileNamesDialog)
        self.replace_underscores.setObjectName("replace_underscores")
        self.gridlayout.addWidget(self.replace_underscores,2,0,1,2)

        self.buttonbox = QtGui.QDialogButtonBox(TagsFromFileNamesDialog)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setObjectName("buttonbox")
        self.gridlayout.addWidget(self.buttonbox,3,0,1,2)

        self.preview = QtGui.QPushButton(TagsFromFileNamesDialog)
        self.preview.setObjectName("preview")
        self.gridlayout.addWidget(self.preview,0,1,1,1)

        self.format = QtGui.QComboBox(TagsFromFileNamesDialog)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.format.sizePolicy().hasHeightForWidth())
        self.format.setSizePolicy(sizePolicy)
        self.format.setEditable(True)
        self.format.setObjectName("format")
        self.gridlayout.addWidget(self.format,0,0,1,1)

        self.retranslateUi(TagsFromFileNamesDialog)
        QtCore.QMetaObject.connectSlotsByName(TagsFromFileNamesDialog)

    def retranslateUi(self, TagsFromFileNamesDialog):
        TagsFromFileNamesDialog.setWindowTitle(_(u"Convert File Names to Tags"))
        self.replace_underscores.setText(_(u"Replace underscores with spaces"))
        self.preview.setText(_(u"&Preview"))

