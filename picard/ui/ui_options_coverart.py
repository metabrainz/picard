# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'contrib/plugins/coverart/ui_options_coverart.ui'
#
# Created: Thu Aug 23 15:33:26 2012
#      by: PyQt4 UI code generator 4.9.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_CoverartOptionsPage(object):
    def setupUi(self, CoverartOptionsPage):
        CoverartOptionsPage.setObjectName(_fromUtf8("CoverartOptionsPage"))
        CoverartOptionsPage.resize(400, 326)
        self.verticalLayout = QtGui.QVBoxLayout(CoverartOptionsPage)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(CoverartOptionsPage)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.caprovider_amazon = QtGui.QCheckBox(self.groupBox)
        self.caprovider_amazon.setObjectName(_fromUtf8("caprovider_amazon"))
        self.verticalLayout_2.addWidget(self.caprovider_amazon)
        self.caprovider_cdbaby = QtGui.QCheckBox(self.groupBox)
        self.caprovider_cdbaby.setObjectName(_fromUtf8("caprovider_cdbaby"))
        self.verticalLayout_2.addWidget(self.caprovider_cdbaby)
        self.caprovider_caa = QtGui.QCheckBox(self.groupBox)
        self.caprovider_caa.setObjectName(_fromUtf8("caprovider_caa"))
        self.verticalLayout_2.addWidget(self.caprovider_caa)
        self.caprovider_jamendo = QtGui.QCheckBox(self.groupBox)
        self.caprovider_jamendo.setObjectName(_fromUtf8("caprovider_jamendo"))
        self.verticalLayout_2.addWidget(self.caprovider_jamendo)
        self.caprovider_whitelist = QtGui.QCheckBox(self.groupBox)
        self.caprovider_whitelist.setObjectName(_fromUtf8("caprovider_whitelist"))
        self.verticalLayout_2.addWidget(self.caprovider_whitelist)
        self.verticalLayout.addWidget(self.groupBox)
        self.gb_caa = QtGui.QGroupBox(CoverartOptionsPage)
        self.gb_caa.setEnabled(False)
        self.gb_caa.setObjectName(_fromUtf8("gb_caa"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.gb_caa)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(self.gb_caa)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cb_image_size = QtGui.QComboBox(self.gb_caa)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cb_image_size.sizePolicy().hasHeightForWidth())
        self.cb_image_size.setSizePolicy(sizePolicy)
        self.cb_image_size.setObjectName(_fromUtf8("cb_image_size"))
        self.cb_image_size.addItem(_fromUtf8(""))
        self.cb_image_size.addItem(_fromUtf8(""))
        self.cb_image_size.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.cb_image_size)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.label_2 = QtGui.QLabel(self.gb_caa)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout_3.addWidget(self.label_2)
        self.le_image_types = QtGui.QLineEdit(self.gb_caa)
        self.le_image_types.setObjectName(_fromUtf8("le_image_types"))
        self.verticalLayout_3.addWidget(self.le_image_types)
        self.cb_approved_only = QtGui.QCheckBox(self.gb_caa)
        self.cb_approved_only.setObjectName(_fromUtf8("cb_approved_only"))
        self.verticalLayout_3.addWidget(self.cb_approved_only)
        self.verticalLayout.addWidget(self.gb_caa)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)

        self.retranslateUi(CoverartOptionsPage)
        QtCore.QObject.connect(self.caprovider_caa, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.gb_caa.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(CoverartOptionsPage)

    def retranslateUi(self, CoverartOptionsPage):
        CoverartOptionsPage.setWindowTitle(QtGui.QApplication.translate("CoverartOptionsPage", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("CoverartOptionsPage", "Coverart Providers", None, QtGui.QApplication.UnicodeUTF8))
        self.caprovider_amazon.setText(QtGui.QApplication.translate("CoverartOptionsPage", "Amazon", None, QtGui.QApplication.UnicodeUTF8))
        self.caprovider_cdbaby.setText(QtGui.QApplication.translate("CoverartOptionsPage", "CD Baby", None, QtGui.QApplication.UnicodeUTF8))
        self.caprovider_caa.setText(QtGui.QApplication.translate("CoverartOptionsPage", "Cover Art Archive", None, QtGui.QApplication.UnicodeUTF8))
        self.caprovider_jamendo.setText(QtGui.QApplication.translate("CoverartOptionsPage", "Jamendo", None, QtGui.QApplication.UnicodeUTF8))
        self.caprovider_whitelist.setText(QtGui.QApplication.translate("CoverartOptionsPage", "Sites on the whitelist", None, QtGui.QApplication.UnicodeUTF8))
        self.gb_caa.setTitle(QtGui.QApplication.translate("CoverartOptionsPage", "Cover Art Archive", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("CoverartOptionsPage", "Only use images of the following size:", None, QtGui.QApplication.UnicodeUTF8))
        self.cb_image_size.setItemText(0, QtGui.QApplication.translate("CoverartOptionsPage", "250 px", None, QtGui.QApplication.UnicodeUTF8))
        self.cb_image_size.setItemText(1, QtGui.QApplication.translate("CoverartOptionsPage", "500 px", None, QtGui.QApplication.UnicodeUTF8))
        self.cb_image_size.setItemText(2, QtGui.QApplication.translate("CoverartOptionsPage", "Full size", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("CoverartOptionsPage", "Download only images of the following types:", None, QtGui.QApplication.UnicodeUTF8))
        self.cb_approved_only.setText(QtGui.QApplication.translate("CoverartOptionsPage", "Download only approved images", None, QtGui.QApplication.UnicodeUTF8))
