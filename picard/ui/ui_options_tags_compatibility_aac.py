# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_TagsCompatibilityOptionsPage(object):
    def setupUi(self, TagsCompatibilityOptionsPage):
        TagsCompatibilityOptionsPage.setObjectName("TagsCompatibilityOptionsPage")
        TagsCompatibilityOptionsPage.resize(539, 705)
        self.vboxlayout = QtWidgets.QVBoxLayout(TagsCompatibilityOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.aac_tags = QtWidgets.QGroupBox(TagsCompatibilityOptionsPage)
        self.aac_tags.setObjectName("aac_tags")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.aac_tags)
        self.verticalLayout.setObjectName("verticalLayout")
        self.info_label = QtWidgets.QLabel(self.aac_tags)
        self.info_label.setWordWrap(True)
        self.info_label.setObjectName("info_label")
        self.verticalLayout.addWidget(self.info_label)
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.aac_save_ape = QtWidgets.QRadioButton(self.aac_tags)
        self.aac_save_ape.setChecked(True)
        self.aac_save_ape.setObjectName("aac_save_ape")
        self.verticalLayout.addWidget(self.aac_save_ape)
        self.aac_no_tags = QtWidgets.QRadioButton(self.aac_tags)
        self.aac_no_tags.setObjectName("aac_no_tags")
        self.verticalLayout.addWidget(self.aac_no_tags)
        self.remove_ape_from_aac = QtWidgets.QCheckBox(self.aac_tags)
        self.remove_ape_from_aac.setObjectName("remove_ape_from_aac")
        self.verticalLayout.addWidget(self.remove_ape_from_aac)
        self.vboxlayout.addWidget(self.aac_tags)
        spacerItem1 = QtWidgets.QSpacerItem(274, 41, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)

        self.retranslateUi(TagsCompatibilityOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(TagsCompatibilityOptionsPage)

    def retranslateUi(self, TagsCompatibilityOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.aac_tags.setTitle(_("AAC files"))
        self.info_label.setText(_("Picard can save APEv2 tags to pure AAC files, which by default do not support tagging. APEv2 tags in AAC are supported by some players, but players not supporting AAC files with APEv2 tags can have issues loading and playing those files. To deal with this you can choose whether to save tags to those files."))
        self.aac_save_ape.setText(_("Save APEv2 tags"))
        self.aac_no_tags.setText(_("Do not save tags"))
        self.remove_ape_from_aac.setText(_("Remove APEv2 tags from AAC files"))
