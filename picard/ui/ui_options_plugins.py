# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_plugins.ui'
#
# Created: Sun Aug  5 10:53:07 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_PluginsOptionsPage(object):
    def setupUi(self, PluginsOptionsPage):
        PluginsOptionsPage.setObjectName("PluginsOptionsPage")
        PluginsOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,265,297).size()).expandedTo(PluginsOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(PluginsOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.splitter = QtGui.QSplitter(PluginsOptionsPage)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")

        self.groupBox_2 = QtGui.QGroupBox(self.splitter)
        self.groupBox_2.setObjectName("groupBox_2")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox_2)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.plugins = QtGui.QTreeWidget(self.groupBox_2)
        self.plugins.setRootIsDecorated(False)
        self.plugins.setObjectName("plugins")
        self.vboxlayout1.addWidget(self.plugins)

        self.groupBox = QtGui.QGroupBox(self.splitter)
        self.groupBox.setObjectName("groupBox")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.details = QtGui.QLabel(self.groupBox)
        self.details.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.details.setWordWrap(True)
        self.details.setObjectName("details")
        self.vboxlayout2.addWidget(self.details)
        self.vboxlayout.addWidget(self.splitter)

        self.retranslateUi(PluginsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(PluginsOptionsPage)

    def retranslateUi(self, PluginsOptionsPage):
        self.groupBox_2.setTitle(_(u"Plugins"))
        self.plugins.headerItem().setText(0,_(u"Name"))
        self.plugins.headerItem().setText(1,_(u"Author"))
        self.plugins.headerItem().setText(2,_(u"Version"))
        self.groupBox.setTitle(_(u"Details"))

