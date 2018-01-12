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
        spacerItem = QtWidgets.QSpacerItem(88, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 4, 8, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(618, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 4, 0, 1, 6)
        self.searchLine = QtWidgets.QLineEdit(fileDialog)
        self.searchLine.setObjectName("searchLine")
        self.gridLayout.addWidget(self.searchLine, 0, 5, 1, 1)
        self.searchBtn = QtWidgets.QPushButton(fileDialog)
        self.searchBtn.setMinimumSize(QtCore.QSize(16, 28))
        self.searchBtn.setText("")
        self.searchBtn.setObjectName("searchBtn")
        self.gridLayout.addWidget(self.searchBtn, 0, 6, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(58, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 0, 4, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(118, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem3, 3, 0, 1, 1)
        spacerItem4 = QtWidgets.QSpacerItem(118, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem4, 0, 8, 1, 1)
        spacerItem5 = QtWidgets.QSpacerItem(138, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem5, 1, 1, 1, 4)
        self.recentList = QtWidgets.QListView(fileDialog)
        self.recentList.setObjectName("recentList")
        self.gridLayout.addWidget(self.recentList, 0, 0, 3, 1)
        self.showHiddenCb = QtWidgets.QCheckBox(fileDialog)
        self.showHiddenCb.setObjectName("showHiddenCb")
        self.gridLayout.addWidget(self.showHiddenCb, 4, 6, 1, 2)
        self.formatsCb = QtWidgets.QComboBox(fileDialog)
        self.formatsCb.setObjectName("formatsCb")
        self.gridLayout.addWidget(self.formatsCb, 4, 9, 1, 1)
        self.fileTree = QtWidgets.QTreeWidget(fileDialog)
        self.fileTree.setObjectName("fileTree")
        self.fileTree.headerItem().setText(0, "1")
        self.gridLayout.addWidget(self.fileTree, 2, 1, 1, 9)
        spacerItem6 = QtWidgets.QSpacerItem(88, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem6, 0, 7, 1, 1)
        self.selectBtn = QtWidgets.QPushButton(fileDialog)
        self.selectBtn.setObjectName("selectBtn")
        self.gridLayout.addWidget(self.selectBtn, 0, 9, 1, 1)
        self.moveBack = QtWidgets.QPushButton(fileDialog)
        self.moveBack.setText("")
        self.moveBack.setObjectName("moveBack")
        self.gridLayout.addWidget(self.moveBack, 0, 2, 1, 1)
        self.moveNext = QtWidgets.QPushButton(fileDialog)
        self.moveNext.setText("")
        self.moveNext.setObjectName("moveNext")
        self.gridLayout.addWidget(self.moveNext, 0, 3, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(fileDialog)
        QtCore.QMetaObject.connectSlotsByName(fileDialog)

    def retranslateUi(self, fileDialog):
        _translate = QtCore.QCoreApplication.translate
        print(_)
        fileDialog.setWindowTitle(_("Dialog"))
        self.searchLine.setText(_("search here"))
        self.showHiddenCb.setText(_("Show hidden files"))
        self.selectBtn.setText(_("Select it !"))

