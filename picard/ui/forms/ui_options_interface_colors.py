# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_interface_colors.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_InterfaceColorsOptionsPage(object):
    def setupUi(self, InterfaceColorsOptionsPage):
        if not InterfaceColorsOptionsPage.objectName():
            InterfaceColorsOptionsPage.setObjectName(u"InterfaceColorsOptionsPage")
        InterfaceColorsOptionsPage.resize(171, 137)
        self.vboxLayout = QVBoxLayout(InterfaceColorsOptionsPage)
        self.vboxLayout.setSpacing(6)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(InterfaceColorsOptionsPage)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setFrameShadow(QFrame.Plain)
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 199, 137))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        self.colors = QGroupBox(self.scrollAreaWidgetContents)
        self.colors.setObjectName(u"colors")

        self.verticalLayout.addWidget(self.colors)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.vboxLayout.addWidget(self.scrollArea)


        self.retranslateUi(InterfaceColorsOptionsPage)

        QMetaObject.connectSlotsByName(InterfaceColorsOptionsPage)
    # setupUi

    def retranslateUi(self, InterfaceColorsOptionsPage):
        self.colors.setTitle(_(u"Colors"))
        pass
    # retranslateUi

