# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/cdlookup.ui'
#
# Created: Sun Jan 13 17:42:14 2008
#      by: PyQt4 UI code generator 4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,385,232).size()).expandedTo(Dialog.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Dialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)

        self.release_list = QtGui.QTreeWidget(Dialog)
        self.release_list.setRootIsDecorated(False)
        self.release_list.setObjectName("release_list")
        self.vboxlayout.addWidget(self.release_list)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        spacerItem = QtGui.QSpacerItem(111,31,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)

        self.ok_button = QtGui.QPushButton(Dialog)
        self.ok_button.setEnabled(False)
        self.ok_button.setObjectName("ok_button")
        self.hboxlayout.addWidget(self.ok_button)

        self.lookup_button = QtGui.QPushButton(Dialog)
        self.lookup_button.setObjectName("lookup_button")
        self.hboxlayout.addWidget(self.lookup_button)

        self.cancel_button = QtGui.QPushButton(Dialog)
        self.cancel_button.setObjectName("cancel_button")
        self.hboxlayout.addWidget(self.cancel_button)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.ok_button,QtCore.SIGNAL("clicked()"),Dialog.accept)
        QtCore.QObject.connect(self.cancel_button,QtCore.SIGNAL("clicked()"),Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.ok_button,self.cancel_button)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_("CD Lookup"))
        self.label.setText(_("The following releases on MusicBrainz match the CD:"))
        self.ok_button.setText(_("OK"))
        self.lookup_button.setText(_("    Lookup manually    "))
        self.cancel_button.setText(_("Cancel"))

