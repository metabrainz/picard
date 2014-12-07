# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CDLookupOptionsPage(object):
    def setupUi(self, CDLookupOptionsPage):
        CDLookupOptionsPage.setObjectName("CDLookupOptionsPage")
        CDLookupOptionsPage.resize(224, 176)
        self.vboxlayout = QtWidgets.QVBoxLayout(CDLookupOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.rename_files = QtWidgets.QGroupBox(CDLookupOptionsPage)
        self.rename_files.setObjectName("rename_files")
        self.gridlayout = QtWidgets.QGridLayout(self.rename_files)
        self.gridlayout.setContentsMargins(9, 9, 9, 9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")
        self.cd_lookup_device = QtWidgets.QLineEdit(self.rename_files)
        self.cd_lookup_device.setObjectName("cd_lookup_device")
        self.gridlayout.addWidget(self.cd_lookup_device, 1, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.rename_files)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.vboxlayout.addWidget(self.rename_files)
        spacerItem = QtWidgets.QSpacerItem(161, 81, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_3.setBuddy(self.cd_lookup_device)

        self.retranslateUi(CDLookupOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CDLookupOptionsPage)

    def retranslateUi(self, CDLookupOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.rename_files.setTitle(_("CD Lookup"))
        self.label_3.setText(_("CD-ROM device to use for lookups:"))

