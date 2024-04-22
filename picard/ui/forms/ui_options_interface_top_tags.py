# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_interface_top_tags.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QSizePolicy, QVBoxLayout,
    QWidget)

from picard.ui.widgets.taglisteditor import TagListEditor

from picard.i18n import gettext as _

class Ui_InterfaceTopTagsOptionsPage(object):
    def setupUi(self, InterfaceTopTagsOptionsPage):
        if not InterfaceTopTagsOptionsPage.objectName():
            InterfaceTopTagsOptionsPage.setObjectName(u"InterfaceTopTagsOptionsPage")
        InterfaceTopTagsOptionsPage.resize(418, 310)
        self.vboxLayout = QVBoxLayout(InterfaceTopTagsOptionsPage)
        self.vboxLayout.setSpacing(6)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(9, 9, 9, 9)
        self.top_tags_groupBox = QGroupBox(InterfaceTopTagsOptionsPage)
        self.top_tags_groupBox.setObjectName(u"top_tags_groupBox")
        self.verticalLayout = QVBoxLayout(self.top_tags_groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.top_tags_list = TagListEditor(self.top_tags_groupBox)
        self.top_tags_list.setObjectName(u"top_tags_list")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.top_tags_list.sizePolicy().hasHeightForWidth())
        self.top_tags_list.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.top_tags_list)


        self.vboxLayout.addWidget(self.top_tags_groupBox)


        self.retranslateUi(InterfaceTopTagsOptionsPage)

        QMetaObject.connectSlotsByName(InterfaceTopTagsOptionsPage)
    # setupUi

    def retranslateUi(self, InterfaceTopTagsOptionsPage):
        self.top_tags_groupBox.setTitle(_(u"Show the below tags above all other tags in the metadata view"))
        pass
    # retranslateUi

