# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import (QtCore,
                   QtWidgets)


class Ui_CoverOptionsPage(object):
    def setupUi(self, CoverOptionsPage):
        CoverOptionsPage.setObjectName("CoverOptionsPage")
        CoverOptionsPage.resize(632, 560)
        self.verticalLayout = QtWidgets.QVBoxLayout(CoverOptionsPage)
        self.verticalLayout.setObjectName("verticalLayout")
        self.location = QtWidgets.QGroupBox(CoverOptionsPage)
        self.location.setObjectName("location")
        self.vboxlayout = QtWidgets.QVBoxLayout(self.location)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(2)
        self.vboxlayout.setObjectName("vboxlayout")
        self.save_images_to_tags = QtWidgets.QCheckBox(self.location)
        self.save_images_to_tags.setObjectName("save_images_to_tags")
        self.vboxlayout.addWidget(self.save_images_to_tags)
        self.cb_embed_front_only = QtWidgets.QCheckBox(self.location)
        self.cb_embed_front_only.setObjectName("cb_embed_front_only")
        self.vboxlayout.addWidget(self.cb_embed_front_only)
        self.save_images_to_files = QtWidgets.QCheckBox(self.location)
        self.save_images_to_files.setObjectName("save_images_to_files")
        self.vboxlayout.addWidget(self.save_images_to_files)
        self.label_use_filename = QtWidgets.QLabel(self.location)
        self.label_use_filename.setObjectName("label_use_filename")
        self.vboxlayout.addWidget(self.label_use_filename)
        self.cover_image_filename = QtWidgets.QLineEdit(self.location)
        self.cover_image_filename.setObjectName("cover_image_filename")
        self.vboxlayout.addWidget(self.cover_image_filename)
        self.save_images_overwrite = QtWidgets.QCheckBox(self.location)
        self.save_images_overwrite.setObjectName("save_images_overwrite")
        self.vboxlayout.addWidget(self.save_images_overwrite)
        self.verticalLayout.addWidget(self.location)
        self.ca_providers_groupbox = QtWidgets.QGroupBox(CoverOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ca_providers_groupbox.sizePolicy().hasHeightForWidth())
        self.ca_providers_groupbox.setSizePolicy(sizePolicy)
        self.ca_providers_groupbox.setObjectName("ca_providers_groupbox")
        self.ca_providers_layout = QtWidgets.QVBoxLayout(self.ca_providers_groupbox)
        self.ca_providers_layout.setObjectName("ca_providers_layout")
        self.ca_providers_list = QtWidgets.QHBoxLayout()
        self.ca_providers_list.setObjectName("ca_providers_list")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Minimum)
        self.ca_providers_list.addItem(spacerItem)
        self.ca_providers_layout.addLayout(self.ca_providers_list)
        self.verticalLayout.addWidget(self.ca_providers_groupbox)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)

        self.retranslateUi(CoverOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(CoverOptionsPage)
        CoverOptionsPage.setTabOrder(self.save_images_to_tags, self.cb_embed_front_only)
        CoverOptionsPage.setTabOrder(self.cb_embed_front_only, self.save_images_to_files)
        CoverOptionsPage.setTabOrder(self.save_images_to_files, self.cover_image_filename)
        CoverOptionsPage.setTabOrder(self.cover_image_filename, self.save_images_overwrite)

    def retranslateUi(self, CoverOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.location.setTitle(_("Location"))
        self.save_images_to_tags.setText(_("Embed cover images into tags"))
        self.cb_embed_front_only.setText(_("Only embed a front image"))
        self.save_images_to_files.setText(_("Save cover images as separate files"))
        self.label_use_filename.setText(_("Use the following file name for images:"))
        self.save_images_overwrite.setText(_("Overwrite the file if it already exists"))
        self.ca_providers_groupbox.setTitle(_("Cover Art Providers"))
