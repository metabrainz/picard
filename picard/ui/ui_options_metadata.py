# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_metadata.ui'
#
# Created: Tue Apr  1 21:09:17 2008
#      by: PyQt4 UI code generator 4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MetadataOptionsPage(object):
    def setupUi(self, MetadataOptionsPage):
        MetadataOptionsPage.setObjectName("MetadataOptionsPage")
        MetadataOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,415,355).size()).expandedTo(MetadataOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(MetadataOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")

        self.rename_files = QtGui.QGroupBox(MetadataOptionsPage)
        self.rename_files.setObjectName("rename_files")

        self.gridlayout = QtGui.QGridLayout(self.rename_files)
        self.gridlayout.setObjectName("gridlayout")

        self.translate_artist_names = QtGui.QCheckBox(self.rename_files)
        self.translate_artist_names.setObjectName("translate_artist_names")
        self.gridlayout.addWidget(self.translate_artist_names,0,0,1,1)

        self.release_ars = QtGui.QCheckBox(self.rename_files)
        self.release_ars.setObjectName("release_ars")
        self.gridlayout.addWidget(self.release_ars,1,0,1,1)

        self.track_ars = QtGui.QCheckBox(self.rename_files)
        self.track_ars.setObjectName("track_ars")
        self.gridlayout.addWidget(self.track_ars,2,0,1,1)

        self.folksonomy_tags = QtGui.QCheckBox(self.rename_files)
        self.folksonomy_tags.setObjectName("folksonomy_tags")
        self.gridlayout.addWidget(self.folksonomy_tags,3,0,1,1)

        self.preferred_release_country = QtGui.QComboBox(self.rename_files)
        self.preferred_release_country.setObjectName("preferred_release_country")
        self.gridlayout.addWidget(self.preferred_release_country,5,0,1,1)

        self.label = QtGui.QLabel(self.rename_files)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label,4,0,1,1)
        self.vboxlayout.addWidget(self.rename_files)

        self.rename_files_2 = QtGui.QGroupBox(MetadataOptionsPage)
        self.rename_files_2.setObjectName("rename_files_2")

        self.gridlayout1 = QtGui.QGridLayout(self.rename_files_2)
        self.gridlayout1.setMargin(9)
        self.gridlayout1.setSpacing(2)
        self.gridlayout1.setObjectName("gridlayout1")

        self.label_3 = QtGui.QLabel(self.rename_files_2)
        self.label_3.setObjectName("label_3")
        self.gridlayout1.addWidget(self.label_3,0,0,1,2)

        self.label_4 = QtGui.QLabel(self.rename_files_2)
        self.label_4.setObjectName("label_4")
        self.gridlayout1.addWidget(self.label_4,2,0,1,2)

        self.nat_name = QtGui.QLineEdit(self.rename_files_2)
        self.nat_name.setObjectName("nat_name")
        self.gridlayout1.addWidget(self.nat_name,3,0,1,1)

        self.nat_name_default = QtGui.QPushButton(self.rename_files_2)
        self.nat_name_default.setObjectName("nat_name_default")
        self.gridlayout1.addWidget(self.nat_name_default,3,1,1,1)

        self.va_name_default = QtGui.QPushButton(self.rename_files_2)
        self.va_name_default.setObjectName("va_name_default")
        self.gridlayout1.addWidget(self.va_name_default,1,1,1,1)

        self.va_name = QtGui.QLineEdit(self.rename_files_2)
        self.va_name.setObjectName("va_name")
        self.gridlayout1.addWidget(self.va_name,1,0,1,1)
        self.vboxlayout.addWidget(self.rename_files_2)

        spacerItem = QtGui.QSpacerItem(331,41,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_3.setBuddy(self.va_name_default)
        self.label_4.setBuddy(self.nat_name_default)

        self.retranslateUi(MetadataOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MetadataOptionsPage)
        MetadataOptionsPage.setTabOrder(self.translate_artist_names,self.va_name)
        MetadataOptionsPage.setTabOrder(self.va_name,self.va_name_default)
        MetadataOptionsPage.setTabOrder(self.va_name_default,self.nat_name)
        MetadataOptionsPage.setTabOrder(self.nat_name,self.nat_name_default)

    def retranslateUi(self, MetadataOptionsPage):
        self.rename_files.setTitle(_("Metadata"))
        self.translate_artist_names.setText(_("Translate foreign artist names to English where possible"))
        self.release_ars.setText(_("Use release relationships"))
        self.track_ars.setText(_("Use track relationships"))
        self.folksonomy_tags.setText(_("Use folksonomy tags as genre"))
        self.label.setText(_("Preferred release country:"))
        self.rename_files_2.setTitle(_("Custom Fields"))
        self.label_3.setText(_("Various artists:"))
        self.label_4.setText(_("Non-album tracks:"))
        self.nat_name_default.setText(_("Default"))
        self.va_name_default.setText(_("Default"))

