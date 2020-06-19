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
        self.ac3_files = QtWidgets.QGroupBox(TagsCompatibilityOptionsPage)
        self.ac3_files.setObjectName("ac3_files")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.ac3_files)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.ac3_save_ape = QtWidgets.QRadioButton(self.ac3_files)
        self.ac3_save_ape.setChecked(True)
        self.ac3_save_ape.setObjectName("ac3_save_ape")
        self.verticalLayout_2.addWidget(self.ac3_save_ape)
        self.ac3_no_tags = QtWidgets.QRadioButton(self.ac3_files)
        self.ac3_no_tags.setObjectName("ac3_no_tags")
        self.verticalLayout_2.addWidget(self.ac3_no_tags)
        self.remove_ape_from_ac3 = QtWidgets.QCheckBox(self.ac3_files)
        self.remove_ape_from_ac3.setObjectName("remove_ape_from_ac3")
        self.verticalLayout_2.addWidget(self.remove_ape_from_ac3)
        self.vboxlayout.addWidget(self.ac3_files)
        spacerItem = QtWidgets.QSpacerItem(274, 41, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(TagsCompatibilityOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(TagsCompatibilityOptionsPage)

    def retranslateUi(self, TagsCompatibilityOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.ac3_files.setTitle(_("AC3 files"))
        self.ac3_save_ape.setText(_("Save APEv2 tags"))
        self.ac3_no_tags.setText(_("Do not save tags"))
        self.remove_ape_from_ac3.setText(_("Remove APEv2 tags from AC3 files"))
