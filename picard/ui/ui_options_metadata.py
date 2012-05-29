# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_metadata.ui'
#
# Created: Tue May 29 19:44:14 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MetadataOptionsPage(object):
    def setupUi(self, MetadataOptionsPage):
        MetadataOptionsPage.setObjectName(_fromUtf8("MetadataOptionsPage"))
        MetadataOptionsPage.resize(423, 553)
        self.verticalLayout = QtGui.QVBoxLayout(MetadataOptionsPage)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.rename_files = QtGui.QGroupBox(MetadataOptionsPage)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rename_files.sizePolicy().hasHeightForWidth())
        self.rename_files.setSizePolicy(sizePolicy)
        self.rename_files.setMinimumSize(QtCore.QSize(397, 135))
        font = QtGui.QFont()
        self.rename_files.setFont(font)
        self.rename_files.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.rename_files.setObjectName(_fromUtf8("rename_files"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.rename_files)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.translate_artist_names = QtGui.QCheckBox(self.rename_files)
        self.translate_artist_names.setObjectName(_fromUtf8("translate_artist_names"))
        self.verticalLayout_3.addWidget(self.translate_artist_names)
        self.artist_locale = QtGui.QComboBox(self.rename_files)
        self.artist_locale.setObjectName(_fromUtf8("artist_locale"))
        self.verticalLayout_3.addWidget(self.artist_locale)
        self.standardize_artists = QtGui.QCheckBox(self.rename_files)
        self.standardize_artists.setObjectName(_fromUtf8("standardize_artists"))
        self.verticalLayout_3.addWidget(self.standardize_artists)
        self.convert_punctuation = QtGui.QCheckBox(self.rename_files)
        self.convert_punctuation.setObjectName(_fromUtf8("convert_punctuation"))
        self.verticalLayout_3.addWidget(self.convert_punctuation)
        self.release_ars = QtGui.QCheckBox(self.rename_files)
        self.release_ars.setObjectName(_fromUtf8("release_ars"))
        self.verticalLayout_3.addWidget(self.release_ars)
        self.track_ars = QtGui.QCheckBox(self.rename_files)
        self.track_ars.setObjectName(_fromUtf8("track_ars"))
        self.verticalLayout_3.addWidget(self.track_ars)
        self.folksonomy_tags = QtGui.QCheckBox(self.rename_files)
        self.folksonomy_tags.setObjectName(_fromUtf8("folksonomy_tags"))
        self.verticalLayout_3.addWidget(self.folksonomy_tags)
        self.verticalLayout.addWidget(self.rename_files)
        self.rename_files_3 = QtGui.QGroupBox(MetadataOptionsPage)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rename_files_3.sizePolicy().hasHeightForWidth())
        self.rename_files_3.setSizePolicy(sizePolicy)
        self.rename_files_3.setMinimumSize(QtCore.QSize(397, 0))
        self.rename_files_3.setObjectName(_fromUtf8("rename_files_3"))
        self.gridlayout = QtGui.QGridLayout(self.rename_files_3)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.label_6 = QtGui.QLabel(self.rename_files_3)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridlayout.addWidget(self.label_6, 0, 0, 1, 2)
        self.label_7 = QtGui.QLabel(self.rename_files_3)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.gridlayout.addWidget(self.label_7, 2, 0, 1, 2)
        self.nat_name = QtGui.QLineEdit(self.rename_files_3)
        self.nat_name.setObjectName(_fromUtf8("nat_name"))
        self.gridlayout.addWidget(self.nat_name, 3, 0, 1, 1)
        self.nat_name_default = QtGui.QPushButton(self.rename_files_3)
        self.nat_name_default.setObjectName(_fromUtf8("nat_name_default"))
        self.gridlayout.addWidget(self.nat_name_default, 3, 1, 1, 1)
        self.va_name_default = QtGui.QPushButton(self.rename_files_3)
        self.va_name_default.setObjectName(_fromUtf8("va_name_default"))
        self.gridlayout.addWidget(self.va_name_default, 1, 1, 1, 1)
        self.va_name = QtGui.QLineEdit(self.rename_files_3)
        self.va_name.setObjectName(_fromUtf8("va_name"))
        self.gridlayout.addWidget(self.va_name, 1, 0, 1, 1)
        self.verticalLayout.addWidget(self.rename_files_3)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.MinimumExpanding)
        self.verticalLayout.addItem(spacerItem)
        self.label_6.setBuddy(self.va_name_default)
        self.label_7.setBuddy(self.nat_name_default)

        self.retranslateUi(MetadataOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MetadataOptionsPage)
        MetadataOptionsPage.setTabOrder(self.translate_artist_names, self.va_name)
        MetadataOptionsPage.setTabOrder(self.va_name, self.va_name_default)
        MetadataOptionsPage.setTabOrder(self.va_name_default, self.nat_name)
        MetadataOptionsPage.setTabOrder(self.nat_name, self.nat_name_default)

    def retranslateUi(self, MetadataOptionsPage):
        self.rename_files.setTitle(_("Metadata"))
        self.translate_artist_names.setText(_("Translate artist names to this locale where possible:"))
        self.standardize_artists.setText(_("Use standardized artist names"))
        self.convert_punctuation.setText(_("Convert Unicode punctuation characters to ASCII"))
        self.release_ars.setText(_("Use release relationships"))
        self.track_ars.setText(_("Use track relationships"))
        self.folksonomy_tags.setText(_("Use folksonomy tags as genre"))
        self.rename_files_3.setTitle(_("Custom Fields"))
        self.label_6.setText(_("Various artists:"))
        self.label_7.setText(_("Non-album tracks:"))
        self.nat_name_default.setText(_("Default"))
        self.va_name_default.setText(_("Default"))

