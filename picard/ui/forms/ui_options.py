# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options.ui'
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
    QHeaderView, QSizePolicy, QSplitter, QStackedWidget,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_OptionsDialog(object):
    def setupUi(self, OptionsDialog):
        if not OptionsDialog.objectName():
            OptionsDialog.setObjectName(u"OptionsDialog")
        OptionsDialog.resize(800, 450)
        self.vboxLayout = QVBoxLayout(OptionsDialog)
        self.vboxLayout.setSpacing(6)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.vboxLayout.setContentsMargins(9, 9, 9, 9)
        self.dialog_splitter = QSplitter(OptionsDialog)
        self.dialog_splitter.setObjectName(u"dialog_splitter")
        self.dialog_splitter.setOrientation(Qt.Horizontal)
        self.dialog_splitter.setChildrenCollapsible(False)
        self.pages_tree = QTreeWidget(self.dialog_splitter)
        self.pages_tree.headerItem().setText(0, "")
        self.pages_tree.setObjectName(u"pages_tree")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pages_tree.sizePolicy().hasHeightForWidth())
        self.pages_tree.setSizePolicy(sizePolicy)
        self.pages_tree.setMinimumSize(QSize(140, 0))
        self.dialog_splitter.addWidget(self.pages_tree)
        self.pages_stack = QStackedWidget(self.dialog_splitter)
        self.pages_stack.setObjectName(u"pages_stack")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pages_stack.sizePolicy().hasHeightForWidth())
        self.pages_stack.setSizePolicy(sizePolicy1)
        self.pages_stack.setMinimumSize(QSize(280, 0))
        self.dialog_splitter.addWidget(self.pages_stack)

        self.vboxLayout.addWidget(self.dialog_splitter)

        self.buttonbox = QDialogButtonBox(OptionsDialog)
        self.buttonbox.setObjectName(u"buttonbox")
        self.buttonbox.setMinimumSize(QSize(0, 0))
        self.buttonbox.setOrientation(Qt.Horizontal)

        self.vboxLayout.addWidget(self.buttonbox)


        self.retranslateUi(OptionsDialog)

        QMetaObject.connectSlotsByName(OptionsDialog)
    # setupUi

    def retranslateUi(self, OptionsDialog):
        OptionsDialog.setWindowTitle(_(u"Options"))
    # retranslateUi

