# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_InterfaceOptionsPage(object):
    def setupUi(self, InterfaceOptionsPage):
        InterfaceOptionsPage.setObjectName("InterfaceOptionsPage")
        InterfaceOptionsPage.resize(421, 275)
        self.vboxlayout = QtWidgets.QVBoxLayout(InterfaceOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.groupBox_2 = QtWidgets.QGroupBox(InterfaceOptionsPage)
        self.groupBox_2.setObjectName("groupBox_2")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.toolbar_show_labels = QtWidgets.QCheckBox(self.groupBox_2)
        self.toolbar_show_labels.setObjectName("toolbar_show_labels")
        self.vboxlayout1.addWidget(self.toolbar_show_labels)
        self.toolbar_multiselect = QtWidgets.QCheckBox(self.groupBox_2)
        self.toolbar_multiselect.setObjectName("toolbar_multiselect")
        self.vboxlayout1.addWidget(self.toolbar_multiselect)
        self.use_adv_search_syntax = QtWidgets.QCheckBox(self.groupBox_2)
        self.use_adv_search_syntax.setObjectName("use_adv_search_syntax")
        self.vboxlayout1.addWidget(self.use_adv_search_syntax)
        self.quit_confirmation = QtWidgets.QCheckBox(self.groupBox_2)
        self.quit_confirmation.setObjectName("quit_confirmation")
        self.vboxlayout1.addWidget(self.quit_confirmation)
        self.starting_directory = QtWidgets.QCheckBox(self.groupBox_2)
        self.starting_directory.setObjectName("starting_directory")
        self.vboxlayout1.addWidget(self.starting_directory)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.starting_directory_path = QtWidgets.QLineEdit(self.groupBox_2)
        self.starting_directory_path.setEnabled(False)
        self.starting_directory_path.setObjectName("starting_directory_path")
        self.horizontalLayout_4.addWidget(self.starting_directory_path)
        self.starting_directory_browse = QtWidgets.QPushButton(self.groupBox_2)
        self.starting_directory_browse.setEnabled(False)
        self.starting_directory_browse.setObjectName("starting_directory_browse")
        self.horizontalLayout_4.addWidget(self.starting_directory_browse)
        self.vboxlayout1.addLayout(self.horizontalLayout_4)
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setObjectName("label")
        self.vboxlayout1.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.ui_language = QtWidgets.QComboBox(self.groupBox_2)
        self.ui_language.setObjectName("ui_language")
        self.horizontalLayout.addWidget(self.ui_language)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.vboxlayout1.addLayout(self.horizontalLayout)
        self.vboxlayout.addWidget(self.groupBox_2)
        spacerItem1 = QtWidgets.QSpacerItem(220, 61, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)

        self.retranslateUi(InterfaceOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(InterfaceOptionsPage)

    def retranslateUi(self, InterfaceOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.groupBox_2.setTitle(_("Miscellaneous"))
        self.toolbar_show_labels.setText(_("Show text labels under icons"))
        self.toolbar_multiselect.setText(_("Allow selection of multiple directories"))
        self.use_adv_search_syntax.setText(_("Use advanced query syntax"))
        self.quit_confirmation.setText(_("Show a quit confirmation dialog for unsaved changes"))
        self.starting_directory.setText(_("Begin browsing in the following directory:"))
        self.starting_directory_browse.setText(_("Browse..."))
        self.label.setText(_("User interface language:"))

