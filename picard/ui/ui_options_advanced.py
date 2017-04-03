# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AdvancedOptionsPage(object):
    def setupUi(self, AdvancedOptionsPage):
        AdvancedOptionsPage.setObjectName("AdvancedOptionsPage")
        AdvancedOptionsPage.resize(570, 435)
        self.vboxlayout = QtWidgets.QVBoxLayout(AdvancedOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.groupBox = QtWidgets.QGroupBox(AdvancedOptionsPage)
        self.groupBox.setObjectName("groupBox")
        self.gridlayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")
        self.regex_error = QtWidgets.QLabel(self.groupBox)
        self.regex_error.setText("")
        self.regex_error.setObjectName("regex_error")
        self.gridlayout.addWidget(self.regex_error, 3, 0, 1, 1)
        self.label_ignore_regex = QtWidgets.QLabel(self.groupBox)
        self.label_ignore_regex.setObjectName("label_ignore_regex")
        self.gridlayout.addWidget(self.label_ignore_regex, 1, 0, 1, 1)
        self.ignore_hidden_files = QtWidgets.QCheckBox(self.groupBox)
        self.ignore_hidden_files.setObjectName("ignore_hidden_files")
        self.gridlayout.addWidget(self.ignore_hidden_files, 4, 0, 1, 1)
        self.ignore_regex = QtWidgets.QLineEdit(self.groupBox)
        self.ignore_regex.setObjectName("ignore_regex")
        self.gridlayout.addWidget(self.ignore_regex, 2, 0, 1, 1)
        self.recursively_add_files = QtWidgets.QCheckBox(self.groupBox)
        self.recursively_add_files.setObjectName("recursively_add_files")
        self.gridlayout.addWidget(self.recursively_add_files, 5, 0, 1, 1)
        self.vboxlayout.addWidget(self.groupBox)
        self.groupBox_completeness = QtWidgets.QGroupBox(AdvancedOptionsPage)
        self.groupBox_completeness.setObjectName("groupBox_completeness")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_completeness)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.completeness_ignore_videos = QtWidgets.QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_videos.setObjectName("completeness_ignore_videos")
        self.verticalLayout_2.addWidget(self.completeness_ignore_videos)
        self.completeness_ignore_pregap = QtWidgets.QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_pregap.setObjectName("completeness_ignore_pregap")
        self.verticalLayout_2.addWidget(self.completeness_ignore_pregap)
        self.completeness_ignore_data = QtWidgets.QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_data.setCheckable(True)
        self.completeness_ignore_data.setObjectName("completeness_ignore_data")
        self.verticalLayout_2.addWidget(self.completeness_ignore_data)
        self.completeness_ignore_silence = QtWidgets.QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_silence.setObjectName("completeness_ignore_silence")
        self.verticalLayout_2.addWidget(self.completeness_ignore_silence)
        self.vboxlayout.addWidget(self.groupBox_completeness)
        spacerItem = QtWidgets.QSpacerItem(181, 21, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(AdvancedOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(AdvancedOptionsPage)

    def retranslateUi(self, AdvancedOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.groupBox.setTitle(_("Advanced options"))
        self.label_ignore_regex.setText(_("Ignore file paths matching the following regular expression:"))
        self.ignore_hidden_files.setText(_("Ignore hidden files"))
        self.recursively_add_files.setText(_("Recursively add files and folders from directory"))
        self.groupBox_completeness.setTitle(_("Ignore the following tracks when determining whether a release is complete"))
        self.completeness_ignore_videos.setText(_("Video tracks"))
        self.completeness_ignore_pregap.setText(_("Pregap tracks"))
        self.completeness_ignore_data.setText(_("Data tracks"))
        self.completeness_ignore_silence.setText(_("Silent tracks"))

