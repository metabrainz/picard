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
        spacerItem = QtWidgets.QSpacerItem(274, 41, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(TagsCompatibilityOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(TagsCompatibilityOptionsPage)

    def retranslateUi(self, TagsCompatibilityOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.aac_tags.setTitle(_("AAC files"))
        self.aac_save_ape.setText(_("Save APEv2 tags"))
        self.aac_no_tags.setText(_("Do not save tags"))
        self.remove_ape_from_aac.setText(_("Remove APEv2 tags from AAC files"))
