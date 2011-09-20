# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_moving.ui'
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

class Ui_MovingOptionsPage(object):
    def setupUi(self, MovingOptionsPage):
        MovingOptionsPage.setObjectName(_fromUtf8("MovingOptionsPage"))
        MovingOptionsPage.resize(504, 563)
        self.gridlayout = QtGui.QGridLayout(MovingOptionsPage)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        spacerItem = QtGui.QSpacerItem(378, 16, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem, 8, 0, 1, 1)
        self.move_additional_files_pattern = QtGui.QLineEdit(MovingOptionsPage)
        self.move_additional_files_pattern.setObjectName(_fromUtf8("move_additional_files_pattern"))
        self.gridlayout.addWidget(self.move_additional_files_pattern, 5, 0, 1, 1)
        self.move_additional_files = QtGui.QCheckBox(MovingOptionsPage)
        self.move_additional_files.setObjectName(_fromUtf8("move_additional_files"))
        self.gridlayout.addWidget(self.move_additional_files, 4, 0, 1, 1)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setSpacing(2)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.move_files_to = QtGui.QLineEdit(MovingOptionsPage)
        self.move_files_to.setObjectName(_fromUtf8("move_files_to"))
        self.hboxlayout.addWidget(self.move_files_to)
        self.move_files_to_browse = QtGui.QPushButton(MovingOptionsPage)
        self.move_files_to_browse.setObjectName(_fromUtf8("move_files_to_browse"))
        self.hboxlayout.addWidget(self.move_files_to_browse)
        self.gridlayout.addLayout(self.hboxlayout, 2, 0, 1, 1)
        self.delete_empty_dirs = QtGui.QCheckBox(MovingOptionsPage)
        self.delete_empty_dirs.setObjectName(_fromUtf8("delete_empty_dirs"))
        self.gridlayout.addWidget(self.delete_empty_dirs, 3, 0, 1, 1)
        self.move_files = QtGui.QCheckBox(MovingOptionsPage)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.move_files.sizePolicy().hasHeightForWidth())
        self.move_files.setSizePolicy(sizePolicy)
        self.move_files.setObjectName(_fromUtf8("move_files"))
        self.gridlayout.addWidget(self.move_files, 1, 0, 1, 1)

        self.retranslateUi(MovingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MovingOptionsPage)

    def retranslateUi(self, MovingOptionsPage):
        self.move_additional_files.setText(_("Move additional files:"))
        self.move_files_to_browse.setText(_("Browse..."))
        self.delete_empty_dirs.setText(_("Delete empty directories"))
        self.move_files.setText(_("Move files to this directory when saving:"))

