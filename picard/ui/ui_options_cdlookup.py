# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_cdlookup.ui'
#
# Created: Sun Jan 28 12:31:42 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_CDLookupOptionsPage(object):
    def setupUi(self, CDLookupOptionsPage):
        CDLookupOptionsPage.setObjectName("CDLookupOptionsPage")
        CDLookupOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,224,176).size()).expandedTo(CDLookupOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(CDLookupOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.rename_files = QtGui.QGroupBox(CDLookupOptionsPage)
        self.rename_files.setObjectName("rename_files")

        self.gridlayout = QtGui.QGridLayout(self.rename_files)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        self.cd_lookup_device = QtGui.QLineEdit(self.rename_files)
        self.cd_lookup_device.setObjectName("cd_lookup_device")
        self.gridlayout.addWidget(self.cd_lookup_device,1,0,1,1)

        self.label_3 = QtGui.QLabel(self.rename_files)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3,0,0,1,1)
        self.vboxlayout.addWidget(self.rename_files)

        spacerItem = QtGui.QSpacerItem(161,81,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_3.setBuddy(self.cd_lookup_device)

        self.retranslateUi(CDLookupOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CDLookupOptionsPage)

    def retranslateUi(self, CDLookupOptionsPage):
        self.rename_files.setTitle(_(u"CD Lookup"))
        self.label_3.setText(_(u"CD-ROM device to use for lookups:"))

