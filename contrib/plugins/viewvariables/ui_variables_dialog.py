# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\variables_dialog.ui'
#
# Created: Wed Mar 26 06:58:04 2014
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

class Ui_VariablesDialog(object):
    def setupUi(self, VariablesDialog):
        VariablesDialog.setObjectName(_fromUtf8("VariablesDialog"))
        VariablesDialog.resize(600, 450)
        self.verticalLayout = QtGui.QVBoxLayout(VariablesDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.metadata_table = QtGui.QTableWidget(VariablesDialog)
        self.metadata_table.setAutoFillBackground(False)
        self.metadata_table.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)
        self.metadata_table.setRowCount(1)
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setObjectName(_fromUtf8("metadata_table"))
        item = QtGui.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.metadata_table.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.metadata_table.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
        self.metadata_table.setItem(0, 0, item)
        item = QtGui.QTableWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
        self.metadata_table.setItem(0, 1, item)
        self.metadata_table.horizontalHeader().setDefaultSectionSize(150)
        self.metadata_table.horizontalHeader().setSortIndicatorShown(False)
        self.metadata_table.horizontalHeader().setStretchLastSection(True)
        self.metadata_table.verticalHeader().setVisible(False)
        self.metadata_table.verticalHeader().setDefaultSectionSize(20)
        self.metadata_table.verticalHeader().setMinimumSectionSize(20)
        self.verticalLayout.addWidget(self.metadata_table)
        self.buttonBox = QtGui.QDialogButtonBox(VariablesDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(VariablesDialog)
        QtCore.QMetaObject.connectSlotsByName(VariablesDialog)

    def retranslateUi(self, VariablesDialog):
        item = self.metadata_table.horizontalHeaderItem(0)
        item.setText(_("Variable"))
        item = self.metadata_table.horizontalHeaderItem(1)
        item.setText(_("Value"))
        __sortingEnabled = self.metadata_table.isSortingEnabled()
        self.metadata_table.setSortingEnabled(False)
        self.metadata_table.setSortingEnabled(__sortingEnabled)

