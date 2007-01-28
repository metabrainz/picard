# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_cover.ui'
#
# Created: Sun Jan 28 12:35:27 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_CoverOptionsPage(object):
    def setupUi(self, CoverOptionsPage):
        CoverOptionsPage.setObjectName("CoverOptionsPage")
        CoverOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,293,314).size()).expandedTo(CoverOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(CoverOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.rename_files = QtGui.QGroupBox(CoverOptionsPage)
        self.rename_files.setObjectName("rename_files")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.rename_files)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.save_images_to_tags = QtGui.QCheckBox(self.rename_files)
        self.save_images_to_tags.setObjectName("save_images_to_tags")
        self.vboxlayout1.addWidget(self.save_images_to_tags)

        self.save_images_to_files = QtGui.QCheckBox(self.rename_files)
        self.save_images_to_files.setObjectName("save_images_to_files")
        self.vboxlayout1.addWidget(self.save_images_to_files)

        self.cover_image_filename = QtGui.QLineEdit(self.rename_files)
        self.cover_image_filename.setObjectName("cover_image_filename")
        self.vboxlayout1.addWidget(self.cover_image_filename)
        self.vboxlayout.addWidget(self.rename_files)

        self.rename_files_2 = QtGui.QGroupBox(CoverOptionsPage)
        self.rename_files_2.setObjectName("rename_files_2")

        self.vboxlayout2 = QtGui.QVBoxLayout(self.rename_files_2)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(2)
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.use_amazon_images = QtGui.QCheckBox(self.rename_files_2)
        self.use_amazon_images.setObjectName("use_amazon_images")
        self.vboxlayout2.addWidget(self.use_amazon_images)

        self.label = QtGui.QLabel(self.rename_files_2)
        self.label.setObjectName("label")
        self.vboxlayout2.addWidget(self.label)
        self.vboxlayout.addWidget(self.rename_files_2)

        spacerItem = QtGui.QSpacerItem(275,51,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(CoverOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CoverOptionsPage)
        CoverOptionsPage.setTabOrder(self.save_images_to_tags,self.save_images_to_files)
        CoverOptionsPage.setTabOrder(self.save_images_to_files,self.cover_image_filename)
        CoverOptionsPage.setTabOrder(self.cover_image_filename,self.use_amazon_images)

    def retranslateUi(self, CoverOptionsPage):
        self.rename_files.setTitle(_(u"Location"))
        self.save_images_to_tags.setText(_(u"Save cover images to tags"))
        self.save_images_to_files.setText(_(u"Save cover images as separate files"))
        self.rename_files_2.setTitle(_(u"Amazon"))
        self.use_amazon_images.setText(_(u"Use cover images from Amazon"))
        self.label.setText(_(u"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'Tahoma\'; font-size:8pt; font-weight:400; font-style:normal; text-decoration:none;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-style:italic;\">TODO: add warning about Amazon\'s ToS</span></p></body></html>"))

