# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_fingerprinting.ui'
#
# Created: Tue Sep 20 10:42:48 2011
#      by: PyQt4 UI code generator 4.7.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_FingerprintingOptionsPage(object):
    def setupUi(self, FingerprintingOptionsPage):
        FingerprintingOptionsPage.setObjectName("FingerprintingOptionsPage")
        FingerprintingOptionsPage.resize(371, 305)
        self.verticalLayout = QtGui.QVBoxLayout(FingerprintingOptionsPage)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtGui.QGroupBox(FingerprintingOptionsPage)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.use_musicdns = QtGui.QRadioButton(self.groupBox)
        self.use_musicdns.setObjectName("use_musicdns")
        self.gridLayout.addWidget(self.use_musicdns, 0, 0, 1, 1)
        self.use_acoustid = QtGui.QRadioButton(self.groupBox)
        self.use_acoustid.setObjectName("use_acoustid")
        self.gridLayout.addWidget(self.use_acoustid, 1, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.acoustid_settings = QtGui.QGroupBox(FingerprintingOptionsPage)
        self.acoustid_settings.setObjectName("acoustid_settings")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.acoustid_settings)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtGui.QLabel(self.acoustid_settings)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.acoustid_fpcalc = QtGui.QLineEdit(self.acoustid_settings)
        self.acoustid_fpcalc.setObjectName("acoustid_fpcalc")
        self.horizontalLayout_2.addWidget(self.acoustid_fpcalc)
        self.acoustid_fpcalc_browse = QtGui.QPushButton(self.acoustid_settings)
        self.acoustid_fpcalc_browse.setObjectName("acoustid_fpcalc_browse")
        self.horizontalLayout_2.addWidget(self.acoustid_fpcalc_browse)
        self.acoustid_fpcalc_download = QtGui.QPushButton(self.acoustid_settings)
        self.acoustid_fpcalc_download.setObjectName("acoustid_fpcalc_download")
        self.horizontalLayout_2.addWidget(self.acoustid_fpcalc_download)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.label_2 = QtGui.QLabel(self.acoustid_settings)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.acoustid_apikey = QtGui.QLineEdit(self.acoustid_settings)
        self.acoustid_apikey.setObjectName("acoustid_apikey")
        self.horizontalLayout.addWidget(self.acoustid_apikey)
        self.acoustid_apikey_get = QtGui.QPushButton(self.acoustid_settings)
        self.acoustid_apikey_get.setObjectName("acoustid_apikey_get")
        self.horizontalLayout.addWidget(self.acoustid_apikey_get)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.acoustid_settings)
        spacerItem = QtGui.QSpacerItem(181, 21, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(FingerprintingOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(FingerprintingOptionsPage)

    def retranslateUi(self, FingerprintingOptionsPage):
        self.groupBox.setTitle(_("Fingerpriting Systems"))
        self.use_musicdns.setText(_("Use AmpliFIND (formerly MusicDNS)"))
        self.use_acoustid.setText(_("Use AcoustID"))
        self.acoustid_settings.setTitle(_("AcoustID\'s Settings"))
        self.label.setText(_("Fingerprinter:"))
        self.acoustid_fpcalc_browse.setText(_("Browse..."))
        self.acoustid_fpcalc_download.setText(_("Download..."))
        self.label_2.setText(_("API key:"))
        self.acoustid_apikey_get.setText(_("Get API key..."))

