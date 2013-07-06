# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/infostatus.ui'
#
# Created: Thu Jun 27 19:18:14 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_InfoStatus(object):
    def setupUi(self, InfoStatus):
        InfoStatus.setObjectName(_fromUtf8("InfoStatus"))
        InfoStatus.resize(350, 24)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(InfoStatus.sizePolicy().hasHeightForWidth())
        InfoStatus.setSizePolicy(sizePolicy)
        InfoStatus.setMinimumSize(QtCore.QSize(0, 0))
        self.horizontalLayout = QtGui.QHBoxLayout(InfoStatus)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.val1 = QtGui.QLabel(InfoStatus)
        self.val1.setMinimumSize(QtCore.QSize(40, 0))
        self.val1.setText(_fromUtf8(""))
        self.val1.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.val1.setObjectName(_fromUtf8("val1"))
        self.horizontalLayout.addWidget(self.val1)
        self.label1 = QtGui.QLabel(InfoStatus)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label1.sizePolicy().hasHeightForWidth())
        self.label1.setSizePolicy(sizePolicy)
        self.label1.setFrameShape(QtGui.QFrame.NoFrame)
        self.label1.setTextFormat(QtCore.Qt.AutoText)
        self.label1.setScaledContents(False)
        self.label1.setMargin(1)
        self.label1.setObjectName(_fromUtf8("label1"))
        self.horizontalLayout.addWidget(self.label1)
        self.val2 = QtGui.QLabel(InfoStatus)
        self.val2.setMinimumSize(QtCore.QSize(40, 0))
        self.val2.setText(_fromUtf8(""))
        self.val2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.val2.setObjectName(_fromUtf8("val2"))
        self.horizontalLayout.addWidget(self.val2)
        self.label2 = QtGui.QLabel(InfoStatus)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label2.sizePolicy().hasHeightForWidth())
        self.label2.setSizePolicy(sizePolicy)
        self.label2.setText(_fromUtf8(""))
        self.label2.setObjectName(_fromUtf8("label2"))
        self.horizontalLayout.addWidget(self.label2)
        self.val3 = QtGui.QLabel(InfoStatus)
        self.val3.setMinimumSize(QtCore.QSize(40, 0))
        self.val3.setText(_fromUtf8(""))
        self.val3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.val3.setObjectName(_fromUtf8("val3"))
        self.horizontalLayout.addWidget(self.val3)
        self.label3 = QtGui.QLabel(InfoStatus)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label3.sizePolicy().hasHeightForWidth())
        self.label3.setSizePolicy(sizePolicy)
        self.label3.setText(_fromUtf8(""))
        self.label3.setObjectName(_fromUtf8("label3"))
        self.horizontalLayout.addWidget(self.label3)
        self.val4 = QtGui.QLabel(InfoStatus)
        self.val4.setMinimumSize(QtCore.QSize(40, 0))
        self.val4.setText(_fromUtf8(""))
        self.val4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.val4.setObjectName(_fromUtf8("val4"))
        self.horizontalLayout.addWidget(self.val4)
        self.label4 = QtGui.QLabel(InfoStatus)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label4.sizePolicy().hasHeightForWidth())
        self.label4.setSizePolicy(sizePolicy)
        self.label4.setText(_fromUtf8(""))
        self.label4.setScaledContents(False)
        self.label4.setObjectName(_fromUtf8("label4"))
        self.horizontalLayout.addWidget(self.label4)

        self.retranslateUi(InfoStatus)
        QtCore.QMetaObject.connectSlotsByName(InfoStatus)

    def retranslateUi(self, InfoStatus):
        InfoStatus.setWindowTitle(_("Form"))

