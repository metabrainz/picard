# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_cover.ui'
#
# Created: Tue May 29 19:44:15 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_CoverOptionsPage(object):
    def setupUi(self, CoverOptionsPage):
        CoverOptionsPage.setObjectName(_fromUtf8("CoverOptionsPage"))
        CoverOptionsPage.resize(293, 279)
        self.vboxlayout = QtGui.QVBoxLayout(CoverOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.rename_files = QtGui.QGroupBox(CoverOptionsPage)
        self.rename_files.setObjectName(_fromUtf8("rename_files"))
        self.vboxlayout1 = QtGui.QVBoxLayout(self.rename_files)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName(_fromUtf8("vboxlayout1"))
        self.save_images_to_tags = QtGui.QCheckBox(self.rename_files)
        self.save_images_to_tags.setObjectName(_fromUtf8("save_images_to_tags"))
        self.vboxlayout1.addWidget(self.save_images_to_tags)
        self.save_images_to_files = QtGui.QCheckBox(self.rename_files)
        self.save_images_to_files.setObjectName(_fromUtf8("save_images_to_files"))
        self.vboxlayout1.addWidget(self.save_images_to_files)
        self.cover_image_filename = QtGui.QLineEdit(self.rename_files)
        self.cover_image_filename.setObjectName(_fromUtf8("cover_image_filename"))
        self.vboxlayout1.addWidget(self.cover_image_filename)
        self.save_images_overwrite = QtGui.QCheckBox(self.rename_files)
        self.save_images_overwrite.setObjectName(_fromUtf8("save_images_overwrite"))
        self.vboxlayout1.addWidget(self.save_images_overwrite)
        self.vboxlayout.addWidget(self.rename_files)
        spacerItem = QtGui.QSpacerItem(275, 91, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(CoverOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CoverOptionsPage)
        CoverOptionsPage.setTabOrder(self.save_images_to_tags, self.save_images_to_files)
        CoverOptionsPage.setTabOrder(self.save_images_to_files, self.cover_image_filename)

    def retranslateUi(self, CoverOptionsPage):
        self.rename_files.setTitle(_("Location"))
        self.save_images_to_tags.setText(_("Embed cover images into tags"))
        self.save_images_to_files.setText(_("Save cover images as separate files"))
        self.save_images_overwrite.setText(_("Overwrite the file if it already exists"))

