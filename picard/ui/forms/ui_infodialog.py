# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'infodialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QLabel, QScrollArea, QSizePolicy, QTabWidget,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_InfoDialog(object):
    def setupUi(self, InfoDialog):
        if not InfoDialog.objectName():
            InfoDialog.setObjectName(u"InfoDialog")
        InfoDialog.resize(665, 436)
        self.verticalLayout = QVBoxLayout(InfoDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(InfoDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.info_tab = QWidget()
        self.info_tab.setObjectName(u"info_tab")
        self.vboxLayout = QVBoxLayout(self.info_tab)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.info_scroll = QScrollArea(self.info_tab)
        self.info_scroll.setObjectName(u"info_scroll")
        self.info_scroll.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setEnabled(True)
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 623, 361))
        self.verticalLayoutLabel = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayoutLabel.setObjectName(u"verticalLayoutLabel")
        self.info = QLabel(self.scrollAreaWidgetContents)
        self.info.setObjectName(u"info")
        self.info.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.info.setWordWrap(True)
        self.info.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.verticalLayoutLabel.addWidget(self.info)

        self.info_scroll.setWidget(self.scrollAreaWidgetContents)

        self.vboxLayout.addWidget(self.info_scroll)

        self.tabWidget.addTab(self.info_tab, "")
        self.error_tab = QWidget()
        self.error_tab.setObjectName(u"error_tab")
        self.vboxLayout1 = QVBoxLayout(self.error_tab)
        self.vboxLayout1.setObjectName(u"vboxLayout1")
        self.scrollArea = QScrollArea(self.error_tab)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_3 = QWidget()
        self.scrollAreaWidgetContents_3.setObjectName(u"scrollAreaWidgetContents_3")
        self.scrollAreaWidgetContents_3.setGeometry(QRect(0, 0, 623, 361))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents_3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.error = QLabel(self.scrollAreaWidgetContents_3)
        self.error.setObjectName(u"error")
        self.error.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.error.setWordWrap(True)
        self.error.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.verticalLayout_2.addWidget(self.error)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents_3)

        self.vboxLayout1.addWidget(self.scrollArea)

        self.tabWidget.addTab(self.error_tab, "")
        self.artwork_tab = QWidget()
        self.artwork_tab.setObjectName(u"artwork_tab")
        self.vboxLayout2 = QVBoxLayout(self.artwork_tab)
        self.vboxLayout2.setObjectName(u"vboxLayout2")
        self.tabWidget.addTab(self.artwork_tab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.buttonBox = QDialogButtonBox(InfoDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.NoButton)

        self.verticalLayout.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.tabWidget, self.buttonBox)

        self.retranslateUi(InfoDialog)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(InfoDialog)
    # setupUi

    def retranslateUi(self, InfoDialog):
        self.info.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.info_tab), _(u"&Info"))
        self.error.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.error_tab), _(u"&Error"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.artwork_tab), _(u"A&rtwork"))
        pass
    # retranslateUi

