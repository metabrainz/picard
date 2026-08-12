# Form implementation generated from reading ui file 'ui/options_advanced.ui'
#
# Created by: PyQt6 UI code generator 6.11.0
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_AdvancedOptionsPage(object):
    def setupUi(self, AdvancedOptionsPage):
        AdvancedOptionsPage.setObjectName("AdvancedOptionsPage")
        AdvancedOptionsPage.resize(570, 455)
        self.vboxlayout = QtWidgets.QVBoxLayout(AdvancedOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.groupBox = QtWidgets.QGroupBox(parent=AdvancedOptionsPage)
        self.groupBox.setObjectName("groupBox")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.groupBox)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.recursively_add_files = QtWidgets.QCheckBox(parent=self.groupBox)
        self.recursively_add_files.setObjectName("recursively_add_files")
        self.vboxlayout1.addWidget(self.recursively_add_files)
        self.ignore_hidden_files = QtWidgets.QCheckBox(parent=self.groupBox)
        self.ignore_hidden_files.setObjectName("ignore_hidden_files")
        self.vboxlayout1.addWidget(self.ignore_hidden_files)
        self.label_ignore_regex = QtWidgets.QLabel(parent=self.groupBox)
        self.label_ignore_regex.setWordWrap(True)
        self.label_ignore_regex.setObjectName("label_ignore_regex")
        self.vboxlayout1.addWidget(self.label_ignore_regex)
        self.ignore_regex = QtWidgets.QLineEdit(parent=self.groupBox)
        self.ignore_regex.setObjectName("ignore_regex")
        self.vboxlayout1.addWidget(self.ignore_regex)
        self.vboxlayout.addWidget(self.groupBox)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_ignore_regex.setBuddy(self.ignore_regex)

        self.retranslateUi(AdvancedOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(AdvancedOptionsPage)
        AdvancedOptionsPage.setTabOrder(self.recursively_add_files, self.ignore_hidden_files)
        AdvancedOptionsPage.setTabOrder(self.ignore_hidden_files, self.ignore_regex)

    def retranslateUi(self, AdvancedOptionsPage):
        self.groupBox.setTitle(_("Advanced options"))
        self.recursively_add_files.setText(_("Include sub-folders when adding files from folder"))
        self.ignore_hidden_files.setText(_("Ignore hidden files"))
        self.label_ignore_regex.setText(_("Ignore file paths matching the following regular expression:"))
