# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_interface.ui'
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

class Ui_InterfaceOptionsPage(object):
    def setupUi(self, InterfaceOptionsPage):
        InterfaceOptionsPage.setObjectName(_fromUtf8("InterfaceOptionsPage"))
        InterfaceOptionsPage.resize(421, 212)
        self.vboxlayout = QtGui.QVBoxLayout(InterfaceOptionsPage)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.groupBox_2 = QtGui.QGroupBox(InterfaceOptionsPage)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox_2)
        self.vboxlayout1.setObjectName(_fromUtf8("vboxlayout1"))
        self.toolbar_show_labels = QtGui.QCheckBox(self.groupBox_2)
        self.toolbar_show_labels.setObjectName(_fromUtf8("toolbar_show_labels"))
        self.vboxlayout1.addWidget(self.toolbar_show_labels)
        self.toolbar_multiselect = QtGui.QCheckBox(self.groupBox_2)
        self.toolbar_multiselect.setObjectName(_fromUtf8("toolbar_multiselect"))
        self.vboxlayout1.addWidget(self.toolbar_multiselect)
        self.use_adv_search_syntax = QtGui.QCheckBox(self.groupBox_2)
        self.use_adv_search_syntax.setObjectName(_fromUtf8("use_adv_search_syntax"))
        self.vboxlayout1.addWidget(self.use_adv_search_syntax)
        self.quit_confirmation = QtGui.QCheckBox(self.groupBox_2)
        self.quit_confirmation.setObjectName(_fromUtf8("quit_confirmation"))
        self.vboxlayout1.addWidget(self.quit_confirmation)
        self.label = QtGui.QLabel(self.groupBox_2)
        self.label.setObjectName(_fromUtf8("label"))
        self.vboxlayout1.addWidget(self.label)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.ui_language = QtGui.QComboBox(self.groupBox_2)
        self.ui_language.setObjectName(_fromUtf8("ui_language"))
        self.horizontalLayout.addWidget(self.ui_language)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.vboxlayout1.addLayout(self.horizontalLayout)
        self.vboxlayout.addWidget(self.groupBox_2)
        spacerItem1 = QtGui.QSpacerItem(220, 61, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)

        self.retranslateUi(InterfaceOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(InterfaceOptionsPage)

    def retranslateUi(self, InterfaceOptionsPage):
        self.groupBox_2.setTitle(_("Miscellaneous"))
        self.toolbar_show_labels.setText(_("Show text labels under icons"))
        self.toolbar_multiselect.setText(_("Allow selection of multiple directories"))
        self.use_adv_search_syntax.setText(_("Use advanced query syntax"))
        self.quit_confirmation.setText(_("Show a quit confirmation dialog for unsaved changes"))
        self.label.setText(_("User interface language:"))

