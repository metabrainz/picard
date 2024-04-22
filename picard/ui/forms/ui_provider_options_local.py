# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'provider_options_local.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

from picard.i18n import gettext as _

class Ui_LocalOptions(object):
    def setupUi(self, LocalOptions):
        if not LocalOptions.objectName():
            LocalOptions.setObjectName(u"LocalOptions")
        LocalOptions.resize(472, 215)
        self.verticalLayout = QVBoxLayout(LocalOptions)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.local_cover_regex_label = QLabel(LocalOptions)
        self.local_cover_regex_label.setObjectName(u"local_cover_regex_label")

        self.verticalLayout.addWidget(self.local_cover_regex_label)

        self.local_cover_regex_edit = QLineEdit(LocalOptions)
        self.local_cover_regex_edit.setObjectName(u"local_cover_regex_edit")

        self.verticalLayout.addWidget(self.local_cover_regex_edit)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.local_cover_regex_error = QLabel(LocalOptions)
        self.local_cover_regex_error.setObjectName(u"local_cover_regex_error")

        self.horizontalLayout_2.addWidget(self.local_cover_regex_error)

        self.local_cover_regex_default = QPushButton(LocalOptions)
        self.local_cover_regex_default.setObjectName(u"local_cover_regex_default")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.local_cover_regex_default.sizePolicy().hasHeightForWidth())
        self.local_cover_regex_default.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.local_cover_regex_default)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.note = QLabel(LocalOptions)
        self.note.setObjectName(u"note")
        font = QFont()
        font.setItalic(True)
        self.note.setFont(font)
        self.note.setWordWrap(True)

        self.verticalLayout.addWidget(self.note)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(LocalOptions)

        QMetaObject.connectSlotsByName(LocalOptions)
    # setupUi

    def retranslateUi(self, LocalOptions):
        LocalOptions.setWindowTitle(_(u"Form"))
        self.local_cover_regex_label.setText(_(u"Local cover art files match the following regular expression:"))
        self.local_cover_regex_error.setText("")
        self.local_cover_regex_default.setText(_(u"Default"))
        self.note.setText(_(u"First group in the regular expression, if any, will be used as type, ie. cover-back-spine.jpg will be set as types Back + Spine. If no type is found, it will default to Front type."))
    # retranslateUi

