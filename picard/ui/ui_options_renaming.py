# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_renaming.ui'
#
# Created: Sun Jan 13 22:20:39 2008
#      by: PyQt4 UI code generator 4.3.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_RenamingOptionsPage(object):
    def setupUi(self, RenamingOptionsPage):
        RenamingOptionsPage.setObjectName("RenamingOptionsPage")
        RenamingOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,621,718).size()).expandedTo(RenamingOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(RenamingOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")

        self.rename_files = QtGui.QGroupBox(RenamingOptionsPage)
        self.rename_files.setCheckable(True)
        self.rename_files.setObjectName("rename_files")

        self.gridlayout = QtGui.QGridLayout(self.rename_files)
        self.gridlayout.setObjectName("gridlayout")

        self.label_3 = QtGui.QLabel(self.rename_files)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3,0,0,1,1)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName("hboxlayout")

        self.file_naming_format = QtGui.QTextEdit(self.rename_files)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.file_naming_format.sizePolicy().hasHeightForWidth())
        self.file_naming_format.setSizePolicy(sizePolicy)
        self.file_naming_format.setMinimumSize(QtCore.QSize(0,0))
        self.file_naming_format.setCursor(QtCore.Qt.IBeamCursor)
        self.file_naming_format.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.file_naming_format.setTabStopWidth(20)
        self.file_naming_format.setObjectName("file_naming_format")
        self.hboxlayout.addWidget(self.file_naming_format)

        self.vboxlayout1 = QtGui.QVBoxLayout()
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.file_naming_format_default = QtGui.QPushButton(self.rename_files)
        self.file_naming_format_default.setObjectName("file_naming_format_default")
        self.vboxlayout1.addWidget(self.file_naming_format_default)

        spacerItem = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout1.addItem(spacerItem)
        self.hboxlayout.addLayout(self.vboxlayout1)
        self.gridlayout.addLayout(self.hboxlayout,1,0,1,1)

        self.windows_compatible_filenames = QtGui.QCheckBox(self.rename_files)
        self.windows_compatible_filenames.setObjectName("windows_compatible_filenames")
        self.gridlayout.addWidget(self.windows_compatible_filenames,2,0,1,1)

        self.ascii_filenames = QtGui.QCheckBox(self.rename_files)
        self.ascii_filenames.setObjectName("ascii_filenames")
        self.gridlayout.addWidget(self.ascii_filenames,3,0,1,1)

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.label = QtGui.QLabel(self.rename_files)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.hboxlayout1.addWidget(self.label)

        self.example_filename = QtGui.QLabel(self.rename_files)

        font = QtGui.QFont()
        font.setWeight(75)
        font.setItalic(False)
        font.setBold(True)
        self.example_filename.setFont(font)
        self.example_filename.setFrameShape(QtGui.QFrame.StyledPanel)
        self.example_filename.setFrameShadow(QtGui.QFrame.Plain)
        self.example_filename.setTextFormat(QtCore.Qt.PlainText)
        self.example_filename.setWordWrap(True)
        self.example_filename.setObjectName("example_filename")
        self.hboxlayout1.addWidget(self.example_filename)
        self.gridlayout.addLayout(self.hboxlayout1,4,0,1,1)

        self.use_va_format = QtGui.QGroupBox(self.rename_files)
        self.use_va_format.setCheckable(True)
        self.use_va_format.setObjectName("use_va_format")

        self.gridlayout1 = QtGui.QGridLayout(self.use_va_format)
        self.gridlayout1.setObjectName("gridlayout1")

        self.label_4 = QtGui.QLabel(self.use_va_format)
        self.label_4.setObjectName("label_4")
        self.gridlayout1.addWidget(self.label_4,0,0,1,1)

        self.hboxlayout2 = QtGui.QHBoxLayout()
        self.hboxlayout2.setObjectName("hboxlayout2")

        self.va_file_naming_format = QtGui.QTextEdit(self.use_va_format)
        self.va_file_naming_format.setCursor(QtCore.Qt.IBeamCursor)
        self.va_file_naming_format.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.va_file_naming_format.setTabStopWidth(20)
        self.va_file_naming_format.setObjectName("va_file_naming_format")
        self.hboxlayout2.addWidget(self.va_file_naming_format)

        self.vboxlayout2 = QtGui.QVBoxLayout()
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.va_file_naming_format_default = QtGui.QPushButton(self.use_va_format)
        self.va_file_naming_format_default.setObjectName("va_file_naming_format_default")
        self.vboxlayout2.addWidget(self.va_file_naming_format_default)

        self.va_copy_from_above = QtGui.QPushButton(self.use_va_format)
        self.va_copy_from_above.setObjectName("va_copy_from_above")
        self.vboxlayout2.addWidget(self.va_copy_from_above)

        spacerItem1 = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout2.addItem(spacerItem1)
        self.hboxlayout2.addLayout(self.vboxlayout2)
        self.gridlayout1.addLayout(self.hboxlayout2,1,0,1,1)

        self.hboxlayout3 = QtGui.QHBoxLayout()
        self.hboxlayout3.setObjectName("hboxlayout3")

        self.label_5 = QtGui.QLabel(self.use_va_format)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName("label_5")
        self.hboxlayout3.addWidget(self.label_5)

        self.example_va_filename = QtGui.QLabel(self.use_va_format)

        font = QtGui.QFont()
        font.setWeight(75)
        font.setItalic(False)
        font.setBold(True)
        self.example_va_filename.setFont(font)
        self.example_va_filename.setFrameShape(QtGui.QFrame.StyledPanel)
        self.example_va_filename.setTextFormat(QtCore.Qt.PlainText)
        self.example_va_filename.setWordWrap(True)
        self.example_va_filename.setObjectName("example_va_filename")
        self.hboxlayout3.addWidget(self.example_va_filename)
        self.gridlayout1.addLayout(self.hboxlayout3,2,0,1,1)
        self.gridlayout.addWidget(self.use_va_format,6,0,1,1)

        spacerItem2 = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem2,5,0,1,1)
        self.vboxlayout.addWidget(self.rename_files)

        self.retranslateUi(RenamingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(RenamingOptionsPage)

    def retranslateUi(self, RenamingOptionsPage):
        RenamingOptionsPage.setWindowTitle(_("Form"))
        self.rename_files.setTitle(_("Rename Files"))
        self.label_3.setText(_("File naming format:"))
        self.file_naming_format_default.setText(_("Default"))
        self.windows_compatible_filenames.setText(_("Replace Windows-incompatible characters"))
        self.ascii_filenames.setText(_("Replace non-ASCII characters"))
        self.label.setText(_("Preview: "))
        self.use_va_format.setTitle(_("Format multiple artists releases differently"))
        self.label_4.setText(_("Multiple artist file naming format:"))
        self.va_file_naming_format_default.setText(_("Default"))
        self.va_copy_from_above.setText(_("Copy from above"))
        self.label_5.setText(_("Preview: "))

