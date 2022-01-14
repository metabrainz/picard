# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MatchingOptionsPage(object):
    def setupUi(self, MatchingOptionsPage):
        MatchingOptionsPage.setObjectName("MatchingOptionsPage")
        MatchingOptionsPage.resize(413, 612)
        self.vboxlayout = QtWidgets.QVBoxLayout(MatchingOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.rename_files = QtWidgets.QGroupBox(MatchingOptionsPage)
        self.rename_files.setObjectName("rename_files")
        self.gridlayout = QtWidgets.QGridLayout(self.rename_files)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")
        self.label_6 = QtWidgets.QLabel(self.rename_files)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName("label_6")
        self.gridlayout.addWidget(self.label_6, 2, 0, 1, 1)
        self.track_matching_threshold = QtWidgets.QSpinBox(self.rename_files)
        self.track_matching_threshold.setMaximum(100)
        self.track_matching_threshold.setObjectName("track_matching_threshold")
        self.gridlayout.addWidget(self.track_matching_threshold, 2, 1, 1, 1)
        self.cluster_lookup_threshold = QtWidgets.QSpinBox(self.rename_files)
        self.cluster_lookup_threshold.setMaximum(100)
        self.cluster_lookup_threshold.setObjectName("cluster_lookup_threshold")
        self.gridlayout.addWidget(self.cluster_lookup_threshold, 1, 1, 1, 1)
        self.file_lookup_threshold = QtWidgets.QSpinBox(self.rename_files)
        self.file_lookup_threshold.setMaximum(100)
        self.file_lookup_threshold.setObjectName("file_lookup_threshold")
        self.gridlayout.addWidget(self.file_lookup_threshold, 0, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.rename_files)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName("label_4")
        self.gridlayout.addWidget(self.label_4, 0, 0, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.rename_files)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName("label_5")
        self.gridlayout.addWidget(self.label_5, 1, 0, 1, 1)
        self.vboxlayout.addWidget(self.rename_files)
        spacerItem = QtWidgets.QSpacerItem(20, 41, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_6.setBuddy(self.file_lookup_threshold)
        self.label_4.setBuddy(self.file_lookup_threshold)
        self.label_5.setBuddy(self.file_lookup_threshold)

        self.retranslateUi(MatchingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MatchingOptionsPage)
        MatchingOptionsPage.setTabOrder(self.file_lookup_threshold, self.cluster_lookup_threshold)
        MatchingOptionsPage.setTabOrder(self.cluster_lookup_threshold, self.track_matching_threshold)

    def retranslateUi(self, MatchingOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.rename_files.setTitle(_("Thresholds"))
        self.label_6.setText(_("Minimal similarity for matching files to tracks:"))
        self.track_matching_threshold.setSuffix(_(" %"))
        self.cluster_lookup_threshold.setSuffix(_(" %"))
        self.file_lookup_threshold.setSuffix(_(" %"))
        self.label_4.setText(_("Minimal similarity for file lookups:"))
        self.label_5.setText(_("Minimal similarity for cluster lookups:"))
