# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_colors.ui'
#
# Created: Thu Jul  4 13:04:07 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ColorsOptionsPage(object):
    def setupUi(self, ColorsOptionsPage):
        ColorsOptionsPage.setObjectName(_fromUtf8("ColorsOptionsPage"))
        ColorsOptionsPage.resize(102, 108)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(ColorsOptionsPage.sizePolicy().hasHeightForWidth())
        ColorsOptionsPage.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(ColorsOptionsPage)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.scrollArea = QtGui.QScrollArea(ColorsOptionsPage)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.gridLayoutWidget = QtGui.QWidget()
        self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 0, 82, 82))
        self.gridLayoutWidget.setObjectName(_fromUtf8("gridLayoutWidget"))
        self.gridLayout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.scrollArea.setWidget(self.gridLayoutWidget)
        self.verticalLayout.addWidget(self.scrollArea)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(ColorsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ColorsOptionsPage)

    def retranslateUi(self, ColorsOptionsPage):
        pass

