# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_interface.ui'
#
# Created: Mon Apr 30 08:20:14 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_InterfaceOptionsPage(object):
    def setupUi(self, InterfaceOptionsPage):
        InterfaceOptionsPage.setObjectName("InterfaceOptionsPage")
        InterfaceOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,238,216).size()).expandedTo(InterfaceOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(InterfaceOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.groupBox_2 = QtGui.QGroupBox(InterfaceOptionsPage)
        self.groupBox_2.setObjectName("groupBox_2")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox_2)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.toolbar_show_labels = QtGui.QCheckBox(self.groupBox_2)
        self.toolbar_show_labels.setObjectName("toolbar_show_labels")
        self.vboxlayout1.addWidget(self.toolbar_show_labels)
        self.vboxlayout.addWidget(self.groupBox_2)

        spacerItem = QtGui.QSpacerItem(181,21,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(InterfaceOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(InterfaceOptionsPage)

    def retranslateUi(self, InterfaceOptionsPage):
        self.groupBox_2.setTitle(_(u"Toolbar"))
        self.toolbar_show_labels.setText(_(u"Show text labels under icons"))

