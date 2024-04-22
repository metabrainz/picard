# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'win_compat_dialog.ui'
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
    QGridLayout, QLabel, QLayout, QLineEdit,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_WinCompatDialog(object):
    def setupUi(self, WinCompatDialog):
        if not WinCompatDialog.objectName():
            WinCompatDialog.setObjectName(u"WinCompatDialog")
        WinCompatDialog.setWindowModality(Qt.WindowModal)
        WinCompatDialog.resize(285, 295)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(WinCompatDialog.sizePolicy().hasHeightForWidth())
        WinCompatDialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(WinCompatDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_header_character = QLabel(WinCompatDialog)
        self.label_header_character.setObjectName(u"label_header_character")
        font = QFont()
        font.setBold(True)
        self.label_header_character.setFont(font)

        self.gridLayout.addWidget(self.label_header_character, 0, 0, 1, 1)

        self.label_header_replace = QLabel(WinCompatDialog)
        self.label_header_replace.setObjectName(u"label_header_replace")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_header_replace.sizePolicy().hasHeightForWidth())
        self.label_header_replace.setSizePolicy(sizePolicy1)
        self.label_header_replace.setFont(font)

        self.gridLayout.addWidget(self.label_header_replace, 0, 2, 1, 1)

        self.label_lt = QLabel(WinCompatDialog)
        self.label_lt.setObjectName(u"label_lt")
        font1 = QFont()
        font1.setFamilies([u"Monospace"])
        self.label_lt.setFont(font1)
        self.label_lt.setText(u"<")

        self.gridLayout.addWidget(self.label_lt, 3, 0, 1, 1)

        self.label_colon = QLabel(WinCompatDialog)
        self.label_colon.setObjectName(u"label_colon")
        self.label_colon.setFont(font1)
        self.label_colon.setText(u":")

        self.gridLayout.addWidget(self.label_colon, 2, 0, 1, 1)

        self.label_gt = QLabel(WinCompatDialog)
        self.label_gt.setObjectName(u"label_gt")
        self.label_gt.setFont(font1)
        self.label_gt.setText(u">")

        self.gridLayout.addWidget(self.label_gt, 4, 0, 1, 1)

        self.replace_questionmark = QLineEdit(WinCompatDialog)
        self.replace_questionmark.setObjectName(u"replace_questionmark")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.replace_questionmark.sizePolicy().hasHeightForWidth())
        self.replace_questionmark.setSizePolicy(sizePolicy2)
        self.replace_questionmark.setMaximumSize(QSize(20, 16777215))
        self.replace_questionmark.setText(u"_")
        self.replace_questionmark.setMaxLength(1)

        self.gridLayout.addWidget(self.replace_questionmark, 5, 2, 1, 1)

        self.label_questionmark = QLabel(WinCompatDialog)
        self.label_questionmark.setObjectName(u"label_questionmark")
        self.label_questionmark.setFont(font1)
        self.label_questionmark.setText(u"?")

        self.gridLayout.addWidget(self.label_questionmark, 5, 0, 1, 1)

        self.label_pipe = QLabel(WinCompatDialog)
        self.label_pipe.setObjectName(u"label_pipe")
        self.label_pipe.setFont(font1)
        self.label_pipe.setText(u"|")

        self.gridLayout.addWidget(self.label_pipe, 6, 0, 1, 1)

        self.replace_asterisk = QLineEdit(WinCompatDialog)
        self.replace_asterisk.setObjectName(u"replace_asterisk")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.replace_asterisk.sizePolicy().hasHeightForWidth())
        self.replace_asterisk.setSizePolicy(sizePolicy3)
        self.replace_asterisk.setMaximumSize(QSize(20, 16777215))
        self.replace_asterisk.setText(u"_")
        self.replace_asterisk.setMaxLength(1)

        self.gridLayout.addWidget(self.replace_asterisk, 1, 2, 1, 1)

        self.replace_gt = QLineEdit(WinCompatDialog)
        self.replace_gt.setObjectName(u"replace_gt")
        sizePolicy2.setHeightForWidth(self.replace_gt.sizePolicy().hasHeightForWidth())
        self.replace_gt.setSizePolicy(sizePolicy2)
        self.replace_gt.setMaximumSize(QSize(20, 16777215))
        self.replace_gt.setText(u"_")
        self.replace_gt.setMaxLength(1)

        self.gridLayout.addWidget(self.replace_gt, 4, 2, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 3, 1, 1)

        self.replace_lt = QLineEdit(WinCompatDialog)
        self.replace_lt.setObjectName(u"replace_lt")
        sizePolicy2.setHeightForWidth(self.replace_lt.sizePolicy().hasHeightForWidth())
        self.replace_lt.setSizePolicy(sizePolicy2)
        self.replace_lt.setMaximumSize(QSize(20, 16777215))
        self.replace_lt.setText(u"_")
        self.replace_lt.setMaxLength(1)

        self.gridLayout.addWidget(self.replace_lt, 3, 2, 1, 1)

        self.label_asterisk = QLabel(WinCompatDialog)
        self.label_asterisk.setObjectName(u"label_asterisk")
        self.label_asterisk.setFont(font1)
        self.label_asterisk.setText(u"*")

        self.gridLayout.addWidget(self.label_asterisk, 1, 0, 1, 1)

        self.replace_pipe = QLineEdit(WinCompatDialog)
        self.replace_pipe.setObjectName(u"replace_pipe")
        sizePolicy2.setHeightForWidth(self.replace_pipe.sizePolicy().hasHeightForWidth())
        self.replace_pipe.setSizePolicy(sizePolicy2)
        self.replace_pipe.setMaximumSize(QSize(20, 16777215))
        self.replace_pipe.setText(u"_")
        self.replace_pipe.setMaxLength(1)

        self.gridLayout.addWidget(self.replace_pipe, 6, 2, 1, 1)

        self.replace_colon = QLineEdit(WinCompatDialog)
        self.replace_colon.setObjectName(u"replace_colon")
        sizePolicy2.setHeightForWidth(self.replace_colon.sizePolicy().hasHeightForWidth())
        self.replace_colon.setSizePolicy(sizePolicy2)
        self.replace_colon.setMaximumSize(QSize(20, 16777215))
        self.replace_colon.setText(u"_")
        self.replace_colon.setMaxLength(1)

        self.gridLayout.addWidget(self.replace_colon, 2, 2, 1, 1)

        self.label_quotationmark = QLabel(WinCompatDialog)
        self.label_quotationmark.setObjectName(u"label_quotationmark")
        self.label_quotationmark.setFont(font1)
        self.label_quotationmark.setText(u"\"")

        self.gridLayout.addWidget(self.label_quotationmark, 7, 0, 1, 1)

        self.replace_quotationmark = QLineEdit(WinCompatDialog)
        self.replace_quotationmark.setObjectName(u"replace_quotationmark")
        sizePolicy2.setHeightForWidth(self.replace_quotationmark.sizePolicy().hasHeightForWidth())
        self.replace_quotationmark.setSizePolicy(sizePolicy2)
        self.replace_quotationmark.setMaximumSize(QSize(20, 16777215))
        self.replace_quotationmark.setText(u"_")

        self.gridLayout.addWidget(self.replace_quotationmark, 7, 2, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonbox = QDialogButtonBox(WinCompatDialog)
        self.buttonbox.setObjectName(u"buttonbox")
        self.buttonbox.setOrientation(Qt.Horizontal)
        self.buttonbox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonbox)

        QWidget.setTabOrder(self.replace_asterisk, self.replace_colon)
        QWidget.setTabOrder(self.replace_colon, self.replace_lt)
        QWidget.setTabOrder(self.replace_lt, self.replace_gt)
        QWidget.setTabOrder(self.replace_gt, self.replace_questionmark)
        QWidget.setTabOrder(self.replace_questionmark, self.replace_pipe)
        QWidget.setTabOrder(self.replace_pipe, self.replace_quotationmark)

        self.retranslateUi(WinCompatDialog)

        QMetaObject.connectSlotsByName(WinCompatDialog)
    # setupUi

    def retranslateUi(self, WinCompatDialog):
        WinCompatDialog.setWindowTitle(_(u"Windows compatibility"))
        self.label_header_character.setText(_(u"Character"))
        self.label_header_replace.setText(_(u"Replacement"))
    # retranslateUi

