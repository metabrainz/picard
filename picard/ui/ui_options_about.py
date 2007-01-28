# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_about.ui'
#
# Created: Sun Jan 28 11:25:55 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_AboutOptionsPage(object):
    def setupUi(self, AboutOptionsPage):
        AboutOptionsPage.setObjectName("AboutOptionsPage")
        AboutOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,171,137).size()).expandedTo(AboutOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(AboutOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.label = QtGui.QLabel(AboutOptionsPage)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.vboxlayout.addWidget(self.label)

        spacerItem = QtGui.QSpacerItem(20,51,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(AboutOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(AboutOptionsPage)

    def retranslateUi(self, AboutOptionsPage):
        pass

