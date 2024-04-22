# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_attached_profiles.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialog,
    QDialogButtonBox, QHeaderView, QSizePolicy, QTableView,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_AttachedProfilesDialog(object):
    def setupUi(self, AttachedProfilesDialog):
        if not AttachedProfilesDialog.objectName():
            AttachedProfilesDialog.setObjectName(u"AttachedProfilesDialog")
        AttachedProfilesDialog.resize(800, 450)
        self.vboxLayout = QVBoxLayout(AttachedProfilesDialog)
        self.vboxLayout.setSpacing(6)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(9, 9, 9, 9)
        self.options_list = QTableView(AttachedProfilesDialog)
        self.options_list.setObjectName(u"options_list")
        self.options_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.options_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.options_list.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.vboxLayout.addWidget(self.options_list)

        self.buttonBox = QDialogButtonBox(AttachedProfilesDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.NoButton)

        self.vboxLayout.addWidget(self.buttonBox)


        self.retranslateUi(AttachedProfilesDialog)

        QMetaObject.connectSlotsByName(AttachedProfilesDialog)
    # setupUi

    def retranslateUi(self, AttachedProfilesDialog):
        AttachedProfilesDialog.setWindowTitle(_(u"Profiles Attached to Options"))
    # retranslateUi

