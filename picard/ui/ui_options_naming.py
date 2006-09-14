# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_naming.ui'
#
# Created: Thu Sep 14 21:17:34 2006
#      by: PyQt4 UI code generator 4.0
#          E:\projects\picard-qt\ui\compile.py
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,401,426).size()).expandedTo(Form.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Form)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.rename_files = QtGui.QGroupBox(Form)
        self.rename_files.setCheckable(True)
        self.rename_files.setObjectName("rename_files")

        self.gridlayout = QtGui.QGridLayout(self.rename_files)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        self.windows_compatible_filenames = QtGui.QCheckBox(self.rename_files)
        self.windows_compatible_filenames.setObjectName("windows_compatible_filenames")
        self.gridlayout.addWidget(self.windows_compatible_filenames,4,0,1,2)

        self.ascii_filenames = QtGui.QCheckBox(self.rename_files)
        self.ascii_filenames.setObjectName("ascii_filenames")
        self.gridlayout.addWidget(self.ascii_filenames,5,0,1,2)

        self.va_file_naming_format = QtGui.QLineEdit(self.rename_files)
        self.va_file_naming_format.setObjectName("va_file_naming_format")
        self.gridlayout.addWidget(self.va_file_naming_format,3,0,1,1)

        self.va_file_naming_format_default = QtGui.QPushButton(self.rename_files)
        self.va_file_naming_format_default.setObjectName("va_file_naming_format_default")
        self.gridlayout.addWidget(self.va_file_naming_format_default,3,1,1,1)

        self.file_naming_format_default = QtGui.QPushButton(self.rename_files)
        self.file_naming_format_default.setObjectName("file_naming_format_default")
        self.gridlayout.addWidget(self.file_naming_format_default,1,1,1,1)

        self.file_naming_format = QtGui.QLineEdit(self.rename_files)
        self.file_naming_format.setObjectName("file_naming_format")
        self.gridlayout.addWidget(self.file_naming_format,1,0,1,1)

        self.label_4 = QtGui.QLabel(self.rename_files)
        self.label_4.setObjectName("label_4")
        self.gridlayout.addWidget(self.label_4,2,0,1,2)

        self.label_3 = QtGui.QLabel(self.rename_files)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3,0,0,1,2)
        self.vboxlayout.addWidget(self.rename_files)

        self.move_files = QtGui.QGroupBox(Form)
        self.move_files.setCheckable(True)
        self.move_files.setObjectName("move_files")

        self.gridlayout1 = QtGui.QGridLayout(self.move_files)
        self.gridlayout1.setMargin(9)
        self.gridlayout1.setSpacing(2)
        self.gridlayout1.setObjectName("gridlayout1")

        self.pushButton = QtGui.QPushButton(self.move_files)
        self.pushButton.setObjectName("pushButton")
        self.gridlayout1.addWidget(self.pushButton,1,1,1,1)

        self.directory = QtGui.QLineEdit(self.move_files)
        self.directory.setObjectName("directory")
        self.gridlayout1.addWidget(self.directory,1,0,1,1)

        self.label_2 = QtGui.QLabel(self.move_files)
        self.label_2.setObjectName("label_2")
        self.gridlayout1.addWidget(self.label_2,0,0,1,2)
        self.vboxlayout.addWidget(self.move_files)

        spacerItem = QtGui.QSpacerItem(21,101,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_4.setBuddy(self.va_file_naming_format)
        self.label_3.setBuddy(self.file_naming_format)
        self.label_2.setBuddy(self.directory)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.file_naming_format,self.file_naming_format_default)
        Form.setTabOrder(self.file_naming_format_default,self.va_file_naming_format)
        Form.setTabOrder(self.va_file_naming_format,self.va_file_naming_format_default)
        Form.setTabOrder(self.va_file_naming_format_default,self.windows_compatible_filenames)
        Form.setTabOrder(self.windows_compatible_filenames,self.ascii_filenames)
        Form.setTabOrder(self.ascii_filenames,self.directory)
        Form.setTabOrder(self.directory,self.pushButton)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_("Form"))
        self.rename_files.setTitle(_("Rename Files"))
        self.windows_compatible_filenames.setText(_("Replace Windows-incompatible characters"))
        self.ascii_filenames.setText(_("Replace non-ASCII characters"))
        self.va_file_naming_format_default.setText(_("Default"))
        self.file_naming_format_default.setText(_("Default"))
        self.label_4.setText(_("Various artists file naming format:"))
        self.label_3.setText(_("File naming format:"))
        self.move_files.setTitle(_("Move Files"))
        self.pushButton.setText(_("Browse"))
        self.label_2.setText(_("Move tagged files to this directory:"))
