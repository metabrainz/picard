# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_fingerprinting.ui'
#
# Created: Fri Sep 16 18:35:59 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_FingerprintingOptionsPage(object):
    def setupUi(self, FingerprintingOptionsPage):
        FingerprintingOptionsPage.setObjectName(_fromUtf8("FingerprintingOptionsPage"))
        FingerprintingOptionsPage.resize(352, 331)
        self.verticalLayout = QtGui.QVBoxLayout(FingerprintingOptionsPage)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(FingerprintingOptionsPage)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.use_musicdns = QtGui.QRadioButton(self.groupBox)
        self.use_musicdns.setObjectName(_fromUtf8("use_musicdns"))
        self.gridLayout.addWidget(self.use_musicdns, 0, 0, 1, 1)
        self.use_acoustid = QtGui.QRadioButton(self.groupBox)
        self.use_acoustid.setObjectName(_fromUtf8("use_acoustid"))
        self.gridLayout.addWidget(self.use_acoustid, 1, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.acoustid_settings = QtGui.QGroupBox(FingerprintingOptionsPage)
        self.acoustid_settings.setObjectName(_fromUtf8("acoustid_settings"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.acoustid_settings)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.label = QtGui.QLabel(self.acoustid_settings)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout_2.addWidget(self.label)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.acoustid_fpcalc = QtGui.QLineEdit(self.acoustid_settings)
        self.acoustid_fpcalc.setObjectName(_fromUtf8("acoustid_fpcalc"))
        self.horizontalLayout_2.addWidget(self.acoustid_fpcalc)
        self.acoustid_fpcalc_browse = QtGui.QPushButton(self.acoustid_settings)
        self.acoustid_fpcalc_browse.setObjectName(_fromUtf8("acoustid_fpcalc_browse"))
        self.horizontalLayout_2.addWidget(self.acoustid_fpcalc_browse)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.label_2 = QtGui.QLabel(self.acoustid_settings)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout_2.addWidget(self.label_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.acoustid_apikey = QtGui.QLineEdit(self.acoustid_settings)
        self.acoustid_apikey.setObjectName(_fromUtf8("acoustid_apikey"))
        self.horizontalLayout.addWidget(self.acoustid_apikey)
        self.acoustid_apikey_get = QtGui.QPushButton(self.acoustid_settings)
        self.acoustid_apikey_get.setObjectName(_fromUtf8("acoustid_apikey_get"))
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
        self.label_2.setText(_("API key:"))
        self.acoustid_apikey_get.setText(_("Get API key..."))

