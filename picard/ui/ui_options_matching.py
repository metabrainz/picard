# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_matching.ui'
#
# Created: Sat Dec 16 15:14:02 2006
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,306,268).size()).expandedTo(Form.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Form)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.rename_files = QtGui.QGroupBox(Form)
        self.rename_files.setObjectName("rename_files")

        self.gridlayout = QtGui.QGridLayout(self.rename_files)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        self.metadata_lookup_threshold = QtGui.QSpinBox(self.rename_files)
        self.metadata_lookup_threshold.setMaximum(100)
        self.metadata_lookup_threshold.setObjectName("metadata_lookup_threshold")
        self.gridlayout.addWidget(self.metadata_lookup_threshold,1,1,1,1)

        self.puid_lookup_threshold = QtGui.QSpinBox(self.rename_files)
        self.puid_lookup_threshold.setMaximum(100)
        self.puid_lookup_threshold.setObjectName("puid_lookup_threshold")
        self.gridlayout.addWidget(self.puid_lookup_threshold,0,1,1,1)

        self.label_4 = QtGui.QLabel(self.rename_files)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName("label_4")
        self.gridlayout.addWidget(self.label_4,1,0,1,1)

        self.label_3 = QtGui.QLabel(self.rename_files)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3,0,0,1,1)
        self.vboxlayout.addWidget(self.rename_files)

        spacerItem = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_4.setBuddy(self.metadata_lookup_threshold)
        self.label_3.setBuddy(self.puid_lookup_threshold)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.puid_lookup_threshold,self.metadata_lookup_threshold)

    def retranslateUi(self, Form):
        self.rename_files.setTitle(_(u"Thresholds"))
        self.metadata_lookup_threshold.setSuffix(_(u" %"))
        self.puid_lookup_threshold.setSuffix(_(u" %"))
        self.label_4.setText(_(u"Minimal similarity for metadata lookups:"))
        self.label_3.setText(_(u"Minimal similarity for PUID lookups:"))
