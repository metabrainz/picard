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

class Ui_AdvancedOptionsPage(object):
    def setupUi(self, AdvancedOptionsPage):
        AdvancedOptionsPage.setObjectName(_fromUtf8("AdvancedOptionsPage"))
        AdvancedOptionsPage.resize(392, 435)
        self.vboxlayout = QtGui.QVBoxLayout(AdvancedOptionsPage)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.groupBox = QtGui.QGroupBox(AdvancedOptionsPage)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridlayout = QtGui.QGridLayout(self.groupBox)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.label_ignore_regex = QtGui.QLabel(self.groupBox)
        self.label_ignore_regex.setObjectName(_fromUtf8("label_ignore_regex"))
        self.gridlayout.addWidget(self.label_ignore_regex, 1, 0, 1, 1)
        self.ignore_regex = QtGui.QLineEdit(self.groupBox)
        self.ignore_regex.setObjectName(_fromUtf8("ignore_regex"))
        self.gridlayout.addWidget(self.ignore_regex, 2, 0, 1, 1)
        self.ignore_hidden_files = QtGui.QCheckBox(self.groupBox)
        self.ignore_hidden_files.setObjectName(_fromUtf8("ignore_hidden_files"))
        self.gridlayout.addWidget(self.ignore_hidden_files, 4, 0, 1, 1)
        self.regex_error = QtGui.QLabel(self.groupBox)
        self.regex_error.setText(_fromUtf8(""))
        self.regex_error.setObjectName(_fromUtf8("regex_error"))
        self.gridlayout.addWidget(self.regex_error, 3, 0, 1, 1)
        self.vboxlayout.addWidget(self.groupBox)
        self.groupBox_completeness = QtGui.QGroupBox(AdvancedOptionsPage)
        self.groupBox_completeness.setObjectName(_fromUtf8("groupBox_completeness"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox_completeness)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.completeness_ignore_videos = QtGui.QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_videos.setObjectName(_fromUtf8("completeness_ignore_videos"))
        self.verticalLayout_2.addWidget(self.completeness_ignore_videos)
        self.completeness_ignore_pregap = QtGui.QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_pregap.setObjectName(_fromUtf8("completeness_ignore_pregap"))
        self.verticalLayout_2.addWidget(self.completeness_ignore_pregap)
        self.completeness_ignore_data = QtGui.QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_data.setCheckable(True)
        self.completeness_ignore_data.setObjectName(_fromUtf8("completeness_ignore_data"))
        self.verticalLayout_2.addWidget(self.completeness_ignore_data)
        self.completeness_ignore_silence = QtGui.QCheckBox(self.groupBox_completeness)
        self.completeness_ignore_silence.setObjectName(_fromUtf8("completeness_ignore_silence"))
        self.verticalLayout_2.addWidget(self.completeness_ignore_silence)
        self.vboxlayout.addWidget(self.groupBox_completeness)
        spacerItem = QtGui.QSpacerItem(181, 21, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(AdvancedOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(AdvancedOptionsPage)

    def retranslateUi(self, AdvancedOptionsPage):
        self.groupBox.setTitle(_("Advanced options"))
        self.label_ignore_regex.setText(_("Ignore file paths matching the following regular expression:"))
        self.ignore_hidden_files.setText(_("Ignore hidden files"))
        self.groupBox_completeness.setTitle(_("Ignore the following tracks when determining whether a release is complete"))
        self.completeness_ignore_videos.setText(_("Video tracks"))
        self.completeness_ignore_pregap.setText(_("Pregap tracks"))
        self.completeness_ignore_data.setText(_("Data tracks"))
        self.completeness_ignore_silence.setText(_("Silent tracks"))

