# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'passworddialog.ui'
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
    QLabel, QLineEdit, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_PasswordDialog(object):
    def setupUi(self, PasswordDialog):
        if not PasswordDialog.objectName():
            PasswordDialog.setObjectName(u"PasswordDialog")
        PasswordDialog.setWindowModality(Qt.WindowModal)
        PasswordDialog.resize(378, 246)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PasswordDialog.sizePolicy().hasHeightForWidth())
        PasswordDialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(PasswordDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.info_text = QLabel(PasswordDialog)
        self.info_text.setObjectName(u"info_text")
        self.info_text.setWordWrap(True)

        self.verticalLayout.addWidget(self.info_text)

        self.verticalSpacer = QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.label = QLabel(PasswordDialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.username = QLineEdit(PasswordDialog)
        self.username.setObjectName(u"username")
        self.username.setWindowModality(Qt.NonModal)
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.username.sizePolicy().hasHeightForWidth())
        self.username.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.username)

        self.label_2 = QLabel(PasswordDialog)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout.addWidget(self.label_2)

        self.password = QLineEdit(PasswordDialog)
        self.password.setObjectName(u"password")
        self.password.setEchoMode(QLineEdit.Password)

        self.verticalLayout.addWidget(self.password)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.buttonbox = QDialogButtonBox(PasswordDialog)
        self.buttonbox.setObjectName(u"buttonbox")
        self.buttonbox.setOrientation(Qt.Horizontal)
        self.buttonbox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonbox)


        self.retranslateUi(PasswordDialog)
        self.buttonbox.rejected.connect(PasswordDialog.reject)

        QMetaObject.connectSlotsByName(PasswordDialog)
    # setupUi

    def retranslateUi(self, PasswordDialog):
        PasswordDialog.setWindowTitle(_(u"Authentication required"))
        self.info_text.setText("")
        self.label.setText(_(u"Username:"))
        self.label_2.setText(_(u"Password:"))
    # retranslateUi

