# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_NetworkOptionsPage(object):
    def setupUi(self, NetworkOptionsPage):
        NetworkOptionsPage.setObjectName("NetworkOptionsPage")
        NetworkOptionsPage.resize(316, 371)
        self.vboxlayout = QtWidgets.QVBoxLayout(NetworkOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.web_proxy = QtWidgets.QGroupBox(NetworkOptionsPage)
        self.web_proxy.setCheckable(True)
        self.web_proxy.setObjectName("web_proxy")
        self.gridlayout = QtWidgets.QGridLayout(self.web_proxy)
        self.gridlayout.setContentsMargins(9, 9, 9, 9)
        self.gridlayout.setSpacing(2)
        self.gridlayout.setObjectName("gridlayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.proxy_type_http = QtWidgets.QRadioButton(self.web_proxy)
        self.proxy_type_http.setChecked(True)
        self.proxy_type_http.setObjectName("proxy_type_http")
        self.horizontalLayout_2.addWidget(self.proxy_type_http)
        self.proxy_type_socks = QtWidgets.QRadioButton(self.web_proxy)
        self.proxy_type_socks.setObjectName("proxy_type_socks")
        self.horizontalLayout_2.addWidget(self.proxy_type_socks)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.gridlayout.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)
        self.server_host = QtWidgets.QLineEdit(self.web_proxy)
        self.server_host.setObjectName("server_host")
        self.gridlayout.addWidget(self.server_host, 5, 0, 1, 1)
        self.username = QtWidgets.QLineEdit(self.web_proxy)
        self.username.setObjectName("username")
        self.gridlayout.addWidget(self.username, 7, 0, 1, 2)
        self.password = QtWidgets.QLineEdit(self.web_proxy)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setObjectName("password")
        self.gridlayout.addWidget(self.password, 9, 0, 1, 2)
        self.server_port = QtWidgets.QSpinBox(self.web_proxy)
        self.server_port.setMinimum(1)
        self.server_port.setMaximum(65535)
        self.server_port.setProperty("value", 80)
        self.server_port.setObjectName("server_port")
        self.gridlayout.addWidget(self.server_port, 5, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.web_proxy)
        self.label_6.setObjectName("label_6")
        self.gridlayout.addWidget(self.label_6, 6, 0, 1, 2)
        self.label_7 = QtWidgets.QLabel(self.web_proxy)
        self.label_7.setObjectName("label_7")
        self.gridlayout.addWidget(self.label_7, 4, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.web_proxy)
        self.label_5.setObjectName("label_5")
        self.gridlayout.addWidget(self.label_5, 8, 0, 1, 2)
        self.label = QtWidgets.QLabel(self.web_proxy)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label, 4, 0, 1, 1)
        self.vboxlayout.addWidget(self.web_proxy)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(NetworkOptionsPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.transfer_timeout = QtWidgets.QSpinBox(NetworkOptionsPage)
        self.transfer_timeout.setMaximum(900)
        self.transfer_timeout.setProperty("value", 30)
        self.transfer_timeout.setObjectName("transfer_timeout")
        self.horizontalLayout_3.addWidget(self.transfer_timeout)
        self.vboxlayout.addLayout(self.horizontalLayout_3)
        self.browser_integration = QtWidgets.QGroupBox(NetworkOptionsPage)
        self.browser_integration.setCheckable(True)
        self.browser_integration.setChecked(True)
        self.browser_integration.setObjectName("browser_integration")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.browser_integration)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.widget = QtWidgets.QWidget(self.browser_integration)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(6, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.browser_integration_port = QtWidgets.QSpinBox(self.widget)
        self.browser_integration_port.setMinimum(1)
        self.browser_integration_port.setMaximum(65535)
        self.browser_integration_port.setProperty("value", 8000)
        self.browser_integration_port.setObjectName("browser_integration_port")
        self.horizontalLayout.addWidget(self.browser_integration_port)
        self.verticalLayout_2.addWidget(self.widget)
        self.browser_integration_localhost_only = QtWidgets.QCheckBox(self.browser_integration)
        self.browser_integration_localhost_only.setChecked(False)
        self.browser_integration_localhost_only.setObjectName("browser_integration_localhost_only")
        self.verticalLayout_2.addWidget(self.browser_integration_localhost_only)
        self.vboxlayout.addWidget(self.browser_integration)
        spacerItem1 = QtWidgets.QSpacerItem(101, 31, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)
        self.label_6.setBuddy(self.username)
        self.label_5.setBuddy(self.password)
        self.label.setBuddy(self.server_host)

        self.retranslateUi(NetworkOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(NetworkOptionsPage)
        NetworkOptionsPage.setTabOrder(self.web_proxy, self.server_host)
        NetworkOptionsPage.setTabOrder(self.server_host, self.server_port)
        NetworkOptionsPage.setTabOrder(self.server_port, self.username)
        NetworkOptionsPage.setTabOrder(self.username, self.password)
        NetworkOptionsPage.setTabOrder(self.password, self.browser_integration)
        NetworkOptionsPage.setTabOrder(self.browser_integration, self.browser_integration_port)
        NetworkOptionsPage.setTabOrder(self.browser_integration_port, self.browser_integration_localhost_only)

    def retranslateUi(self, NetworkOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.web_proxy.setTitle(_("Web Proxy"))
        self.proxy_type_http.setText(_("HTTP"))
        self.proxy_type_socks.setText(_("SOCKS"))
        self.label_6.setText(_("Username:"))
        self.label_7.setText(_("Port:"))
        self.label_5.setText(_("Password:"))
        self.label.setText(_("Server address:"))
        self.label_3.setText(_("Request timeout in seconds:"))
        self.browser_integration.setTitle(_("Browser Integration"))
        self.label_2.setText(_("Default listening port:"))
        self.browser_integration_localhost_only.setText(_("Listen only on localhost"))
