# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_fileDialog(object):
    def setupUi(self, fileDialog):
        fileDialog.setObjectName("fileDialog")
        fileDialog.resize(1218, 554)
        self.gridLayout_2 = QtWidgets.QGridLayout(fileDialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(118, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 6, 1, 1)
        self.recentList = QtWidgets.QListView(fileDialog)
        self.recentList.setObjectName("recentList")
        self.gridLayout.addWidget(self.recentList, 0, 0, 3, 1)
        self.searchLine = QtWidgets.QLineEdit(fileDialog)
        self.searchLine.setObjectName("searchLine")
        self.gridLayout.addWidget(self.searchLine, 0, 3, 1, 1)
        self.searchBtn = QtWidgets.QPushButton(fileDialog)
        self.searchBtn.setMinimumSize(QtCore.QSize(16, 28))
        self.searchBtn.setText("")
        self.searchBtn.setObjectName("searchBtn")
        self.gridLayout.addWidget(self.searchBtn, 0, 4, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(88, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 4, 6, 1, 1)
        self.formatsCb = QtWidgets.QComboBox(fileDialog)
        self.formatsCb.setObjectName("formatsCb")
        self.gridLayout.addWidget(self.formatsCb, 4, 7, 1, 1)
        self.fileTree = QtWidgets.QTreeView(fileDialog)
        self.fileTree.setObjectName("fileTree")
        self.gridLayout.addWidget(self.fileTree, 2, 1, 1, 7)
        spacerItem2 = QtWidgets.QSpacerItem(618, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 4, 0, 1, 4)
        spacerItem3 = QtWidgets.QSpacerItem(88, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem3, 0, 5, 1, 1)
        self.selectBtn = QtWidgets.QPushButton(fileDialog)
        self.selectBtn.setObjectName("selectBtn")
        self.gridLayout.addWidget(self.selectBtn, 0, 7, 1, 1)
        spacerItem4 = QtWidgets.QSpacerItem(118, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem4, 3, 0, 1, 1)
        spacerItem5 = QtWidgets.QSpacerItem(58, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem5, 0, 2, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(fileDialog)
        QtCore.QMetaObject.connectSlotsByName(fileDialog)

    def retranslateUi(self, fileDialog):
        _translate = QtCore.QCoreApplication.translate
        fileDialog.setWindowTitle(_("FileDialog"))
        self.searchLine.setText(_("search here"))
        self.selectBtn.setText(_("Select"))

