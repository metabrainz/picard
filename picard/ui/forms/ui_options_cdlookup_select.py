# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_cdlookup_select.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_CDLookupOptionsPage(object):
    def setupUi(self, CDLookupOptionsPage):
        if not CDLookupOptionsPage.objectName():
            CDLookupOptionsPage.setObjectName(u"CDLookupOptionsPage")
        CDLookupOptionsPage.resize(255, 155)
        self.vboxLayout = QVBoxLayout(CDLookupOptionsPage)
#ifndef Q_OS_MAC
        self.vboxLayout.setSpacing(6)
#endif
#ifndef Q_OS_MAC
        self.vboxLayout.setContentsMargins(9, 9, 9, 9)
#endif
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.rename_files = QGroupBox(CDLookupOptionsPage)
        self.rename_files.setObjectName(u"rename_files")
        self.gridLayout = QGridLayout(self.rename_files)
        self.gridLayout.setSpacing(2)
#ifndef Q_OS_MAC
        self.gridLayout.setContentsMargins(9, 9, 9, 9)
#endif
        self.gridLayout.setObjectName(u"gridLayout")
        self.cd_lookup_ = QLabel(self.rename_files)
        self.cd_lookup_.setObjectName(u"cd_lookup_")

        self.gridLayout.addWidget(self.cd_lookup_, 0, 0, 1, 1)

        self.hboxLayout = QHBoxLayout()
#ifndef Q_OS_MAC
        self.hboxLayout.setSpacing(6)
#endif
        self.hboxLayout.setContentsMargins(0, 0, 0, 0)
        self.hboxLayout.setObjectName(u"hboxLayout")
        self.cd_lookup_device = QComboBox(self.rename_files)
        self.cd_lookup_device.setObjectName(u"cd_lookup_device")

        self.hboxLayout.addWidget(self.cd_lookup_device)

        self.spacerItem = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout.addItem(self.spacerItem)


        self.gridLayout.addLayout(self.hboxLayout, 1, 0, 1, 1)


        self.vboxLayout.addWidget(self.rename_files)

        self.spacerItem1 = QSpacerItem(161, 81, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vboxLayout.addItem(self.spacerItem1)

#if QT_CONFIG(shortcut)
        self.cd_lookup_.setBuddy(self.cd_lookup_device)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(CDLookupOptionsPage)

        QMetaObject.connectSlotsByName(CDLookupOptionsPage)
    # setupUi

    def retranslateUi(self, CDLookupOptionsPage):
        self.rename_files.setTitle(_(u"CD Lookup"))
        self.cd_lookup_.setText(_(u"Default CD-ROM drive to use for lookups:"))
        pass
    # retranslateUi

