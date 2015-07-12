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

class Ui_FolksonomyOptionsPage(object):
    def setupUi(self, FolksonomyOptionsPage):
        FolksonomyOptionsPage.setObjectName(_fromUtf8("FolksonomyOptionsPage"))
        FolksonomyOptionsPage.resize(590, 304)
        self.verticalLayout_2 = QtGui.QVBoxLayout(FolksonomyOptionsPage)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.rename_files_3 = QtGui.QGroupBox(FolksonomyOptionsPage)
        self.rename_files_3.setObjectName(_fromUtf8("rename_files_3"))
        self.verticalLayout = QtGui.QVBoxLayout(self.rename_files_3)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.ignore_tags_2 = QtGui.QLabel(self.rename_files_3)
        self.ignore_tags_2.setObjectName(_fromUtf8("ignore_tags_2"))
        self.verticalLayout.addWidget(self.ignore_tags_2)
        self.ignore_tags = QtGui.QLineEdit(self.rename_files_3)
        self.ignore_tags.setObjectName(_fromUtf8("ignore_tags"))
        self.verticalLayout.addWidget(self.ignore_tags)
        self.only_my_tags = QtGui.QCheckBox(self.rename_files_3)
        self.only_my_tags.setObjectName(_fromUtf8("only_my_tags"))
        self.verticalLayout.addWidget(self.only_my_tags)
        self.artists_tags = QtGui.QCheckBox(self.rename_files_3)
        self.artists_tags.setEnabled(True)
        self.artists_tags.setObjectName(_fromUtf8("artists_tags"))
        self.verticalLayout.addWidget(self.artists_tags)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.label_5 = QtGui.QLabel(self.rename_files_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.hboxlayout.addWidget(self.label_5)
        self.min_tag_usage = QtGui.QSpinBox(self.rename_files_3)
        self.min_tag_usage.setMaximum(100)
        self.min_tag_usage.setObjectName(_fromUtf8("min_tag_usage"))
        self.hboxlayout.addWidget(self.min_tag_usage)
        self.verticalLayout.addLayout(self.hboxlayout)
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setObjectName(_fromUtf8("hboxlayout1"))
        self.label_6 = QtGui.QLabel(self.rename_files_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.hboxlayout1.addWidget(self.label_6)
        self.max_tags = QtGui.QSpinBox(self.rename_files_3)
        self.max_tags.setMaximum(100)
        self.max_tags.setObjectName(_fromUtf8("max_tags"))
        self.hboxlayout1.addWidget(self.max_tags)
        self.verticalLayout.addLayout(self.hboxlayout1)
        self.hboxlayout2 = QtGui.QHBoxLayout()
        self.hboxlayout2.setSpacing(6)
        self.hboxlayout2.setMargin(0)
        self.hboxlayout2.setObjectName(_fromUtf8("hboxlayout2"))
        self.ignore_tags_4 = QtGui.QLabel(self.rename_files_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(4)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ignore_tags_4.sizePolicy().hasHeightForWidth())
        self.ignore_tags_4.setSizePolicy(sizePolicy)
        self.ignore_tags_4.setObjectName(_fromUtf8("ignore_tags_4"))
        self.hboxlayout2.addWidget(self.ignore_tags_4)
        self.join_tags = QtGui.QComboBox(self.rename_files_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.join_tags.sizePolicy().hasHeightForWidth())
        self.join_tags.setSizePolicy(sizePolicy)
        self.join_tags.setEditable(True)
        self.join_tags.setObjectName(_fromUtf8("join_tags"))
        self.join_tags.addItem(_fromUtf8(""))
        self.join_tags.setItemText(0, _fromUtf8(""))
        self.join_tags.addItem(_fromUtf8(""))
        self.join_tags.addItem(_fromUtf8(""))
        self.hboxlayout2.addWidget(self.join_tags)
        self.verticalLayout.addLayout(self.hboxlayout2)
        self.verticalLayout_2.addWidget(self.rename_files_3)
        spacerItem = QtGui.QSpacerItem(181, 31, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.label_5.setBuddy(self.min_tag_usage)
        self.label_6.setBuddy(self.min_tag_usage)

        self.retranslateUi(FolksonomyOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(FolksonomyOptionsPage)

    def retranslateUi(self, FolksonomyOptionsPage):
        self.rename_files_3.setTitle(_("Folksonomy Tags"))
        self.ignore_tags_2.setText(_("Ignore tags:"))
        self.only_my_tags.setText(_("Only use my tags"))
        self.artists_tags.setText(_("Fall back on album\'s artists tags if no tags are found for the release or release group"))
        self.label_5.setText(_("Minimal tag usage:"))
        self.min_tag_usage.setSuffix(_(" %"))
        self.label_6.setText(_("Maximum number of tags:"))
        self.ignore_tags_4.setText(_("Join multiple tags with:"))
        self.join_tags.setItemText(1, _(" / "))
        self.join_tags.setItemText(2, _(", "))

