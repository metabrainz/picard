# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_moving.ui'
#
# Created: Sun Jan 13 20:22:17 2008
#      by: PyQt4 UI code generator 4.3.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MovingOptionsPage(object):
    def setupUi(self, MovingOptionsPage):
        MovingOptionsPage.setObjectName("MovingOptionsPage")
        MovingOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,501,563).size()).expandedTo(MovingOptionsPage.minimumSizeHint()))

        self.gridlayout = QtGui.QGridLayout(MovingOptionsPage)
        self.gridlayout.setObjectName("gridlayout")

        self.move_files = QtGui.QGroupBox(MovingOptionsPage)
        self.move_files.setCheckable(True)
        self.move_files.setObjectName("move_files")

        self.vboxlayout = QtGui.QVBoxLayout(self.move_files)
        self.vboxlayout.setSpacing(2)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName("vboxlayout")

        self.label_2 = QtGui.QLabel(self.move_files)
        self.label_2.setObjectName("label_2")
        self.vboxlayout.addWidget(self.label_2)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setSpacing(2)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setObjectName("hboxlayout")

        self.move_files_to = QtGui.QLineEdit(self.move_files)
        self.move_files_to.setObjectName("move_files_to")
        self.hboxlayout.addWidget(self.move_files_to)

        self.move_files_to_browse = QtGui.QPushButton(self.move_files)
        self.move_files_to_browse.setObjectName("move_files_to_browse")
        self.hboxlayout.addWidget(self.move_files_to_browse)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.move_additional_files = QtGui.QCheckBox(self.move_files)
        self.move_additional_files.setObjectName("move_additional_files")
        self.vboxlayout.addWidget(self.move_additional_files)

        self.move_additional_files_pattern = QtGui.QLineEdit(self.move_files)
        self.move_additional_files_pattern.setObjectName("move_additional_files_pattern")
        self.vboxlayout.addWidget(self.move_additional_files_pattern)

        self.delete_empty_dirs = QtGui.QCheckBox(self.move_files)
        self.delete_empty_dirs.setObjectName("delete_empty_dirs")
        self.vboxlayout.addWidget(self.delete_empty_dirs)
        self.gridlayout.addWidget(self.move_files,0,0,1,1)

        spacerItem = QtGui.QSpacerItem(378,16,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem,1,0,1,1)
        self.label_2.setBuddy(self.move_files_to_browse)

        self.retranslateUi(MovingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MovingOptionsPage)
        MovingOptionsPage.setTabOrder(self.move_files_to,self.move_files_to_browse)

    def retranslateUi(self, MovingOptionsPage):
        self.move_files.setTitle(_("Move Files"))
        self.label_2.setText(_("Move tagged files to this directory:"))
        self.move_files_to_browse.setText(_("Browse..."))
        self.move_additional_files.setText(_("Move additional files:"))
        self.delete_empty_dirs.setText(_("Delete empty directories"))

