# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_proxy.ui'
#
# Created: Tue May 29 19:44:15 2012
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ProxyOptionsPage(object):
    def setupUi(self, ProxyOptionsPage):
        ProxyOptionsPage.setObjectName(_fromUtf8("ProxyOptionsPage"))
        ProxyOptionsPage.resize(233, 252)
        self.vboxlayout = QtGui.QVBoxLayout(ProxyOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.web_proxy = QtGui.QGroupBox(ProxyOptionsPage)
        self.web_proxy.setCheckable(True)
        self.web_proxy.setObjectName(_fromUtf8("web_proxy"))
        self.gridlayout = QtGui.QGridLayout(self.web_proxy)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.password = QtGui.QLineEdit(self.web_proxy)
        self.password.setEchoMode(QtGui.QLineEdit.Password)
        self.password.setObjectName(_fromUtf8("password"))
        self.gridlayout.addWidget(self.password, 5, 0, 1, 2)
        self.username = QtGui.QLineEdit(self.web_proxy)
        self.username.setObjectName(_fromUtf8("username"))
        self.gridlayout.addWidget(self.username, 3, 0, 1, 2)
        self.label_5 = QtGui.QLabel(self.web_proxy)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridlayout.addWidget(self.label_5, 4, 0, 1, 2)
        self.label_6 = QtGui.QLabel(self.web_proxy)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridlayout.addWidget(self.label_6, 2, 0, 1, 2)
        self.server_host = QtGui.QLineEdit(self.web_proxy)
        self.server_host.setObjectName(_fromUtf8("server_host"))
        self.gridlayout.addWidget(self.server_host, 1, 0, 1, 1)
        self.label_7 = QtGui.QLabel(self.web_proxy)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.gridlayout.addWidget(self.label_7, 0, 1, 1, 1)
        self.server_port = QtGui.QSpinBox(self.web_proxy)
        self.server_port.setMaximum(65535)
        self.server_port.setMinimum(1)
        self.server_port.setProperty(_fromUtf8("value"), 80)
        self.server_port.setObjectName(_fromUtf8("server_port"))
        self.gridlayout.addWidget(self.server_port, 1, 1, 1, 1)
        self.label = QtGui.QLabel(self.web_proxy)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridlayout.addWidget(self.label, 0, 0, 1, 1)
        self.vboxlayout.addWidget(self.web_proxy)
        spacerItem = QtGui.QSpacerItem(101, 31, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_5.setBuddy(self.password)
        self.label_6.setBuddy(self.username)
        self.label.setBuddy(self.server_host)

        self.retranslateUi(ProxyOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ProxyOptionsPage)
        ProxyOptionsPage.setTabOrder(self.server_host, self.server_port)
        ProxyOptionsPage.setTabOrder(self.server_port, self.username)
        ProxyOptionsPage.setTabOrder(self.username, self.password)

    def retranslateUi(self, ProxyOptionsPage):
        self.web_proxy.setTitle(_("Web Proxy"))
        self.label_5.setText(_("Password:"))
        self.label_6.setText(_("Username:"))
        self.label_7.setText(_("Port:"))
        self.label.setText(_("Server address:"))

