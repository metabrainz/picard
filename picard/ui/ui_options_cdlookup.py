# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_cdlookup.ui'
#
# Created: Tue May 29 19:44:15 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_CDLookupOptionsPage(object):
    def setupUi(self, CDLookupOptionsPage):
        CDLookupOptionsPage.setObjectName(_fromUtf8("CDLookupOptionsPage"))
        CDLookupOptionsPage.resize(224, 176)
        self.vboxlayout = QtGui.QVBoxLayout(CDLookupOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.rename_files = QtGui.QGroupBox(CDLookupOptionsPage)
        self.rename_files.setObjectName(_fromUtf8("rename_files"))
        self.gridlayout = QtGui.QGridLayout(self.rename_files)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.cd_lookup_device = QtGui.QLineEdit(self.rename_files)
        self.cd_lookup_device.setObjectName(_fromUtf8("cd_lookup_device"))
        self.gridlayout.addWidget(self.cd_lookup_device, 1, 0, 1, 1)
        self.label_3 = QtGui.QLabel(self.rename_files)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridlayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.vboxlayout.addWidget(self.rename_files)
        spacerItem = QtGui.QSpacerItem(161, 81, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_3.setBuddy(self.cd_lookup_device)

        self.retranslateUi(CDLookupOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CDLookupOptionsPage)

    def retranslateUi(self, CDLookupOptionsPage):
        self.rename_files.setTitle(_("CD Lookup"))
        self.label_3.setText(_("CD-ROM device to use for lookups:"))

