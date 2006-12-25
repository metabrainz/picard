# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/edittagdialog.ui'
#
# Created: Sat Dec 23 13:51:18 2006
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

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")

        spacerItem = QtGui.QSpacerItem(131,31,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem)

        self.okButton = QtGui.QPushButton(EditTagDialog)
        self.okButton.setDefault(True)
        self.okButton.setObjectName("okButton")
        self.hboxlayout1.addWidget(self.okButton)

        self.cancelButton = QtGui.QPushButton(EditTagDialog)
        self.cancelButton.setObjectName("cancelButton")
        self.hboxlayout1.addWidget(self.cancelButton)
        self.vboxlayout.addLayout(self.hboxlayout1)

        self.retranslateUi(EditTagDialog)
        QtCore.QObject.connect(self.okButton,QtCore.SIGNAL("clicked()"),EditTagDialog.accept)
        QtCore.QObject.connect(self.cancelButton,QtCore.SIGNAL("clicked()"),EditTagDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(EditTagDialog)

    def retranslateUi(self, EditTagDialog):
        EditTagDialog.setWindowTitle(_(u"Edit Tag"))
        self.okButton.setText(_(u"OK"))
        self.cancelButton.setText(_(u"Cancel"))

