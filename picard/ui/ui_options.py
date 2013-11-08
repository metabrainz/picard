# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options.ui'
#
# Created: Fri Nov  8 17:04:27 2013
#      by: PyQt4 UI code generator 4.10.3
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
        Dialog.resize(485, 398)
        self.vboxlayout = QtGui.QVBoxLayout(Dialog)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.splitter = QtGui.QSplitter(Dialog)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.pages_tree = QtGui.QTreeWidget(self.splitter)
        self.pages_tree.setObjectName(_fromUtf8("pages_tree"))
        self.pages_stack = QtGui.QStackedWidget(self.splitter)
        self.pages_stack.setObjectName(_fromUtf8("pages_stack"))
        self.vboxlayout.addWidget(self.splitter)
        self.buttonbox = QtGui.QDialogButtonBox(Dialog)
        self.buttonbox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonbox.setObjectName(_fromUtf8("buttonbox"))
        self.vboxlayout.addWidget(self.buttonbox)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_("Options"))

