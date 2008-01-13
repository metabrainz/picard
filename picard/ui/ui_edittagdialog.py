# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/edittagdialog.ui'
#
# Created: Sun Jan 13 17:42:14 2008
#      by: PyQt4 UI code generator 4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_EditTagDialog(object):
    def setupUi(self, EditTagDialog):
        EditTagDialog.setObjectName("EditTagDialog")
        EditTagDialog.resize(QtCore.QSize(QtCore.QRect(0,0,384,225).size()).expandedTo(EditTagDialog.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(EditTagDialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.name = QtGui.QComboBox(EditTagDialog)
        self.name.setEditable(True)
        self.name.setObjectName("name")
        self.vboxlayout.addWidget(self.name)

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
        EditTagDialog.setTabOrder(self.buttonbox,self.name)
        EditTagDialog.setTabOrder(self.name,self.value)

    def retranslateUi(self, EditTagDialog):
        EditTagDialog.setWindowTitle(_("Edit Tag"))

