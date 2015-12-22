# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CDLookupOptionsPage(object):
    def setupUi(self, CDLookupOptionsPage):
        CDLookupOptionsPage.setObjectName("CDLookupOptionsPage")
        CDLookupOptionsPage.resize(255, 155)
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
        self.cd_lookup_ = QtWidgets.QLabel(self.rename_files)
        self.cd_lookup_.setObjectName("cd_lookup_")
        self.gridlayout.addWidget(self.cd_lookup_, 0, 0, 1, 1)
        self.hboxlayout = QtWidgets.QHBoxLayout()
        self.hboxlayout.setContentsMargins(0, 0, 0, 0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")
        self.cd_lookup_device = QtWidgets.QComboBox(self.rename_files)
        self.cd_lookup_device.setObjectName("cd_lookup_device")
        self.hboxlayout.addWidget(self.cd_lookup_device)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.gridlayout.addLayout(self.hboxlayout, 1, 0, 1, 1)
        self.vboxlayout.addWidget(self.rename_files)
        spacerItem1 = QtWidgets.QSpacerItem(161, 81, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)
        self.cd_lookup_.setBuddy(self.cd_lookup_device)

        self.retranslateUi(CDLookupOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CDLookupOptionsPage)

    def retranslateUi(self, CDLookupOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.rename_files.setTitle(_("CD Lookup"))
        self.cd_lookup_.setText(_("Default CD-ROM drive to use for lookups:"))

