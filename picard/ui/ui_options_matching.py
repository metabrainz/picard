# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_matching.ui'
#
# Created: Sun Jan 28 12:45:00 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_MatchingOptionsPage(object):
    def setupUi(self, MatchingOptionsPage):
        MatchingOptionsPage.setObjectName("MatchingOptionsPage")
        MatchingOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,328,313).size()).expandedTo(MatchingOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(MatchingOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.rename_files = QtGui.QGroupBox(MatchingOptionsPage)
        self.rename_files.setObjectName("rename_files")

        self.gridlayout = QtGui.QGridLayout(self.rename_files)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        self.label_6 = QtGui.QLabel(self.rename_files)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName("label_6")
        self.gridlayout.addWidget(self.label_6,3,0,1,1)

        self.track_matching_threshold = QtGui.QSpinBox(self.rename_files)
        self.track_matching_threshold.setMaximum(100)
        self.track_matching_threshold.setObjectName("track_matching_threshold")
        self.gridlayout.addWidget(self.track_matching_threshold,3,1,1,1)

        self.cluster_lookup_threshold = QtGui.QSpinBox(self.rename_files)
        self.cluster_lookup_threshold.setMaximum(100)
        self.cluster_lookup_threshold.setObjectName("cluster_lookup_threshold")
        self.gridlayout.addWidget(self.cluster_lookup_threshold,2,1,1,1)

        self.file_lookup_threshold = QtGui.QSpinBox(self.rename_files)
        self.file_lookup_threshold.setMaximum(100)
        self.file_lookup_threshold.setObjectName("file_lookup_threshold")
        self.gridlayout.addWidget(self.file_lookup_threshold,1,1,1,1)

        self.label_4 = QtGui.QLabel(self.rename_files)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName("label_4")
        self.gridlayout.addWidget(self.label_4,1,0,1,1)

        self.label_5 = QtGui.QLabel(self.rename_files)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName("label_5")
        self.gridlayout.addWidget(self.label_5,2,0,1,1)

        self.label_3 = QtGui.QLabel(self.rename_files)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3,0,0,1,1)

        self.puid_lookup_threshold = QtGui.QSpinBox(self.rename_files)
        self.puid_lookup_threshold.setMaximum(100)
        self.puid_lookup_threshold.setObjectName("puid_lookup_threshold")
        self.gridlayout.addWidget(self.puid_lookup_threshold,0,1,1,1)
        self.vboxlayout.addWidget(self.rename_files)

        spacerItem = QtGui.QSpacerItem(20,41,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_6.setBuddy(self.file_lookup_threshold)
        self.label_4.setBuddy(self.file_lookup_threshold)
        self.label_5.setBuddy(self.file_lookup_threshold)
        self.label_3.setBuddy(self.puid_lookup_threshold)

        self.retranslateUi(MatchingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MatchingOptionsPage)
        MatchingOptionsPage.setTabOrder(self.puid_lookup_threshold,self.file_lookup_threshold)
        MatchingOptionsPage.setTabOrder(self.file_lookup_threshold,self.cluster_lookup_threshold)
        MatchingOptionsPage.setTabOrder(self.cluster_lookup_threshold,self.track_matching_threshold)

    def retranslateUi(self, MatchingOptionsPage):
        self.rename_files.setTitle(_(u"Thresholds"))
        self.label_6.setText(_(u"Minimal similarity for matching files to tracks:"))
        self.track_matching_threshold.setSuffix(_(u" %"))
        self.cluster_lookup_threshold.setSuffix(_(u" %"))
        self.file_lookup_threshold.setSuffix(_(u" %"))
        self.label_4.setText(_(u"Minimal similarity for file lookups:"))
        self.label_5.setText(_(u"Minimal similarity for cluster lookups:"))
        self.label_3.setText(_(u"Minimal similarity for PUID lookups:"))
        self.puid_lookup_threshold.setSuffix(_(u" %"))

