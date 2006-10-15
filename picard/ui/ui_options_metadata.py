# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\options_metadata.ui'
#
# Created: Sun Oct 15 13:45:25 2006
#      by: PyQt4 UI code generator 4.0
#          E:\projects\picard-qt\setup.py build_ui
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,350,300).size()).expandedTo(Form.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Form)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(2)
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

        spacerItem = QtGui.QSpacerItem(61,201,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        self.rename_files.setTitle(_("Metadata"))
        self.translate_artist_names.setText(_("Translate foreign artist names to English where possible"))
