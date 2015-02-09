# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_FingerprintingOptionsPage(object):
    def setupUi(self, FingerprintingOptionsPage):
        FingerprintingOptionsPage.setObjectName(_fromUtf8("FingerprintingOptionsPage"))
        FingerprintingOptionsPage.resize(371, 408)
        self.verticalLayout = QtGui.QVBoxLayout(FingerprintingOptionsPage)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.fingerprinting = QtGui.QGroupBox(FingerprintingOptionsPage)
        self.fingerprinting.setCheckable(False)
        self.fingerprinting.setObjectName(_fromUtf8("fingerprinting"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.fingerprinting)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.disable_fingerprinting = QtGui.QRadioButton(self.fingerprinting)
        self.disable_fingerprinting.setObjectName(_fromUtf8("disable_fingerprinting"))
        self.verticalLayout_3.addWidget(self.disable_fingerprinting)
        self.use_acoustid = QtGui.QRadioButton(self.fingerprinting)
        self.use_acoustid.setObjectName(_fromUtf8("use_acoustid"))
        self.verticalLayout_3.addWidget(self.use_acoustid)
        self.verticalLayout.addWidget(self.fingerprinting)
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
        self.acoustid_fpcalc_download = QtGui.QPushButton(self.acoustid_settings)
        self.acoustid_fpcalc_download.setObjectName(_fromUtf8("acoustid_fpcalc_download"))
        self.horizontalLayout_2.addWidget(self.acoustid_fpcalc_download)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.acoustid_fpcalc_info = QtGui.QLabel(self.acoustid_settings)
        self.acoustid_fpcalc_info.setText(_fromUtf8(""))
        self.acoustid_fpcalc_info.setObjectName(_fromUtf8("acoustid_fpcalc_info"))
        self.verticalLayout_2.addWidget(self.acoustid_fpcalc_info)
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
        self.fingerprinting.setTitle(_("Audio Fingerprinting"))
        self.disable_fingerprinting.setText(_("Do not use audio fingerprinting"))
        self.use_acoustid.setText(_("Use AcoustID"))
        self.acoustid_settings.setTitle(_("AcoustID Settings"))
        self.label.setText(_("Fingerprint calculator:"))
        self.acoustid_fpcalc_browse.setText(_("Browse..."))
        self.acoustid_fpcalc_download.setText(_("Download..."))
        self.label_2.setText(_("API key:"))
        self.acoustid_apikey_get.setText(_("Get API key..."))

