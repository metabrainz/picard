# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_about.ui'
#
# Created: Wed Nov 26 21:41:46 2008
#      by: PyQt4 UI code generator 4.4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_AboutOptionsPage(object):
    def setupUi(self, AboutOptionsPage):
        AboutOptionsPage.setObjectName("AboutOptionsPage")
        AboutOptionsPage.resize(171, 137)
        self.vboxlayout = QtGui.QVBoxLayout(AboutOptionsPage)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setObjectName("vboxlayout")
        self.scrollArea = QtGui.QScrollArea(AboutOptionsPage)
        self.scrollArea.setFrameShape(QtGui.QFrame.NoFrame)
        self.scrollArea.setFrameShadow(QtGui.QFrame.Plain)
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtGui.QWidget(self.scrollArea)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 171, 137))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setMargin(9)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.label.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.vboxlayout.addWidget(self.scrollArea)

        self.retranslateUi(AboutOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(AboutOptionsPage)

    def retranslateUi(self, AboutOptionsPage):
        pass

