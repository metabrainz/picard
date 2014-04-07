# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_AdvancedOptionsPage(object):
    def setupUi(self, AdvancedOptionsPage):
        AdvancedOptionsPage.setObjectName(_fromUtf8("AdvancedOptionsPage"))
        AdvancedOptionsPage.resize(338, 435)
        self.vboxlayout = QtGui.QVBoxLayout(AdvancedOptionsPage)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.groupBox = QtGui.QGroupBox(AdvancedOptionsPage)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridlayout = QtGui.QGridLayout(self.groupBox)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.label_ignore_regex = QtGui.QLabel(self.groupBox)
        self.label_ignore_regex.setObjectName(_fromUtf8("label_ignore_regex"))
        self.gridlayout.addWidget(self.label_ignore_regex, 1, 0, 1, 1)
        self.ignore_regex = QtGui.QLineEdit(self.groupBox)
        self.ignore_regex.setObjectName(_fromUtf8("ignore_regex"))
        self.gridlayout.addWidget(self.ignore_regex, 2, 0, 1, 1)
        self.regex_error = QtGui.QLabel(self.groupBox)
        self.regex_error.setText(_fromUtf8(""))
        self.regex_error.setObjectName(_fromUtf8("regex_error"))
        self.gridlayout.addWidget(self.regex_error, 3, 0, 1, 1)
        self.vboxlayout.addWidget(self.groupBox)
        spacerItem = QtGui.QSpacerItem(181, 21, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(AdvancedOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(AdvancedOptionsPage)

    def retranslateUi(self, AdvancedOptionsPage):
        self.groupBox.setTitle(_("Advanced options"))
        self.label_ignore_regex.setText(_("Ignore file paths matching the following regular expression:"))

