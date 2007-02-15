# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_cover.ui'
#
# Created: Thu Feb 15 23:42:37 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_CoverOptionsPage(object):
    def setupUi(self, CoverOptionsPage):
        CoverOptionsPage.setObjectName("CoverOptionsPage")
        CoverOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,293,277).size()).expandedTo(CoverOptionsPage.minimumSizeHint()))

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

        spacerItem = QtGui.QSpacerItem(275,51,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(CoverOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CoverOptionsPage)
        CoverOptionsPage.setTabOrder(self.save_images_to_tags,self.save_images_to_files)
        CoverOptionsPage.setTabOrder(self.save_images_to_files,self.cover_image_filename)

    def retranslateUi(self, CoverOptionsPage):
        self.rename_files.setTitle(QtGui.QApplication.translate("CoverOptionsPage", "Location", None, QtGui.QApplication.UnicodeUTF8))
        self.save_images_to_tags.setText(QtGui.QApplication.translate("CoverOptionsPage", "Embed cover images into tags", None, QtGui.QApplication.UnicodeUTF8))
        self.save_images_to_files.setText(QtGui.QApplication.translate("CoverOptionsPage", "Save cover images as separate files", None, QtGui.QApplication.UnicodeUTF8))

