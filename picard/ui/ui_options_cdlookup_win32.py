# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_cdlookup_win32.ui'
#
# Created: Sun Jan 13 17:42:14 2008
#      by: PyQt4 UI code generator 4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_CDLookupOptionsPage(object):
    def setupUi(self, CDLookupOptionsPage):
        CDLookupOptionsPage.setObjectName("CDLookupOptionsPage")
        CDLookupOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,255,155).size()).expandedTo(CDLookupOptionsPage.minimumSizeHint()))

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

        self.cd_lookup_ = QtGui.QLabel(self.rename_files)
        self.cd_lookup_.setObjectName("cd_lookup_")
        self.gridlayout.addWidget(self.cd_lookup_,0,0,1,1)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.cd_lookup_device = QtGui.QComboBox(self.rename_files)
        self.cd_lookup_device.setObjectName("cd_lookup_device")
        self.hboxlayout.addWidget(self.cd_lookup_device)

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.gridlayout.addLayout(self.hboxlayout,1,0,1,1)
        self.vboxlayout.addWidget(self.rename_files)

        spacerItem1 = QtGui.QSpacerItem(161,81,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)
        self.cd_lookup_.setBuddy(self.cd_lookup_device)

        self.retranslateUi(CDLookupOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CDLookupOptionsPage)

    def retranslateUi(self, CDLookupOptionsPage):
        self.rename_files.setTitle(_("CD Lookup"))
        self.cd_lookup_.setText(_("Default CD-ROM drive to use for lookups:"))

