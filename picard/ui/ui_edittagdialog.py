# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/edittagdialog.ui'
#
# Created: Sat Mar  3 19:09:31 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_EditTagDialog(object):
    def setupUi(self, EditTagDialog):
        EditTagDialog.setObjectName("EditTagDialog")
        EditTagDialog.resize(QtCore.QSize(QtCore.QRect(0,0,384,225).size()).expandedTo(EditTagDialog.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(EditTagDialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.name = QtGui.QComboBox(EditTagDialog)
        self.name.setObjectName("name")
        self.hboxlayout.addWidget(self.name)

        self.desc = QtGui.QLineEdit(EditTagDialog)
        self.desc.setObjectName("desc")
        self.hboxlayout.addWidget(self.desc)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.value = QtGui.QTextEdit(EditTagDialog)
        self.value.setTabChangesFocus(True)
        self.value.setAcceptRichText(False)
        self.value.setObjectName("value")
        self.vboxlayout.addWidget(self.value)

        self.buttonbox = QtGui.QDialogButtonBox(EditTagDialog)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setObjectName("buttonbox")
        self.vboxlayout.addWidget(self.buttonbox)

        self.retranslateUi(EditTagDialog)
        QtCore.QMetaObject.connectSlotsByName(EditTagDialog)

    def retranslateUi(self, EditTagDialog):
        EditTagDialog.setWindowTitle(_(u"Edit Tag"))

