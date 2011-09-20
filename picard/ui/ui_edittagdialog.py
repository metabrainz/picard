# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/edittagdialog.ui'
#
# Created: Thu Sep 15 13:39:10 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_EditTagDialog(object):
    def setupUi(self, EditTagDialog):
        EditTagDialog.setObjectName(_fromUtf8("EditTagDialog"))
        EditTagDialog.resize(384, 225)
        self.vboxlayout = QtGui.QVBoxLayout(EditTagDialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.name = QtGui.QComboBox(EditTagDialog)
        self.name.setEditable(True)
        self.name.setObjectName(_fromUtf8("name"))
        self.vboxlayout.addWidget(self.name)
        self.value = QtGui.QTextEdit(EditTagDialog)
        self.value.setTabChangesFocus(True)
        self.value.setAcceptRichText(False)
        self.value.setObjectName(_fromUtf8("value"))
        self.vboxlayout.addWidget(self.value)
        self.buttonbox = QtGui.QDialogButtonBox(EditTagDialog)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setObjectName(_fromUtf8("buttonbox"))
        self.vboxlayout.addWidget(self.buttonbox)

        self.retranslateUi(EditTagDialog)
        QtCore.QMetaObject.connectSlotsByName(EditTagDialog)
        EditTagDialog.setTabOrder(self.buttonbox, self.name)
        EditTagDialog.setTabOrder(self.name, self.value)

    def retranslateUi(self, EditTagDialog):
        EditTagDialog.setWindowTitle(_("Edit Tag"))

