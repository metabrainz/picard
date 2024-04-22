# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'infostatus.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QWidget)

from picard.i18n import gettext as _

class Ui_InfoStatus(object):
    def setupUi(self, InfoStatus):
        if not InfoStatus.objectName():
            InfoStatus.setObjectName(u"InfoStatus")
        InfoStatus.resize(683, 145)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(InfoStatus.sizePolicy().hasHeightForWidth())
        InfoStatus.setSizePolicy(sizePolicy)
        InfoStatus.setMinimumSize(QSize(0, 0))
        self.horizontalLayout = QHBoxLayout(InfoStatus)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.val1 = QLabel(InfoStatus)
        self.val1.setObjectName(u"val1")
        self.val1.setMinimumSize(QSize(40, 0))
        self.val1.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.val1)

        self.label1 = QLabel(InfoStatus)
        self.label1.setObjectName(u"label1")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label1.sizePolicy().hasHeightForWidth())
        self.label1.setSizePolicy(sizePolicy1)
        self.label1.setMinimumSize(QSize(0, 0))
        self.label1.setFrameShape(QFrame.NoFrame)
        self.label1.setTextFormat(Qt.AutoText)
        self.label1.setScaledContents(False)
        self.label1.setMargin(1)

        self.horizontalLayout.addWidget(self.label1)

        self.val2 = QLabel(InfoStatus)
        self.val2.setObjectName(u"val2")
        self.val2.setMinimumSize(QSize(40, 0))
        self.val2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.val2)

        self.label2 = QLabel(InfoStatus)
        self.label2.setObjectName(u"label2")
        sizePolicy1.setHeightForWidth(self.label2.sizePolicy().hasHeightForWidth())
        self.label2.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.label2)

        self.val3 = QLabel(InfoStatus)
        self.val3.setObjectName(u"val3")
        self.val3.setMinimumSize(QSize(40, 0))
        self.val3.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.val3)

        self.label3 = QLabel(InfoStatus)
        self.label3.setObjectName(u"label3")
        sizePolicy1.setHeightForWidth(self.label3.sizePolicy().hasHeightForWidth())
        self.label3.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.label3)

        self.val4 = QLabel(InfoStatus)
        self.val4.setObjectName(u"val4")
        self.val4.setMinimumSize(QSize(40, 0))
        self.val4.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.val4)

        self.label4 = QLabel(InfoStatus)
        self.label4.setObjectName(u"label4")
        sizePolicy1.setHeightForWidth(self.label4.sizePolicy().hasHeightForWidth())
        self.label4.setSizePolicy(sizePolicy1)
        self.label4.setScaledContents(False)

        self.horizontalLayout.addWidget(self.label4)

        self.val5 = QLabel(InfoStatus)
        self.val5.setObjectName(u"val5")
        self.val5.setMinimumSize(QSize(40, 0))
        self.val5.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.val5)

        self.label5 = QLabel(InfoStatus)
        self.label5.setObjectName(u"label5")
        self.label5.setMinimumSize(QSize(0, 0))
        self.label5.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label5.setMargin(0)

        self.horizontalLayout.addWidget(self.label5)


        self.retranslateUi(InfoStatus)

        QMetaObject.connectSlotsByName(InfoStatus)
    # setupUi

    def retranslateUi(self, InfoStatus):
        InfoStatus.setWindowTitle(_(u"Form"))
        self.val1.setText("")
        self.val2.setText("")
        self.label2.setText("")
        self.val3.setText("")
        self.label3.setText("")
        self.val4.setText("")
        self.label4.setText("")
        self.val5.setText("")
        self.label5.setText("")
    # retranslateUi

