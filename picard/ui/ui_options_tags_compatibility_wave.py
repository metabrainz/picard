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
        self.wave_files = QtWidgets.QGroupBox(TagsCompatibilityOptionsPage)
        self.wave_files.setObjectName("wave_files")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.wave_files)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label = QtWidgets.QLabel(self.wave_files)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout_3.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout_3.addItem(spacerItem)
        self.write_wave_riff_info = QtWidgets.QCheckBox(self.wave_files)
        self.write_wave_riff_info.setObjectName("write_wave_riff_info")
        self.verticalLayout_3.addWidget(self.write_wave_riff_info)
        self.remove_wave_riff_info = QtWidgets.QCheckBox(self.wave_files)
        self.remove_wave_riff_info.setObjectName("remove_wave_riff_info")
        self.verticalLayout_3.addWidget(self.remove_wave_riff_info)
        self.wave_riff_info_encoding = QtWidgets.QGroupBox(self.wave_files)
        self.wave_riff_info_encoding.setObjectName("wave_riff_info_encoding")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.wave_riff_info_encoding)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.wave_riff_info_enc_cp1252 = QtWidgets.QRadioButton(self.wave_riff_info_encoding)
        self.wave_riff_info_enc_cp1252.setChecked(True)
        self.wave_riff_info_enc_cp1252.setObjectName("wave_riff_info_enc_cp1252")
        self.horizontalLayout_3.addWidget(self.wave_riff_info_enc_cp1252)
        self.wave_riff_info_enc_utf8 = QtWidgets.QRadioButton(self.wave_riff_info_encoding)
        self.wave_riff_info_enc_utf8.setObjectName("wave_riff_info_enc_utf8")
        self.horizontalLayout_3.addWidget(self.wave_riff_info_enc_utf8)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.verticalLayout_3.addWidget(self.wave_riff_info_encoding)
        self.vboxlayout.addWidget(self.wave_files)
        spacerItem2 = QtWidgets.QSpacerItem(274, 41, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem2)

        self.retranslateUi(TagsCompatibilityOptionsPage)
        self.write_wave_riff_info.toggled['bool'].connect(self.remove_wave_riff_info.setDisabled)
        QtCore.QMetaObject.connectSlotsByName(TagsCompatibilityOptionsPage)

    def retranslateUi(self, TagsCompatibilityOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.wave_files.setTitle(_("WAVE files"))
        self.label.setText(_("Picard will tag WAVE files using ID3v2 tags. This is not supported by all software. For compatibility with software which does not support ID3v2 tags in WAVE files additional RIFF INFO tags can be written to the files. RIFF INFO has only limited support for tags and character encodings."))
        self.write_wave_riff_info.setText(_("Also include RIFF INFO tags in the files"))
        self.remove_wave_riff_info.setText(_("Remove existing RIFF INFO tags from WAVE files"))
        self.wave_riff_info_encoding.setTitle(_("RIFF INFO Text Encoding"))
        self.wave_riff_info_enc_cp1252.setText(_("Windows-1252"))
        self.wave_riff_info_enc_utf8.setText(_("UTF-8"))
