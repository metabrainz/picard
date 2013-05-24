# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\cdlookup.ui'
#
# Created: Fri May 24 19:28:34 2013
#      by: PyQt4 UI code generator 4.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(640, 240)
        self.vboxlayout = QtGui.QVBoxLayout(Dialog)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.vboxlayout.addWidget(self.label)
        self.release_list = QtGui.QTreeWidget(Dialog)
        self.release_list.setRootIsDecorated(False)
        self.release_list.setObjectName(_fromUtf8("release_list"))
        self.vboxlayout.addWidget(self.release_list)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        spacerItem = QtGui.QSpacerItem(111, 31, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.ok_button = QtGui.QPushButton(Dialog)
        self.ok_button.setEnabled(False)
        self.ok_button.setObjectName(_fromUtf8("ok_button"))
        self.hboxlayout.addWidget(self.ok_button)
        self.lookup_button = QtGui.QPushButton(Dialog)
        self.lookup_button.setObjectName(_fromUtf8("lookup_button"))
        self.hboxlayout.addWidget(self.lookup_button)
        self.cancel_button = QtGui.QPushButton(Dialog)
        self.cancel_button.setObjectName(_fromUtf8("cancel_button"))
        self.hboxlayout.addWidget(self.cancel_button)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.ok_button, QtCore.SIGNAL(_fromUtf8("clicked()")), Dialog.accept)
        QtCore.QObject.connect(self.cancel_button, QtCore.SIGNAL(_fromUtf8("clicked()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.ok_button, self.cancel_button)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_("CD Lookup"))
        self.label.setText(_("The following releases on MusicBrainz match the CD:"))
        self.ok_button.setText(_("OK"))
        self.lookup_button.setText(_("    Lookup manually    "))
        self.cancel_button.setText(_("Cancel"))

