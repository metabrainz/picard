# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_fingerprinting.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

from picard.i18n import gettext as _

class Ui_FingerprintingOptionsPage(object):
    def setupUi(self, FingerprintingOptionsPage):
        if not FingerprintingOptionsPage.objectName():
            FingerprintingOptionsPage.setObjectName(u"FingerprintingOptionsPage")
        FingerprintingOptionsPage.resize(371, 408)
        self.verticalLayout = QVBoxLayout(FingerprintingOptionsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.fingerprinting = QGroupBox(FingerprintingOptionsPage)
        self.fingerprinting.setObjectName(u"fingerprinting")
        self.fingerprinting.setCheckable(False)
        self.verticalLayout_3 = QVBoxLayout(self.fingerprinting)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.disable_fingerprinting = QRadioButton(self.fingerprinting)
        self.disable_fingerprinting.setObjectName(u"disable_fingerprinting")

        self.verticalLayout_3.addWidget(self.disable_fingerprinting)

        self.use_acoustid = QRadioButton(self.fingerprinting)
        self.use_acoustid.setObjectName(u"use_acoustid")

        self.verticalLayout_3.addWidget(self.use_acoustid)


        self.verticalLayout.addWidget(self.fingerprinting)

        self.acoustid_settings = QGroupBox(FingerprintingOptionsPage)
        self.acoustid_settings.setObjectName(u"acoustid_settings")
        self.verticalLayout_2 = QVBoxLayout(self.acoustid_settings)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.ignore_existing_acoustid_fingerprints = QCheckBox(self.acoustid_settings)
        self.ignore_existing_acoustid_fingerprints.setObjectName(u"ignore_existing_acoustid_fingerprints")

        self.verticalLayout_2.addWidget(self.ignore_existing_acoustid_fingerprints)

        self.save_acoustid_fingerprints = QCheckBox(self.acoustid_settings)
        self.save_acoustid_fingerprints.setObjectName(u"save_acoustid_fingerprints")

        self.verticalLayout_2.addWidget(self.save_acoustid_fingerprints)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(-1, 0, -1, -1)
        self.label_3 = QLabel(self.acoustid_settings)
        self.label_3.setObjectName(u"label_3")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)

        self.horizontalLayout_3.addWidget(self.label_3)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.fpcalc_threads = QSpinBox(self.acoustid_settings)
        self.fpcalc_threads.setObjectName(u"fpcalc_threads")
        self.fpcalc_threads.setMinimum(1)
        self.fpcalc_threads.setMaximum(9)

        self.horizontalLayout_3.addWidget(self.fpcalc_threads)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.label = QLabel(self.acoustid_settings)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.acoustid_fpcalc = QLineEdit(self.acoustid_settings)
        self.acoustid_fpcalc.setObjectName(u"acoustid_fpcalc")

        self.horizontalLayout_2.addWidget(self.acoustid_fpcalc)

        self.acoustid_fpcalc_browse = QPushButton(self.acoustid_settings)
        self.acoustid_fpcalc_browse.setObjectName(u"acoustid_fpcalc_browse")

        self.horizontalLayout_2.addWidget(self.acoustid_fpcalc_browse)

        self.acoustid_fpcalc_download = QPushButton(self.acoustid_settings)
        self.acoustid_fpcalc_download.setObjectName(u"acoustid_fpcalc_download")

        self.horizontalLayout_2.addWidget(self.acoustid_fpcalc_download)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.acoustid_fpcalc_info = QLabel(self.acoustid_settings)
        self.acoustid_fpcalc_info.setObjectName(u"acoustid_fpcalc_info")

        self.verticalLayout_2.addWidget(self.acoustid_fpcalc_info)

        self.label_2 = QLabel(self.acoustid_settings)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_2.addWidget(self.label_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.acoustid_apikey = QLineEdit(self.acoustid_settings)
        self.acoustid_apikey.setObjectName(u"acoustid_apikey")

        self.horizontalLayout.addWidget(self.acoustid_apikey)

        self.acoustid_apikey_get = QPushButton(self.acoustid_settings)
        self.acoustid_apikey_get.setObjectName(u"acoustid_apikey_get")

        self.horizontalLayout.addWidget(self.acoustid_apikey_get)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout.addWidget(self.acoustid_settings)

        self.spacerItem = QSpacerItem(181, 21, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.spacerItem)


        self.retranslateUi(FingerprintingOptionsPage)

        QMetaObject.connectSlotsByName(FingerprintingOptionsPage)
    # setupUi

    def retranslateUi(self, FingerprintingOptionsPage):
        self.fingerprinting.setTitle(_(u"Audio Fingerprinting"))
        self.disable_fingerprinting.setText(_(u"Do not use audio fingerprinting"))
        self.use_acoustid.setText(_(u"Use AcoustID"))
        self.acoustid_settings.setTitle(_(u"AcoustID Settings"))
        self.ignore_existing_acoustid_fingerprints.setText(_(u"Ignore existing AcoustID fingerprints"))
        self.save_acoustid_fingerprints.setText(_(u"Save AcoustID fingerprints to file tags"))
        self.label_3.setText(_(u"Maximum threads to use for calculator:"))
        self.label.setText(_(u"Fingerprint calculator:"))
        self.acoustid_fpcalc_browse.setText(_(u"Browse\u2026"))
        self.acoustid_fpcalc_download.setText(_(u"Download\u2026"))
        self.acoustid_fpcalc_info.setText("")
        self.label_2.setText(_(u"API key:"))
        self.acoustid_apikey_get.setText(_(u"Get API key\u2026"))
        pass
    # retranslateUi

