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

class Ui_CoverOptionsPage(object):
    def setupUi(self, CoverOptionsPage):
        CoverOptionsPage.setObjectName(_fromUtf8("CoverOptionsPage"))
        CoverOptionsPage.resize(632, 560)
        self.verticalLayout = QtGui.QVBoxLayout(CoverOptionsPage)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.location = QtGui.QGroupBox(CoverOptionsPage)
        self.location.setObjectName(_fromUtf8("location"))
        self.vboxlayout = QtGui.QVBoxLayout(self.location)
        self.vboxlayout.setSpacing(2)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.save_images_to_tags = QtGui.QCheckBox(self.location)
        self.save_images_to_tags.setObjectName(_fromUtf8("save_images_to_tags"))
        self.vboxlayout.addWidget(self.save_images_to_tags)
        self.cb_embed_front_only = QtGui.QCheckBox(self.location)
        self.cb_embed_front_only.setObjectName(_fromUtf8("cb_embed_front_only"))
        self.vboxlayout.addWidget(self.cb_embed_front_only)
        self.save_images_to_files = QtGui.QCheckBox(self.location)
        self.save_images_to_files.setObjectName(_fromUtf8("save_images_to_files"))
        self.vboxlayout.addWidget(self.save_images_to_files)
        self.label_use_filename = QtGui.QLabel(self.location)
        self.label_use_filename.setObjectName(_fromUtf8("label_use_filename"))
        self.vboxlayout.addWidget(self.label_use_filename)
        self.cover_image_filename = QtGui.QLineEdit(self.location)
        self.cover_image_filename.setObjectName(_fromUtf8("cover_image_filename"))
        self.vboxlayout.addWidget(self.cover_image_filename)
        self.save_images_overwrite = QtGui.QCheckBox(self.location)
        self.save_images_overwrite.setObjectName(_fromUtf8("save_images_overwrite"))
        self.vboxlayout.addWidget(self.save_images_overwrite)
        self.verticalLayout.addWidget(self.location)
        self.ca_providers_groupbox = QtGui.QGroupBox(CoverOptionsPage)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ca_providers_groupbox.sizePolicy().hasHeightForWidth())
        self.ca_providers_groupbox.setSizePolicy(sizePolicy)
        self.ca_providers_groupbox.setObjectName(_fromUtf8("ca_providers_groupbox"))
        self.ca_providers_layout = QtGui.QVBoxLayout(self.ca_providers_groupbox)
        self.ca_providers_layout.setObjectName(_fromUtf8("ca_providers_layout"))
        self.ca_providers_list = QtGui.QHBoxLayout()
        self.ca_providers_list.setObjectName(_fromUtf8("ca_providers_list"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.ca_providers_list.addItem(spacerItem)
        self.ca_providers_layout.addLayout(self.ca_providers_list)
        self.verticalLayout.addWidget(self.ca_providers_groupbox)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)

        self.retranslateUi(CoverOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CoverOptionsPage)
        CoverOptionsPage.setTabOrder(self.save_images_to_tags, self.cb_embed_front_only)
        CoverOptionsPage.setTabOrder(self.cb_embed_front_only, self.save_images_to_files)
        CoverOptionsPage.setTabOrder(self.save_images_to_files, self.cover_image_filename)
        CoverOptionsPage.setTabOrder(self.cover_image_filename, self.save_images_overwrite)

    def retranslateUi(self, CoverOptionsPage):
        self.location.setTitle(_("Location"))
        self.save_images_to_tags.setText(_("Embed cover images into tags"))
        self.cb_embed_front_only.setText(_("Only embed a front image"))
        self.save_images_to_files.setText(_("Save cover images as separate files"))
        self.label_use_filename.setText(_("Use the following file name for images:"))
        self.save_images_overwrite.setText(_("Overwrite the file if it already exists"))
        self.ca_providers_groupbox.setTitle(_("Cover Art Providers"))

