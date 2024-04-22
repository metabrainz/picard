# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_plugins.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLayout,
    QPushButton, QScrollArea, QSizePolicy, QSplitter,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_PluginsOptionsPage(object):
    def setupUi(self, PluginsOptionsPage):
        if not PluginsOptionsPage.objectName():
            PluginsOptionsPage.setObjectName(u"PluginsOptionsPage")
        PluginsOptionsPage.resize(697, 441)
        self.vboxLayout = QVBoxLayout(PluginsOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.plugins_container = QSplitter(PluginsOptionsPage)
        self.plugins_container.setObjectName(u"plugins_container")
        self.plugins_container.setEnabled(True)
        self.plugins_container.setOrientation(Qt.Vertical)
        self.plugins_container.setHandleWidth(2)
        self.groupBox_2 = QGroupBox(self.plugins_container)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.vboxLayout1 = QVBoxLayout(self.groupBox_2)
        self.vboxLayout1.setSpacing(2)
        self.vboxLayout1.setObjectName(u"vboxLayout1")
        self.plugins = QTreeWidget(self.groupBox_2)
        self.plugins.headerItem().setText(3, "")
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setTextAlignment(2, Qt.AlignCenter);
        self.plugins.setHeaderItem(__qtreewidgetitem)
        self.plugins.setObjectName(u"plugins")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plugins.sizePolicy().hasHeightForWidth())
        self.plugins.setSizePolicy(sizePolicy)
        self.plugins.setAcceptDrops(True)
        self.plugins.setDragDropMode(QAbstractItemView.DropOnly)
        self.plugins.setRootIsDecorated(False)

        self.vboxLayout1.addWidget(self.plugins)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.install_plugin = QPushButton(self.groupBox_2)
        self.install_plugin.setObjectName(u"install_plugin")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.install_plugin.sizePolicy().hasHeightForWidth())
        self.install_plugin.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.install_plugin)

        self.folder_open = QPushButton(self.groupBox_2)
        self.folder_open.setObjectName(u"folder_open")
        sizePolicy1.setHeightForWidth(self.folder_open.sizePolicy().hasHeightForWidth())
        self.folder_open.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.folder_open)

        self.reload_list_of_plugins = QPushButton(self.groupBox_2)
        self.reload_list_of_plugins.setObjectName(u"reload_list_of_plugins")
        sizePolicy1.setHeightForWidth(self.reload_list_of_plugins.sizePolicy().hasHeightForWidth())
        self.reload_list_of_plugins.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.reload_list_of_plugins)


        self.vboxLayout1.addLayout(self.horizontalLayout)

        self.plugins_container.addWidget(self.groupBox_2)
        self.groupBox = QGroupBox(self.plugins_container)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy2)
        self.vboxLayout2 = QVBoxLayout(self.groupBox)
        self.vboxLayout2.setSpacing(0)
        self.vboxLayout2.setObjectName(u"vboxLayout2")
        self.scrollArea = QScrollArea(self.groupBox)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy2)
        self.scrollArea.setFrameShape(QFrame.HLine)
        self.scrollArea.setFrameShadow(QFrame.Plain)
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 655, 82))
        sizePolicy2.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy2)
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetNoConstraint)
        self.verticalLayout.setContentsMargins(0, 0, 6, 0)
        self.details = QLabel(self.scrollAreaWidgetContents)
        self.details.setObjectName(u"details")
        sizePolicy2.setHeightForWidth(self.details.sizePolicy().hasHeightForWidth())
        self.details.setSizePolicy(sizePolicy2)
        self.details.setMinimumSize(QSize(0, 0))
        self.details.setFrameShape(QFrame.Box)
        self.details.setLineWidth(0)
        self.details.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.details.setWordWrap(True)
        self.details.setIndent(0)
        self.details.setOpenExternalLinks(True)
        self.details.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.verticalLayout.addWidget(self.details)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.vboxLayout2.addWidget(self.scrollArea)

        self.plugins_container.addWidget(self.groupBox)

        self.vboxLayout.addWidget(self.plugins_container)

        QWidget.setTabOrder(self.plugins, self.install_plugin)
        QWidget.setTabOrder(self.install_plugin, self.folder_open)
        QWidget.setTabOrder(self.folder_open, self.reload_list_of_plugins)
        QWidget.setTabOrder(self.reload_list_of_plugins, self.scrollArea)

        self.retranslateUi(PluginsOptionsPage)

        QMetaObject.connectSlotsByName(PluginsOptionsPage)
    # setupUi

    def retranslateUi(self, PluginsOptionsPage):
        self.groupBox_2.setTitle(_(u"Plugins"))
        ___qtreewidgetitem = self.plugins.headerItem()
        ___qtreewidgetitem.setText(2, _(u"Actions"));
        ___qtreewidgetitem.setText(1, _(u"Version"));
        ___qtreewidgetitem.setText(0, _(u"Name"));
        self.install_plugin.setText(_(u"Install plugin\u2026"))
        self.folder_open.setText(_(u"Open plugin folder"))
        self.reload_list_of_plugins.setText(_(u"Reload List of Plugins"))
        self.groupBox.setTitle(_(u"Details"))
        self.details.setText("")
        pass
    # retranslateUi

