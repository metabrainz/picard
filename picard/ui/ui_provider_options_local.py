# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

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

class Ui_LocalOptions(object):
    def setupUi(self, LocalOptions):
        LocalOptions.setObjectName(_fromUtf8("LocalOptions"))
        LocalOptions.resize(472, 215)
        self.verticalLayout = QtGui.QVBoxLayout(LocalOptions)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.local_cover_regex_label = QtGui.QLabel(LocalOptions)
        self.local_cover_regex_label.setObjectName(_fromUtf8("local_cover_regex_label"))
        self.verticalLayout.addWidget(self.local_cover_regex_label)
        self.local_cover_regex_edit = QtGui.QLineEdit(LocalOptions)
        self.local_cover_regex_edit.setObjectName(_fromUtf8("local_cover_regex_edit"))
        self.verticalLayout.addWidget(self.local_cover_regex_edit)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.local_cover_regex_error = QtGui.QLabel(LocalOptions)
        self.local_cover_regex_error.setText(_fromUtf8(""))
        self.local_cover_regex_error.setObjectName(_fromUtf8("local_cover_regex_error"))
        self.horizontalLayout_2.addWidget(self.local_cover_regex_error)
        self.local_cover_regex_default = QtGui.QPushButton(LocalOptions)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.local_cover_regex_default.sizePolicy().hasHeightForWidth())
        self.local_cover_regex_default.setSizePolicy(sizePolicy)
        self.local_cover_regex_default.setObjectName(_fromUtf8("local_cover_regex_default"))
        self.horizontalLayout_2.addWidget(self.local_cover_regex_default)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.note = QtGui.QLabel(LocalOptions)
        font = QtGui.QFont()
        font.setItalic(True)
        self.note.setFont(font)
        self.note.setWordWrap(True)
        self.note.setObjectName(_fromUtf8("note"))
        self.verticalLayout.addWidget(self.note)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(LocalOptions)
        QtCore.QMetaObject.connectSlotsByName(LocalOptions)

    def retranslateUi(self, LocalOptions):
        LocalOptions.setWindowTitle(_("Form"))
        self.local_cover_regex_label.setText(_("Local cover art files match the following regular expression:"))
        self.local_cover_regex_default.setText(_("Default"))
        self.note.setText(_("First group in the regular expression, if any, will be used as type, ie. cover-back-spine.jpg will be set as types Back + Spine. If no type is found, it will default to Front type."))

