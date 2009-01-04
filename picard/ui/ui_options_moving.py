# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_moving.ui'
#
# Created: Sun Jan  4 22:20:33 2009
#      by: PyQt4 UI code generator 4.4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MovingOptionsPage(object):
    def setupUi(self, MovingOptionsPage):
        MovingOptionsPage.setObjectName("MovingOptionsPage")
        MovingOptionsPage.resize(504, 563)
        self.gridlayout = QtGui.QGridLayout(MovingOptionsPage)
        self.gridlayout.setObjectName("gridlayout")
        spacerItem = QtGui.QSpacerItem(378, 16, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem, 10, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(MovingOptionsPage)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setWeight(75)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.move_files = QtGui.QCheckBox(MovingOptionsPage)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.move_files.sizePolicy().hasHeightForWidth())
        self.move_files.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.move_files.setFont(font)
        self.move_files.setObjectName("move_files")
        self.horizontalLayout.addWidget(self.move_files)
        self.gridlayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.line = QtGui.QFrame(MovingOptionsPage)
        self.line.setFrameShadow(QtGui.QFrame.Plain)
        self.line.setLineWidth(2)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridlayout.addWidget(self.line, 1, 0, 1, 1)
        self.move_additional_files_pattern = QtGui.QLineEdit(MovingOptionsPage)
        self.move_additional_files_pattern.setObjectName("move_additional_files_pattern")
        self.gridlayout.addWidget(self.move_additional_files_pattern, 7, 0, 1, 1)
        self.move_additional_files = QtGui.QCheckBox(MovingOptionsPage)
        self.move_additional_files.setObjectName("move_additional_files")
        self.gridlayout.addWidget(self.move_additional_files, 6, 0, 1, 1)
        self.label_2 = QtGui.QLabel(MovingOptionsPage)
        self.label_2.setObjectName("label_2")
        self.gridlayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setSpacing(2)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setObjectName("hboxlayout")
        self.move_files_to = QtGui.QLineEdit(MovingOptionsPage)
        self.move_files_to.setObjectName("move_files_to")
        self.hboxlayout.addWidget(self.move_files_to)
        self.move_files_to_browse = QtGui.QPushButton(MovingOptionsPage)
        self.move_files_to_browse.setObjectName("move_files_to_browse")
        self.hboxlayout.addWidget(self.move_files_to_browse)
        self.gridlayout.addLayout(self.hboxlayout, 4, 0, 1, 1)
        self.delete_empty_dirs = QtGui.QCheckBox(MovingOptionsPage)
        self.delete_empty_dirs.setObjectName("delete_empty_dirs")
        self.gridlayout.addWidget(self.delete_empty_dirs, 5, 0, 1, 1)
        self.label_2.setBuddy(self.move_files_to_browse)

        self.retranslateUi(MovingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MovingOptionsPage)

    def retranslateUi(self, MovingOptionsPage):
        self.label.setText(_("Move files"))
        self.move_files.setText(_("Enabled"))
        self.move_additional_files.setText(_("Move additional files:"))
        self.label_2.setText(_("Move tagged files to this directory:"))
        self.move_files_to_browse.setText(_("Browse..."))
        self.delete_empty_dirs.setText(_("Delete empty directories"))

