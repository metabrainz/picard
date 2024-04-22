# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_network.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## Use `python setup.py build_ui` to update it.
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QRadioButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

from picard.i18n import gettext as _

class Ui_NetworkOptionsPage(object):
    def setupUi(self, NetworkOptionsPage):
        if not NetworkOptionsPage.objectName():
            NetworkOptionsPage.setObjectName(u"NetworkOptionsPage")
        NetworkOptionsPage.resize(316, 491)
        self.vboxLayout = QVBoxLayout(NetworkOptionsPage)
        self.vboxLayout.setSpacing(6)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(9, 9, 9, 9)
        self.web_proxy = QGroupBox(NetworkOptionsPage)
        self.web_proxy.setObjectName(u"web_proxy")
        self.web_proxy.setCheckable(True)
        self.gridLayout = QGridLayout(self.web_proxy)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.proxy_type_http = QRadioButton(self.web_proxy)
        self.proxy_type_http.setObjectName(u"proxy_type_http")
        self.proxy_type_http.setChecked(True)

        self.horizontalLayout_2.addWidget(self.proxy_type_http)

        self.proxy_type_socks = QRadioButton(self.web_proxy)
        self.proxy_type_socks.setObjectName(u"proxy_type_socks")

        self.horizontalLayout_2.addWidget(self.proxy_type_socks)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)

        self.server_host = QLineEdit(self.web_proxy)
        self.server_host.setObjectName(u"server_host")

        self.gridLayout.addWidget(self.server_host, 5, 0, 1, 1)

        self.username = QLineEdit(self.web_proxy)
        self.username.setObjectName(u"username")

        self.gridLayout.addWidget(self.username, 7, 0, 1, 2)

        self.password = QLineEdit(self.web_proxy)
        self.password.setObjectName(u"password")
        self.password.setEchoMode(QLineEdit.Password)

        self.gridLayout.addWidget(self.password, 9, 0, 1, 2)

        self.server_port = QSpinBox(self.web_proxy)
        self.server_port.setObjectName(u"server_port")
        self.server_port.setMinimum(1)
        self.server_port.setMaximum(65535)
        self.server_port.setValue(80)

        self.gridLayout.addWidget(self.server_port, 5, 1, 1, 1)

        self.label_6 = QLabel(self.web_proxy)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 6, 0, 1, 2)

        self.label_7 = QLabel(self.web_proxy)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 4, 1, 1, 1)

        self.label_5 = QLabel(self.web_proxy)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 8, 0, 1, 2)

        self.label = QLabel(self.web_proxy)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 4, 0, 1, 1)


        self.vboxLayout.addWidget(self.web_proxy)

        self.networkopts = QGroupBox(NetworkOptionsPage)
        self.networkopts.setObjectName(u"networkopts")
        self.verticalLayout_5 = QVBoxLayout(self.networkopts)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(self.networkopts)
        self.label_3.setObjectName(u"label_3")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)

        self.horizontalLayout_3.addWidget(self.label_3)

        self.transfer_timeout = QSpinBox(self.networkopts)
        self.transfer_timeout.setObjectName(u"transfer_timeout")
        self.transfer_timeout.setMaximum(900)
        self.transfer_timeout.setValue(30)

        self.horizontalLayout_3.addWidget(self.transfer_timeout)


        self.verticalLayout_5.addLayout(self.horizontalLayout_3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_cache_size = QLabel(self.networkopts)
        self.label_cache_size.setObjectName(u"label_cache_size")
        sizePolicy.setHeightForWidth(self.label_cache_size.sizePolicy().hasHeightForWidth())
        self.label_cache_size.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.label_cache_size, 0, Qt.AlignLeft|Qt.AlignVCenter)

        self.network_cache_size = QLineEdit(self.networkopts)
        self.network_cache_size.setObjectName(u"network_cache_size")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.network_cache_size.sizePolicy().hasHeightForWidth())
        self.network_cache_size.setSizePolicy(sizePolicy1)
        self.network_cache_size.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.network_cache_size)


        self.verticalLayout_5.addLayout(self.horizontalLayout)


        self.vboxLayout.addWidget(self.networkopts, 0, Qt.AlignVCenter)

        self.browser_integration = QGroupBox(NetworkOptionsPage)
        self.browser_integration.setObjectName(u"browser_integration")
        self.browser_integration.setCheckable(True)
        self.browser_integration.setChecked(True)
        self.verticalLayout_2 = QVBoxLayout(self.browser_integration)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_2 = QLabel(self.browser_integration)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)

        self.horizontalLayout_4.addWidget(self.label_2)

        self.browser_integration_port = QSpinBox(self.browser_integration)
        self.browser_integration_port.setObjectName(u"browser_integration_port")
        self.browser_integration_port.setMinimum(1)
        self.browser_integration_port.setMaximum(65535)
        self.browser_integration_port.setValue(8000)

        self.horizontalLayout_4.addWidget(self.browser_integration_port)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.browser_integration_localhost_only = QCheckBox(self.browser_integration)
        self.browser_integration_localhost_only.setObjectName(u"browser_integration_localhost_only")
        self.browser_integration_localhost_only.setChecked(False)

        self.verticalLayout_2.addWidget(self.browser_integration_localhost_only)


        self.vboxLayout.addWidget(self.browser_integration)

        self.spacerItem = QSpacerItem(101, 31, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vboxLayout.addItem(self.spacerItem)

#if QT_CONFIG(shortcut)
        self.label_6.setBuddy(self.username)
        self.label_5.setBuddy(self.password)
        self.label.setBuddy(self.server_host)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.web_proxy, self.proxy_type_http)
        QWidget.setTabOrder(self.proxy_type_http, self.proxy_type_socks)
        QWidget.setTabOrder(self.proxy_type_socks, self.server_host)
        QWidget.setTabOrder(self.server_host, self.server_port)
        QWidget.setTabOrder(self.server_port, self.username)
        QWidget.setTabOrder(self.username, self.password)
        QWidget.setTabOrder(self.password, self.network_cache_size)
        QWidget.setTabOrder(self.network_cache_size, self.browser_integration)
        QWidget.setTabOrder(self.browser_integration, self.browser_integration_port)
        QWidget.setTabOrder(self.browser_integration_port, self.browser_integration_localhost_only)

        self.retranslateUi(NetworkOptionsPage)

        QMetaObject.connectSlotsByName(NetworkOptionsPage)
    # setupUi

    def retranslateUi(self, NetworkOptionsPage):
        self.web_proxy.setTitle(_(u"Web Proxy"))
        self.proxy_type_http.setText(_(u"HTTP"))
        self.proxy_type_socks.setText(_(u"SOCKS"))
        self.label_6.setText(_(u"Username:"))
        self.label_7.setText(_(u"Port:"))
        self.label_5.setText(_(u"Password:"))
        self.label.setText(_(u"Server address:"))
        self.networkopts.setTitle(_(u"Network options"))
        self.label_3.setText(_(u"Request timeout in seconds:"))
        self.label_cache_size.setText(_(u"Cache size (MB):"))
        self.browser_integration.setTitle(_(u"Browser Integration"))
        self.label_2.setText(_(u"Default listening port:"))
        self.browser_integration_localhost_only.setText(_(u"Listen only on localhost"))
        pass
    # retranslateUi

