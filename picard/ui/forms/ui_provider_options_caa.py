# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'provider_options_caa.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_CaaOptions(object):
    def setupUi(self, CaaOptions):
        if not CaaOptions.objectName():
            CaaOptions.setObjectName(u"CaaOptions")
        CaaOptions.resize(660, 194)
        self.verticalLayout = QVBoxLayout(CaaOptions)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.select_caa_types_group = QHBoxLayout()
        self.select_caa_types_group.setObjectName(u"select_caa_types_group")
        self.restrict_images_types = QCheckBox(CaaOptions)
        self.restrict_images_types.setObjectName(u"restrict_images_types")

        self.select_caa_types_group.addWidget(self.restrict_images_types)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.select_caa_types_group.addItem(self.horizontalSpacer_2)

        self.select_caa_types = QPushButton(CaaOptions)
        self.select_caa_types.setObjectName(u"select_caa_types")
        self.select_caa_types.setEnabled(False)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.select_caa_types.sizePolicy().hasHeightForWidth())
        self.select_caa_types.setSizePolicy(sizePolicy)

        self.select_caa_types_group.addWidget(self.select_caa_types)


        self.verticalLayout.addLayout(self.select_caa_types_group)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(CaaOptions)
        self.label.setObjectName(u"label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.cb_image_size = QComboBox(CaaOptions)
        self.cb_image_size.setObjectName(u"cb_image_size")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.cb_image_size.sizePolicy().hasHeightForWidth())
        self.cb_image_size.setSizePolicy(sizePolicy2)

        self.horizontalLayout.addWidget(self.cb_image_size)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.cb_approved_only = QCheckBox(CaaOptions)
        self.cb_approved_only.setObjectName(u"cb_approved_only")

        self.verticalLayout.addWidget(self.cb_approved_only)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        QWidget.setTabOrder(self.restrict_images_types, self.select_caa_types)
        QWidget.setTabOrder(self.select_caa_types, self.cb_image_size)
        QWidget.setTabOrder(self.cb_image_size, self.cb_approved_only)

        self.retranslateUi(CaaOptions)

        QMetaObject.connectSlotsByName(CaaOptions)
    # setupUi

    def retranslateUi(self, CaaOptions):
        CaaOptions.setWindowTitle(_(u"Form"))
        self.restrict_images_types.setText(_(u"Download only cover art images matching selected types"))
        self.select_caa_types.setText(_(u"Select types\u2026"))
        self.label.setText(_(u"Only use images of at most the following size:"))
        self.cb_approved_only.setText(_(u"Download only approved images"))
    # retranslateUi

