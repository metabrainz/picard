# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_colors.ui'
#
# Created: Thu Jul  4 22:11:05 2013
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
        ColorsOptionsPage.resize(719, 267)
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
        self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 0, 699, 136))
        self.gridLayoutWidget.setObjectName(_fromUtf8("gridLayoutWidget"))
        self.gridLayout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.scrollArea.setWidget(self.gridLayoutWidget)
        self.verticalLayout.addWidget(self.scrollArea)
        spacerItem = QtGui.QSpacerItem(20, 80, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.disclaimer = QtGui.QLabel(ColorsOptionsPage)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.disclaimer.setFont(font)
        self.disclaimer.setFrameShape(QtGui.QFrame.StyledPanel)
        self.disclaimer.setAlignment(QtCore.Qt.AlignCenter)
        self.disclaimer.setObjectName(_fromUtf8("disclaimer"))
        self.verticalLayout_2.addWidget(self.disclaimer)
        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.retranslateUi(ColorsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ColorsOptionsPage)

    def retranslateUi(self, ColorsOptionsPage):
        self.disclaimer.setText(_("Changes here may not take effect until Picard is restarted."))

