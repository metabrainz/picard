# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options_proxy.ui'
#
# Created: Sat Mar  3 19:09:31 2007
#      by: PyQt4 UI code generator 4.1
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_ProxyOptionsPage(object):
    def setupUi(self, ProxyOptionsPage):
        ProxyOptionsPage.setObjectName("ProxyOptionsPage")
        ProxyOptionsPage.resize(QtCore.QSize(QtCore.QRect(0,0,233,252).size()).expandedTo(ProxyOptionsPage.minimumSizeHint()))

        self.vboxlayout = QtGui.QVBoxLayout(ProxyOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")

        self.web_proxy = QtGui.QGroupBox(ProxyOptionsPage)
        self.web_proxy.setCheckable(True)
        self.web_proxy.setObjectName("web_proxy")

        self.gridlayout = QtGui.QGridLayout(self.web_proxy)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")

        self.password = QtGui.QLineEdit(self.web_proxy)
        self.password.setEchoMode(QtGui.QLineEdit.Password)
        self.password.setObjectName("password")
        self.gridlayout.addWidget(self.password,5,0,1,2)

        self.username = QtGui.QLineEdit(self.web_proxy)
        self.username.setObjectName("username")
        self.gridlayout.addWidget(self.username,3,0,1,2)

        self.label_5 = QtGui.QLabel(self.web_proxy)
        self.label_5.setObjectName("label_5")
        self.gridlayout.addWidget(self.label_5,4,0,1,2)

        self.label_6 = QtGui.QLabel(self.web_proxy)
        self.label_6.setObjectName("label_6")
        self.gridlayout.addWidget(self.label_6,2,0,1,2)

        self.server_host = QtGui.QLineEdit(self.web_proxy)
        self.server_host.setObjectName("server_host")
        self.gridlayout.addWidget(self.server_host,1,0,1,1)

        self.label_7 = QtGui.QLabel(self.web_proxy)
        self.label_7.setObjectName("label_7")
        self.gridlayout.addWidget(self.label_7,0,1,1,1)

        self.server_port = QtGui.QSpinBox(self.web_proxy)
        self.server_port.setMaximum(65535)
        self.server_port.setMinimum(1)
        self.server_port.setProperty("value",QtCore.QVariant(80))
        self.server_port.setObjectName("server_port")
        self.gridlayout.addWidget(self.server_port,1,1,1,1)

        self.label = QtGui.QLabel(self.web_proxy)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label,0,0,1,1)
        self.vboxlayout.addWidget(self.web_proxy)

        spacerItem = QtGui.QSpacerItem(101,31,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_5.setBuddy(self.password)
        self.label_6.setBuddy(self.username)
        self.label.setBuddy(self.server_host)

        self.retranslateUi(ProxyOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ProxyOptionsPage)
        ProxyOptionsPage.setTabOrder(self.server_host,self.server_port)
        ProxyOptionsPage.setTabOrder(self.server_port,self.username)
        ProxyOptionsPage.setTabOrder(self.username,self.password)

    def retranslateUi(self, ProxyOptionsPage):
        self.web_proxy.setTitle(_(u"Web Proxy"))
        self.label_5.setText(_(u"Password:"))
        self.label_6.setText(_(u"Username:"))
        self.label_7.setText(_(u"Port:"))
        self.label.setText(_(u"Server address:"))

