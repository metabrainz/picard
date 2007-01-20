# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_tags.ui'
#
# Created: Sat Jan 20 17:45:24 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,292,295).size()).expandedTo(Form.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(Form)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.rename_files = QtGui.QGroupBox(Form)
        self.rename_files.setObjectName("rename_files")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.rename_files)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.clear_existing_tags = QtGui.QCheckBox(self.rename_files)
        self.clear_existing_tags.setObjectName("clear_existing_tags")
        self.vboxlayout1.addWidget(self.clear_existing_tags)
        self.vboxlayout.addWidget(self.rename_files)

        self.rename_files_2 = QtGui.QGroupBox(Form)
        self.rename_files_2.setObjectName("rename_files_2")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.rename_files_2)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(2)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.write_id3v1 = QtGui.QCheckBox(self.rename_files_2)
        self.write_id3v1.setObjectName("write_id3v1")
        self.vboxlayout2.addWidget(self.write_id3v1)

        self.write_id3v23 = QtGui.QCheckBox(self.rename_files_2)
        self.write_id3v23.setObjectName("write_id3v23")
        self.vboxlayout2.addWidget(self.write_id3v23)

        self.label_2 = QtGui.QLabel(self.rename_files_2)
        self.label_2.setObjectName("label_2")
        self.vboxlayout2.addWidget(self.label_2)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.enc_iso88591 = QtGui.QRadioButton(self.rename_files_2)
        self.enc_iso88591.setObjectName("enc_iso88591")
        self.hboxlayout.addWidget(self.enc_iso88591)

        self.enc_utf16 = QtGui.QRadioButton(self.rename_files_2)
        self.enc_utf16.setObjectName("enc_utf16")
        self.hboxlayout.addWidget(self.enc_utf16)

        self.enc_utf8 = QtGui.QRadioButton(self.rename_files_2)
        self.enc_utf8.setObjectName("enc_utf8")
        self.hboxlayout.addWidget(self.enc_utf8)

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.vboxlayout2.addLayout(self.hboxlayout)
        self.vboxlayout.addWidget(self.rename_files_2)

        self.rename_files_3 = QtGui.QGroupBox(Form)
        self.rename_files_3.setObjectName("rename_files_3")

        self.vboxlayout3 = QtGui.QVBoxLayout(self.rename_files_3)
        self.vboxlayout3.setMargin(9)
        self.vboxlayout3.setSpacing(2)
        self.vboxlayout3.setObjectName("vboxlayout3")

        self.strip_ape_tags = QtGui.QCheckBox(self.rename_files_3)
        self.strip_ape_tags.setObjectName("strip_ape_tags")
        self.vboxlayout3.addWidget(self.strip_ape_tags)
        self.vboxlayout.addWidget(self.rename_files_3)

        spacerItem1 = QtGui.QSpacerItem(81,21,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        self.rename_files.setTitle(_(u"Common"))
        self.clear_existing_tags.setText(_(u"Clear existing tags before writing new tags"))
        self.rename_files_2.setTitle(_(u"ID3"))
        self.write_id3v1.setText(_(u"Write ID3v1 tags to the files"))
        self.write_id3v23.setText(_(u"Write ID3v2 version 2.3 tags (2.4 is default)"))
        self.label_2.setText(_(u"Text encoding to use while writing ID3v2 tags:"))
        self.enc_iso88591.setText(_(u"ISO-8859-1"))
        self.enc_utf16.setText(_(u"UTF-16"))
        self.enc_utf8.setText(_(u"UTF-8"))
        self.rename_files_3.setTitle(_(u"APE"))
        self.strip_ape_tags.setText(_(u"Strip APE tags from MP3 files"))

