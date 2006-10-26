# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\options_metadata.ui'
#
# Created: Thu Oct 26 15:08:00 2006
#      by: PyQt4 UI code generator 4-snapshot-20061015
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,344,356).size()).expandedTo(Form.minimumSizeHint()))

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

        self.translate_artist_names = QtGui.QCheckBox(self.rename_files)
        self.translate_artist_names.setObjectName("translate_artist_names")
        self.gridlayout.addWidget(self.translate_artist_names,0,0,1,1)
        self.vboxlayout.addWidget(self.rename_files)

        self.rename_files_2 = QtGui.QGroupBox(Form)
        self.rename_files_2.setObjectName("rename_files_2")

        self.gridlayout1 = QtGui.QGridLayout(self.rename_files_2)
        self.gridlayout1.setMargin(9)
        self.gridlayout1.setSpacing(2)
        self.gridlayout1.setObjectName("gridlayout1")

        self.label_3 = QtGui.QLabel(self.rename_files_2)
        self.label_3.setObjectName("label_3")
        self.gridlayout1.addWidget(self.label_3,0,0,1,2)

        self.label_4 = QtGui.QLabel(self.rename_files_2)
        self.label_4.setObjectName("label_4")
        self.gridlayout1.addWidget(self.label_4,2,0,1,2)

        self.nat_name = QtGui.QLineEdit(self.rename_files_2)
        self.nat_name.setObjectName("nat_name")
        self.gridlayout1.addWidget(self.nat_name,3,0,1,1)

        self.nat_name_default = QtGui.QPushButton(self.rename_files_2)
        self.nat_name_default.setObjectName("nat_name_default")
        self.gridlayout1.addWidget(self.nat_name_default,3,1,1,1)

        self.va_name_default = QtGui.QPushButton(self.rename_files_2)
        self.va_name_default.setObjectName("va_name_default")
        self.gridlayout1.addWidget(self.va_name_default,1,1,1,1)

        self.va_name = QtGui.QLineEdit(self.rename_files_2)
        self.va_name.setObjectName("va_name")
        self.gridlayout1.addWidget(self.va_name,1,0,1,1)
        self.vboxlayout.addWidget(self.rename_files_2)

        spacerItem = QtGui.QSpacerItem(141,81,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_3.setBuddy(self.va_name_default)
        self.label_4.setBuddy(self.nat_name_default)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.translate_artist_names,self.va_name)
        Form.setTabOrder(self.va_name,self.va_name_default)
        Form.setTabOrder(self.va_name_default,self.nat_name)
        Form.setTabOrder(self.nat_name,self.nat_name_default)

    def retranslateUi(self, Form):
        self.rename_files.setTitle(_(u"Metadata"))
        self.translate_artist_names.setText(_(u"Translate foreign artist names to English where possible"))
        self.rename_files_2.setTitle(_(u"Custom Fields"))
        self.label_3.setText(_(u"Various artists:"))
        self.label_4.setText(_(u"Non-album tracks:"))
        self.nat_name_default.setText(_(u"Default"))
        self.va_name_default.setText(_(u"Default"))

