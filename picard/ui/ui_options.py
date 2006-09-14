# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options.ui'
#
# Created: Thu Sep 14 21:17:34 2006
#      by: PyQt4 UI code generator 4.0
#          E:\projects\picard-qt\ui\compile.py
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,485,398).size()).expandedTo(Dialog.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Dialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.splitter = QtGui.QSplitter(Dialog)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")

        self.pages_tree = QtGui.QTreeWidget(self.splitter)
        self.pages_tree.setObjectName("pages_tree")

        self.pages_stack = QtGui.QStackedWidget(self.splitter)
        self.pages_stack.setObjectName("pages_stack")
        self.vboxlayout.addWidget(self.splitter)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        spacerItem = QtGui.QSpacerItem(201,31,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)

        self.ok_button = QtGui.QPushButton(Dialog)
        self.ok_button.setObjectName("ok_button")
        self.hboxlayout.addWidget(self.ok_button)

        self.cancel_button = QtGui.QPushButton(Dialog)
        self.cancel_button.setObjectName("cancel_button")
        self.hboxlayout.addWidget(self.cancel_button)

        self.pushButton = QtGui.QPushButton(Dialog)
        self.pushButton.setObjectName("pushButton")
        self.hboxlayout.addWidget(self.pushButton)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.ok_button,QtCore.SIGNAL("clicked()"),Dialog.accept)
        QtCore.QObject.connect(self.cancel_button,QtCore.SIGNAL("clicked()"),Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_("Options"))
        self.ok_button.setText(_("&OK"))
        self.cancel_button.setText(_("&Cancel"))
        self.pushButton.setText(_("&Help"))
