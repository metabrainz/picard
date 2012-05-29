# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_matching.ui'
#
# Created: Tue May 29 19:44:14 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MatchingOptionsPage(object):
    def setupUi(self, MatchingOptionsPage):
        MatchingOptionsPage.setObjectName(_fromUtf8("MatchingOptionsPage"))
        MatchingOptionsPage.resize(413, 612)
        self.vboxlayout = QtGui.QVBoxLayout(MatchingOptionsPage)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.rename_files = QtGui.QGroupBox(MatchingOptionsPage)
        self.rename_files.setObjectName(_fromUtf8("rename_files"))
        self.gridlayout = QtGui.QGridLayout(self.rename_files)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.label_6 = QtGui.QLabel(self.rename_files)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridlayout.addWidget(self.label_6, 2, 0, 1, 1)
        self.track_matching_threshold = QtGui.QSpinBox(self.rename_files)
        self.track_matching_threshold.setMaximum(100)
        self.track_matching_threshold.setObjectName(_fromUtf8("track_matching_threshold"))
        self.gridlayout.addWidget(self.track_matching_threshold, 2, 1, 1, 1)
        self.cluster_lookup_threshold = QtGui.QSpinBox(self.rename_files)
        self.cluster_lookup_threshold.setMaximum(100)
        self.cluster_lookup_threshold.setObjectName(_fromUtf8("cluster_lookup_threshold"))
        self.gridlayout.addWidget(self.cluster_lookup_threshold, 1, 1, 1, 1)
        self.file_lookup_threshold = QtGui.QSpinBox(self.rename_files)
        self.file_lookup_threshold.setMaximum(100)
        self.file_lookup_threshold.setObjectName(_fromUtf8("file_lookup_threshold"))
        self.gridlayout.addWidget(self.file_lookup_threshold, 0, 1, 1, 1)
        self.label_4 = QtGui.QLabel(self.rename_files)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridlayout.addWidget(self.label_4, 0, 0, 1, 1)
        self.label_5 = QtGui.QLabel(self.rename_files)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridlayout.addWidget(self.label_5, 1, 0, 1, 1)
        self.vboxlayout.addWidget(self.rename_files)
        spacerItem = QtGui.QSpacerItem(20, 41, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_6.setBuddy(self.file_lookup_threshold)
        self.label_4.setBuddy(self.file_lookup_threshold)
        self.label_5.setBuddy(self.file_lookup_threshold)

        self.retranslateUi(MatchingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MatchingOptionsPage)
        MatchingOptionsPage.setTabOrder(self.file_lookup_threshold, self.cluster_lookup_threshold)
        MatchingOptionsPage.setTabOrder(self.cluster_lookup_threshold, self.track_matching_threshold)

    def retranslateUi(self, MatchingOptionsPage):
        self.rename_files.setTitle(_("Thresholds"))
        self.label_6.setText(_("Minimal similarity for matching files to tracks:"))
        self.track_matching_threshold.setSuffix(_(" %"))
        self.cluster_lookup_threshold.setSuffix(_(" %"))
        self.file_lookup_threshold.setSuffix(_(" %"))
        self.label_4.setText(_("Minimal similarity for file lookups:"))
        self.label_5.setText(_("Minimal similarity for cluster lookups:"))

