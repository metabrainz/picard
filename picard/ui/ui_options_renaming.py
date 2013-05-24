# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\options_renaming.ui'
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

class Ui_RenamingOptionsPage(object):
    def setupUi(self, RenamingOptionsPage):
        RenamingOptionsPage.setObjectName(_fromUtf8("RenamingOptionsPage"))
        RenamingOptionsPage.setEnabled(True)
        RenamingOptionsPage.resize(453, 421)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RenamingOptionsPage.sizePolicy().hasHeightForWidth())
        RenamingOptionsPage.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QtGui.QVBoxLayout(RenamingOptionsPage)
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.rename_files = QtGui.QCheckBox(RenamingOptionsPage)
        self.rename_files.setObjectName(_fromUtf8("rename_files"))
        self.verticalLayout_5.addWidget(self.rename_files)
        self.ascii_filenames = QtGui.QCheckBox(RenamingOptionsPage)
        self.ascii_filenames.setObjectName(_fromUtf8("ascii_filenames"))
        self.verticalLayout_5.addWidget(self.ascii_filenames)
        self.windows_compatible_filenames = QtGui.QCheckBox(RenamingOptionsPage)
        self.windows_compatible_filenames.setObjectName(_fromUtf8("windows_compatible_filenames"))
        self.verticalLayout_5.addWidget(self.windows_compatible_filenames)
        self.move_files = QtGui.QCheckBox(RenamingOptionsPage)
        self.move_files.setObjectName(_fromUtf8("move_files"))
        self.verticalLayout_5.addWidget(self.move_files)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.move_files_to = QtGui.QLineEdit(RenamingOptionsPage)
        self.move_files_to.setEnabled(False)
        self.move_files_to.setObjectName(_fromUtf8("move_files_to"))
        self.horizontalLayout_4.addWidget(self.move_files_to)
        self.move_files_to_browse = QtGui.QPushButton(RenamingOptionsPage)
        self.move_files_to_browse.setEnabled(False)
        self.move_files_to_browse.setObjectName(_fromUtf8("move_files_to_browse"))
        self.horizontalLayout_4.addWidget(self.move_files_to_browse)
        self.verticalLayout_5.addLayout(self.horizontalLayout_4)
        self.delete_empty_dirs = QtGui.QCheckBox(RenamingOptionsPage)
        self.delete_empty_dirs.setEnabled(False)
        self.delete_empty_dirs.setObjectName(_fromUtf8("delete_empty_dirs"))
        self.verticalLayout_5.addWidget(self.delete_empty_dirs)
        self.move_additional_files = QtGui.QCheckBox(RenamingOptionsPage)
        self.move_additional_files.setEnabled(False)
        self.move_additional_files.setObjectName(_fromUtf8("move_additional_files"))
        self.verticalLayout_5.addWidget(self.move_additional_files)
        self.move_additional_files_pattern = QtGui.QLineEdit(RenamingOptionsPage)
        self.move_additional_files_pattern.setEnabled(False)
        self.move_additional_files_pattern.setObjectName(_fromUtf8("move_additional_files_pattern"))
        self.verticalLayout_5.addWidget(self.move_additional_files_pattern)
        self.groupBox_2 = QtGui.QGroupBox(RenamingOptionsPage)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.file_naming_format = QtGui.QTextEdit(self.groupBox_2)
        self.file_naming_format.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.file_naming_format.sizePolicy().hasHeightForWidth())
        self.file_naming_format.setSizePolicy(sizePolicy)
        self.file_naming_format.setMinimumSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Monospace"))
        self.file_naming_format.setFont(font)
        self.file_naming_format.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.file_naming_format.setTabChangesFocus(False)
        self.file_naming_format.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.file_naming_format.setTabStopWidth(20)
        self.file_naming_format.setAcceptRichText(True)
        self.file_naming_format.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.file_naming_format.setObjectName(_fromUtf8("file_naming_format"))
        self.verticalLayout_2.addWidget(self.file_naming_format)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.renaming_error = QtGui.QLabel(self.groupBox_2)
        self.renaming_error.setText(_fromUtf8(""))
        self.renaming_error.setAlignment(QtCore.Qt.AlignCenter)
        self.renaming_error.setObjectName(_fromUtf8("renaming_error"))
        self.horizontalLayout.addWidget(self.renaming_error)
        self.file_naming_format_default = QtGui.QPushButton(self.groupBox_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.file_naming_format_default.sizePolicy().hasHeightForWidth())
        self.file_naming_format_default.setSizePolicy(sizePolicy)
        self.file_naming_format_default.setMinimumSize(QtCore.QSize(0, 0))
        self.file_naming_format_default.setObjectName(_fromUtf8("file_naming_format_default"))
        self.horizontalLayout.addWidget(self.file_naming_format_default)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout_5.addWidget(self.groupBox_2)
        self.groupBox = QtGui.QGroupBox(RenamingOptionsPage)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout.setContentsMargins(2, 0, 2, 0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.example_filename = QtGui.QLabel(self.groupBox)
        self.example_filename.setText(_fromUtf8(""))
        self.example_filename.setTextFormat(QtCore.Qt.RichText)
        self.example_filename.setWordWrap(True)
        self.example_filename.setObjectName(_fromUtf8("example_filename"))
        self.verticalLayout.addWidget(self.example_filename)
        self.example_filename_va = QtGui.QLabel(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.example_filename_va.sizePolicy().hasHeightForWidth())
        self.example_filename_va.setSizePolicy(sizePolicy)
        self.example_filename_va.setText(_fromUtf8(""))
        self.example_filename_va.setWordWrap(True)
        self.example_filename_va.setObjectName(_fromUtf8("example_filename_va"))
        self.verticalLayout.addWidget(self.example_filename_va)
        self.verticalLayout_5.addWidget(self.groupBox)

        self.retranslateUi(RenamingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(RenamingOptionsPage)

    def retranslateUi(self, RenamingOptionsPage):
        self.rename_files.setText(_("Rename files when saving"))
        self.ascii_filenames.setText(_("Replace non-ASCII characters"))
        self.windows_compatible_filenames.setText(_("Replace Windows-incompatible characters"))
        self.move_files.setText(_("Move files to this directory when saving:"))
        self.move_files_to_browse.setText(_("Browse..."))
        self.delete_empty_dirs.setText(_("Delete empty directories"))
        self.move_additional_files.setText(_("Move additional files:"))
        self.groupBox_2.setTitle(_("Name files like this"))
        self.file_naming_format.setHtml(_translate("RenamingOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Monospace\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:10pt;\"><br /></p></body></html>", None))
        self.file_naming_format_default.setText(_("Default"))
        self.groupBox.setTitle(_("Examples"))

