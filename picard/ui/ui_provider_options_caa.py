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

class Ui_CaaOptions(object):
    def setupUi(self, CaaOptions):
        CaaOptions.setObjectName(_fromUtf8("CaaOptions"))
        CaaOptions.resize(586, 194)
        self.verticalLayout = QtGui.QVBoxLayout(CaaOptions)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.select_caa_types_group = QtGui.QHBoxLayout()
        self.select_caa_types_group.setObjectName(_fromUtf8("select_caa_types_group"))
        self.restrict_images_types = QtGui.QCheckBox(CaaOptions)
        self.restrict_images_types.setObjectName(_fromUtf8("restrict_images_types"))
        self.select_caa_types_group.addWidget(self.restrict_images_types)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.select_caa_types_group.addItem(spacerItem)
        self.select_caa_types = QtGui.QPushButton(CaaOptions)
        self.select_caa_types.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.select_caa_types.sizePolicy().hasHeightForWidth())
        self.select_caa_types.setSizePolicy(sizePolicy)
        self.select_caa_types.setObjectName(_fromUtf8("select_caa_types"))
        self.select_caa_types_group.addWidget(self.select_caa_types)
        self.verticalLayout.addLayout(self.select_caa_types_group)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(CaaOptions)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.cb_image_size = QtGui.QComboBox(CaaOptions)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cb_image_size.sizePolicy().hasHeightForWidth())
        self.cb_image_size.setSizePolicy(sizePolicy)
        self.cb_image_size.setObjectName(_fromUtf8("cb_image_size"))
        self.cb_image_size.addItem(_fromUtf8(""))
        self.cb_image_size.addItem(_fromUtf8(""))
        self.cb_image_size.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.cb_image_size)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.cb_save_single_front_image = QtGui.QCheckBox(CaaOptions)
        self.cb_save_single_front_image.setObjectName(_fromUtf8("cb_save_single_front_image"))
        self.verticalLayout.addWidget(self.cb_save_single_front_image)
        self.cb_approved_only = QtGui.QCheckBox(CaaOptions)
        self.cb_approved_only.setObjectName(_fromUtf8("cb_approved_only"))
        self.verticalLayout.addWidget(self.cb_approved_only)
        self.cb_type_as_filename = QtGui.QCheckBox(CaaOptions)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cb_type_as_filename.sizePolicy().hasHeightForWidth())
        self.cb_type_as_filename.setSizePolicy(sizePolicy)
        self.cb_type_as_filename.setObjectName(_fromUtf8("cb_type_as_filename"))
        self.verticalLayout.addWidget(self.cb_type_as_filename)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)

        self.retranslateUi(CaaOptions)
        QtCore.QMetaObject.connectSlotsByName(CaaOptions)

    def retranslateUi(self, CaaOptions):
        CaaOptions.setWindowTitle(_("Form"))
        self.restrict_images_types.setText(_("Download only cover art images matching selected types"))
        self.select_caa_types.setText(_("Select types..."))
        self.label.setText(_("Only use images of the following size:"))
        self.cb_image_size.setItemText(0, _("250 px"))
        self.cb_image_size.setItemText(1, _("500 px"))
        self.cb_image_size.setItemText(2, _("Full size"))
        self.cb_save_single_front_image.setText(_("Save only one front image as separate file"))
        self.cb_approved_only.setText(_("Download only approved images"))
        self.cb_type_as_filename.setText(_("Use the first image type as the filename. This will not change the filename of front images."))

