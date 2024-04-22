# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tagsfromfilenames.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QGridLayout, QHeaderView,
    QPushButton, QSizePolicy, QTreeWidget, QTreeWidgetItem,
    QWidget)

from picard.i18n import gettext as _

class Ui_TagsFromFileNamesDialog(object):
    def setupUi(self, TagsFromFileNamesDialog):
        if not TagsFromFileNamesDialog.objectName():
            TagsFromFileNamesDialog.setObjectName(u"TagsFromFileNamesDialog")
        TagsFromFileNamesDialog.resize(560, 400)
        self.gridLayout = QGridLayout(TagsFromFileNamesDialog)
#ifndef Q_OS_MAC
        self.gridLayout.setSpacing(6)
#endif
#ifndef Q_OS_MAC
        self.gridLayout.setContentsMargins(9, 9, 9, 9)
#endif
        self.gridLayout.setObjectName(u"gridLayout")
        self.files = QTreeWidget(TagsFromFileNamesDialog)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.files.setHeaderItem(__qtreewidgetitem)
        self.files.setObjectName(u"files")
        self.files.setAlternatingRowColors(True)
        self.files.setRootIsDecorated(False)

        self.gridLayout.addWidget(self.files, 1, 0, 1, 2)

        self.replace_underscores = QCheckBox(TagsFromFileNamesDialog)
        self.replace_underscores.setObjectName(u"replace_underscores")

        self.gridLayout.addWidget(self.replace_underscores, 2, 0, 1, 2)

        self.buttonbox = QDialogButtonBox(TagsFromFileNamesDialog)
        self.buttonbox.setObjectName(u"buttonbox")
        self.buttonbox.setOrientation(Qt.Horizontal)

        self.gridLayout.addWidget(self.buttonbox, 3, 0, 1, 2)

        self.preview = QPushButton(TagsFromFileNamesDialog)
        self.preview.setObjectName(u"preview")

        self.gridLayout.addWidget(self.preview, 0, 1, 1, 1)

        self.format = QComboBox(TagsFromFileNamesDialog)
        self.format.setObjectName(u"format")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.format.sizePolicy().hasHeightForWidth())
        self.format.setSizePolicy(sizePolicy)
        self.format.setEditable(True)

        self.gridLayout.addWidget(self.format, 0, 0, 1, 1)

        QWidget.setTabOrder(self.format, self.preview)
        QWidget.setTabOrder(self.preview, self.files)
        QWidget.setTabOrder(self.files, self.replace_underscores)
        QWidget.setTabOrder(self.replace_underscores, self.buttonbox)

        self.retranslateUi(TagsFromFileNamesDialog)

        QMetaObject.connectSlotsByName(TagsFromFileNamesDialog)
    # setupUi

    def retranslateUi(self, TagsFromFileNamesDialog):
        TagsFromFileNamesDialog.setWindowTitle(_(u"Convert File Names to Tags"))
        self.replace_underscores.setText(_(u"Replace underscores with spaces"))
        self.preview.setText(_(u"&Preview"))
    # retranslateUi

