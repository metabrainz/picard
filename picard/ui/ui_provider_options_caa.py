# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CaaOptions(object):
    def setupUi(self, CaaOptions):
        CaaOptions.setObjectName("CaaOptions")
        CaaOptions.resize(660, 194)
        self.verticalLayout = QtWidgets.QVBoxLayout(CaaOptions)
        self.verticalLayout.setObjectName("verticalLayout")
        self.select_caa_types_group = QtWidgets.QHBoxLayout()
        self.select_caa_types_group.setObjectName("select_caa_types_group")
        self.restrict_images_types = QtWidgets.QCheckBox(CaaOptions)
        self.restrict_images_types.setObjectName("restrict_images_types")
        self.select_caa_types_group.addWidget(self.restrict_images_types)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.select_caa_types_group.addItem(spacerItem)
        self.select_caa_types = QtWidgets.QPushButton(CaaOptions)
        self.select_caa_types.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.select_caa_types.sizePolicy().hasHeightForWidth())
        self.select_caa_types.setSizePolicy(sizePolicy)
        self.select_caa_types.setObjectName("select_caa_types")
        self.select_caa_types_group.addWidget(self.select_caa_types)
        self.verticalLayout.addLayout(self.select_caa_types_group)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(CaaOptions)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.cb_image_size = QtWidgets.QComboBox(CaaOptions)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cb_image_size.sizePolicy().hasHeightForWidth())
        self.cb_image_size.setSizePolicy(sizePolicy)
        self.cb_image_size.setObjectName("cb_image_size")
        self.horizontalLayout.addWidget(self.cb_image_size)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.cb_approved_only = QtWidgets.QCheckBox(CaaOptions)
        self.cb_approved_only.setObjectName("cb_approved_only")
        self.verticalLayout.addWidget(self.cb_approved_only)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)

        self.retranslateUi(CaaOptions)
        QtCore.QMetaObject.connectSlotsByName(CaaOptions)
        CaaOptions.setTabOrder(self.restrict_images_types, self.select_caa_types)
        CaaOptions.setTabOrder(self.select_caa_types, self.cb_image_size)
        CaaOptions.setTabOrder(self.cb_image_size, self.cb_approved_only)

    def retranslateUi(self, CaaOptions):
        _translate = QtCore.QCoreApplication.translate
        CaaOptions.setWindowTitle(_("Form"))
        self.restrict_images_types.setText(_("Download only cover art images matching selected types"))
        self.select_caa_types.setText(_("Select types..."))
        self.label.setText(_("Only use images of the following size:"))
        self.cb_approved_only.setText(_("Download only approved images"))
