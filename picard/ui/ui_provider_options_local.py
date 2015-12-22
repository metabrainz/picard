# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LocalOptions(object):
    def setupUi(self, LocalOptions):
        LocalOptions.setObjectName("LocalOptions")
        LocalOptions.resize(472, 215)
        self.verticalLayout = QtWidgets.QVBoxLayout(LocalOptions)
        self.verticalLayout.setObjectName("verticalLayout")
        self.local_cover_regex_label = QtWidgets.QLabel(LocalOptions)
        self.local_cover_regex_label.setObjectName("local_cover_regex_label")
        self.verticalLayout.addWidget(self.local_cover_regex_label)
        self.local_cover_regex_edit = QtWidgets.QLineEdit(LocalOptions)
        self.local_cover_regex_edit.setObjectName("local_cover_regex_edit")
        self.verticalLayout.addWidget(self.local_cover_regex_edit)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.local_cover_regex_error = QtWidgets.QLabel(LocalOptions)
        self.local_cover_regex_error.setText("")
        self.local_cover_regex_error.setObjectName("local_cover_regex_error")
        self.horizontalLayout_2.addWidget(self.local_cover_regex_error)
        self.local_cover_regex_default = QtWidgets.QPushButton(LocalOptions)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.local_cover_regex_default.sizePolicy().hasHeightForWidth())
        self.local_cover_regex_default.setSizePolicy(sizePolicy)
        self.local_cover_regex_default.setObjectName("local_cover_regex_default")
        self.horizontalLayout_2.addWidget(self.local_cover_regex_default)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.note = QtWidgets.QLabel(LocalOptions)
        font = QtGui.QFont()
        font.setItalic(True)
        self.note.setFont(font)
        self.note.setWordWrap(True)
        self.note.setObjectName("note")
        self.verticalLayout.addWidget(self.note)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(LocalOptions)
        QtCore.QMetaObject.connectSlotsByName(LocalOptions)

    def retranslateUi(self, LocalOptions):
        _translate = QtCore.QCoreApplication.translate
        LocalOptions.setWindowTitle(_("Form"))
        self.local_cover_regex_label.setText(_("Local cover art files match the following regular expression:"))
        self.local_cover_regex_default.setText(_("Default"))
        self.note.setText(_("First group in the regular expression, if any, will be used as type, ie. cover-back-spine.jpg will be set as types Back + Spine. If no type is found, it will default to Front type."))

