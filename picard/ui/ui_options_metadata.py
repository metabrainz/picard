# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_metadata.ui'
#
# Created: Sun Jan 13 17:42:15 2008
#      by: PyQt4 UI code generator 4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MetadataOptionsPage(object):
    def setupUi(self, MetadataOptionsPage):
        MetadataOptionsPage.setObjectName("MetadataOptionsPage")
        MetadataOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,344,356).size()).expandedTo(MetadataOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(MetadataOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.rename_files = QtGui.QGroupBox(MetadataOptionsPage)
        self.rename_files.setObjectName("rename_files")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.rename_files)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.translate_artist_names = QtGui.QCheckBox(self.rename_files)
        self.translate_artist_names.setObjectName("translate_artist_names")
        self.vboxlayout1.addWidget(self.translate_artist_names)

        self.release_ars = QtGui.QCheckBox(self.rename_files)
        self.release_ars.setObjectName("release_ars")
        self.vboxlayout1.addWidget(self.release_ars)

        self.track_ars = QtGui.QCheckBox(self.rename_files)
        self.track_ars.setObjectName("track_ars")
        self.vboxlayout1.addWidget(self.track_ars)
        self.vboxlayout.addWidget(self.rename_files)

        self.rename_files_2 = QtGui.QGroupBox(MetadataOptionsPage)
        self.rename_files_2.setObjectName("rename_files_2")

        self.gridlayout = QtGui.QGridLayout(self.rename_files_2)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        self.label_3 = QtGui.QLabel(self.rename_files_2)
        self.label_3.setObjectName("label_3")
        self.gridlayout.addWidget(self.label_3,0,0,1,2)

        self.label_4 = QtGui.QLabel(self.rename_files_2)
        self.label_4.setObjectName("label_4")
        self.gridlayout.addWidget(self.label_4,2,0,1,2)

        self.nat_name = QtGui.QLineEdit(self.rename_files_2)
        self.nat_name.setObjectName("nat_name")
        self.gridlayout.addWidget(self.nat_name,3,0,1,1)

        self.nat_name_default = QtGui.QPushButton(self.rename_files_2)
        self.nat_name_default.setObjectName("nat_name_default")
        self.gridlayout.addWidget(self.nat_name_default,3,1,1,1)

        self.va_name_default = QtGui.QPushButton(self.rename_files_2)
        self.va_name_default.setObjectName("va_name_default")
        self.gridlayout.addWidget(self.va_name_default,1,1,1,1)

        self.va_name = QtGui.QLineEdit(self.rename_files_2)
        self.va_name.setObjectName("va_name")
        self.gridlayout.addWidget(self.va_name,1,0,1,1)
        self.vboxlayout.addWidget(self.rename_files_2)

        spacerItem = QtGui.QSpacerItem(326,51,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
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
        self.rename_files_2.setTitle(_("Custom Fields"))
        self.label_3.setText(_("Various artists:"))
        self.label_4.setText(_("Non-album tracks:"))
        self.nat_name_default.setText(_("Default"))
        self.va_name_default.setText(_("Default"))

