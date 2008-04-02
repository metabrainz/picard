# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_interface.ui'
#
# Created: Thu Apr  3 00:22:10 2008
#      by: PyQt4 UI code generator 4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_InterfaceOptionsPage(object):
    def setupUi(self, InterfaceOptionsPage):
        InterfaceOptionsPage.setObjectName("InterfaceOptionsPage")
        InterfaceOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,295,196).size()).expandedTo(InterfaceOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(InterfaceOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")

        self.groupBox_2 = QtGui.QGroupBox(InterfaceOptionsPage)
        self.groupBox_2.setObjectName("groupBox_2")

        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox_2)
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.toolbar_show_labels = QtGui.QCheckBox(self.groupBox_2)
        self.toolbar_show_labels.setObjectName("toolbar_show_labels")
        self.vboxlayout1.addWidget(self.toolbar_show_labels)

        self.toolbar_multiselect = QtGui.QCheckBox(self.groupBox_2)
        self.toolbar_multiselect.setObjectName("toolbar_multiselect")
        self.vboxlayout1.addWidget(self.toolbar_multiselect)

        self.show_hidden_files = QtGui.QCheckBox(self.groupBox_2)
        self.show_hidden_files.setObjectName("show_hidden_files")
        self.vboxlayout1.addWidget(self.show_hidden_files)

        self.use_adv_search_syntax = QtGui.QCheckBox(self.groupBox_2)
        self.use_adv_search_syntax.setObjectName("use_adv_search_syntax")
        self.vboxlayout1.addWidget(self.use_adv_search_syntax)
        self.vboxlayout.addWidget(self.groupBox_2)

        spacerItem = QtGui.QSpacerItem(220,61,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(InterfaceOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(InterfaceOptionsPage)

    def retranslateUi(self, InterfaceOptionsPage):
        self.groupBox_2.setTitle(_("Miscellaneous"))
        self.toolbar_show_labels.setText(_("Show text labels under icons"))
        self.toolbar_multiselect.setText(_("Allow selection of multiple directories"))
        self.show_hidden_files.setText(_("Show hidden files in file browser"))
        self.use_adv_search_syntax.setText(_("Use advanced query syntax"))

