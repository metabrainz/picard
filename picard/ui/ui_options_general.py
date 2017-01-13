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

class Ui_GeneralOptionsPage(object):
    def setupUi(self, GeneralOptionsPage):
        GeneralOptionsPage.setObjectName(_fromUtf8("GeneralOptionsPage"))
        GeneralOptionsPage.resize(283, 435)
        self.vboxlayout = QtGui.QVBoxLayout(GeneralOptionsPage)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.groupBox = QtGui.QGroupBox(GeneralOptionsPage)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridlayout = QtGui.QGridLayout(self.groupBox)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.server_host = QtGui.QComboBox(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.server_host.sizePolicy().hasHeightForWidth())
        self.server_host.setSizePolicy(sizePolicy)
        self.server_host.setEditable(True)
        self.server_host.setObjectName(_fromUtf8("server_host"))
        self.gridlayout.addWidget(self.server_host, 1, 0, 1, 1)
        self.label_7 = QtGui.QLabel(self.groupBox)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.gridlayout.addWidget(self.label_7, 0, 1, 1, 1)
        self.server_port = QtGui.QSpinBox(self.groupBox)
        self.server_port.setMinimum(1)
        self.server_port.setMaximum(65535)
        self.server_port.setProperty("value", 80)
        self.server_port.setObjectName(_fromUtf8("server_port"))
        self.gridlayout.addWidget(self.server_port, 1, 1, 1, 1)
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridlayout.addWidget(self.label, 0, 0, 1, 1)
        self.vboxlayout.addWidget(self.groupBox)
        self.rename_files_2 = QtGui.QGroupBox(GeneralOptionsPage)
        self.rename_files_2.setObjectName(_fromUtf8("rename_files_2"))
        self.gridlayout1 = QtGui.QGridLayout(self.rename_files_2)
        self.gridlayout1.setSpacing(2)
        self.gridlayout1.setObjectName(_fromUtf8("gridlayout1"))
        self.login = QtGui.QPushButton(self.rename_files_2)
        self.login.setObjectName(_fromUtf8("login"))
        self.gridlayout1.addWidget(self.login, 1, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridlayout1.addItem(spacerItem, 1, 2, 1, 1)
        self.logout = QtGui.QPushButton(self.rename_files_2)
        self.logout.setObjectName(_fromUtf8("logout"))
        self.gridlayout1.addWidget(self.logout, 1, 1, 1, 1)
        self.logged_in = QtGui.QLabel(self.rename_files_2)
        self.logged_in.setText(_fromUtf8(""))
        self.logged_in.setObjectName(_fromUtf8("logged_in"))
        self.gridlayout1.addWidget(self.logged_in, 0, 0, 1, 3)
        self.vboxlayout.addWidget(self.rename_files_2)
        self.groupBox_2 = QtGui.QGroupBox(GeneralOptionsPage)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.analyze_new_files = QtGui.QCheckBox(self.groupBox_2)
        self.analyze_new_files.setObjectName(_fromUtf8("analyze_new_files"))
        self.verticalLayout.addWidget(self.analyze_new_files)
        self.ignore_file_mbids = QtGui.QCheckBox(self.groupBox_2)
        self.ignore_file_mbids.setObjectName(_fromUtf8("ignore_file_mbids"))
        self.verticalLayout.addWidget(self.ignore_file_mbids)
        self.vboxlayout.addWidget(self.groupBox_2)
        spacerItem1 = QtGui.QSpacerItem(181, 21, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)

        self.retranslateUi(GeneralOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(GeneralOptionsPage)
        GeneralOptionsPage.setTabOrder(self.server_host, self.server_port)

    def retranslateUi(self, GeneralOptionsPage):
        self.groupBox.setTitle(_("MusicBrainz Server"))
        self.label_7.setText(_("Port:"))
        self.label.setText(_("Server address:"))
        self.rename_files_2.setTitle(_("MusicBrainz Account"))
        self.login.setText(_("Log in"))
        self.logout.setText(_("Log out"))
        self.groupBox_2.setTitle(_("General"))
        self.analyze_new_files.setText(_("Automatically scan all new files"))
        self.ignore_file_mbids.setText(_("Ignore MBIDs when loading new files"))

