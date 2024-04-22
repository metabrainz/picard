# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_releases.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QGroupBox,
    QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_ReleasesOptionsPage(object):
    def setupUi(self, ReleasesOptionsPage):
        if not ReleasesOptionsPage.objectName():
            ReleasesOptionsPage.setObjectName(u"ReleasesOptionsPage")
        ReleasesOptionsPage.resize(551, 497)
        self.verticalLayout_3 = QVBoxLayout(ReleasesOptionsPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.type_group = QGroupBox(ReleasesOptionsPage)
        self.type_group.setObjectName(u"type_group")
        self.gridLayout = QGridLayout(self.type_group)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setVerticalSpacing(6)

        self.verticalLayout_3.addWidget(self.type_group)

        self.country_group = QGroupBox(ReleasesOptionsPage)
        self.country_group.setObjectName(u"country_group")
        self.horizontalLayout = QHBoxLayout(self.country_group)
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.country_list = QListWidget(self.country_group)
        self.country_list.setObjectName(u"country_list")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.country_list.sizePolicy().hasHeightForWidth())
        self.country_list.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.country_list)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.add_countries = QPushButton(self.country_group)
        self.add_countries.setObjectName(u"add_countries")
        icon = QIcon()
        iconThemeName = u":/images/16x16/go-next.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.add_countries.setIcon(icon)

        self.verticalLayout.addWidget(self.add_countries)

        self.remove_countries = QPushButton(self.country_group)
        self.remove_countries.setObjectName(u"remove_countries")
        icon1 = QIcon()
        iconThemeName = u":/images/16x16/go-previous.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.remove_countries.setIcon(icon1)

        self.verticalLayout.addWidget(self.remove_countries)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.preferred_country_list = QListWidget(self.country_group)
        self.preferred_country_list.setObjectName(u"preferred_country_list")
        sizePolicy.setHeightForWidth(self.preferred_country_list.sizePolicy().hasHeightForWidth())
        self.preferred_country_list.setSizePolicy(sizePolicy)
        self.preferred_country_list.setDragEnabled(True)
        self.preferred_country_list.setDragDropMode(QAbstractItemView.InternalMove)

        self.horizontalLayout.addWidget(self.preferred_country_list)


        self.verticalLayout_3.addWidget(self.country_group)

        self.format_group = QGroupBox(ReleasesOptionsPage)
        self.format_group.setObjectName(u"format_group")
        self.horizontalLayout_2 = QHBoxLayout(self.format_group)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.format_list = QListWidget(self.format_group)
        self.format_list.setObjectName(u"format_list")
        sizePolicy.setHeightForWidth(self.format_list.sizePolicy().hasHeightForWidth())
        self.format_list.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.format_list)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_3)

        self.add_formats = QPushButton(self.format_group)
        self.add_formats.setObjectName(u"add_formats")
        self.add_formats.setIcon(icon)

        self.verticalLayout_2.addWidget(self.add_formats)

        self.remove_formats = QPushButton(self.format_group)
        self.remove_formats.setObjectName(u"remove_formats")
        self.remove_formats.setIcon(icon1)

        self.verticalLayout_2.addWidget(self.remove_formats)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_4)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)

        self.preferred_format_list = QListWidget(self.format_group)
        self.preferred_format_list.setObjectName(u"preferred_format_list")
        sizePolicy.setHeightForWidth(self.preferred_format_list.sizePolicy().hasHeightForWidth())
        self.preferred_format_list.setSizePolicy(sizePolicy)
        self.preferred_format_list.setDragEnabled(True)
        self.preferred_format_list.setDragDropMode(QAbstractItemView.InternalMove)

        self.horizontalLayout_2.addWidget(self.preferred_format_list)


        self.verticalLayout_3.addWidget(self.format_group)


        self.retranslateUi(ReleasesOptionsPage)

        QMetaObject.connectSlotsByName(ReleasesOptionsPage)
    # setupUi

    def retranslateUi(self, ReleasesOptionsPage):
        self.type_group.setTitle(_(u"Preferred release types"))
        self.country_group.setTitle(_(u"Preferred release countries"))
#if QT_CONFIG(tooltip)
        self.add_countries.setToolTip(_(u"Add to preferred release countries"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.add_countries.setAccessibleDescription(_(u"Add to preferred release countries"))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.remove_countries.setToolTip(_(u"Remove from preferred release countries"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.remove_countries.setAccessibleDescription(_(u"Remove from preferred release countries"))
#endif // QT_CONFIG(accessibility)
        self.format_group.setTitle(_(u"Preferred medium formats"))
#if QT_CONFIG(tooltip)
        self.add_formats.setToolTip(_(u"Add to preferred release formats"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.add_formats.setAccessibleName(_(u"Add to preferred release formats"))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.remove_formats.setToolTip(_(u"Remove from preferred release formats"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.remove_formats.setAccessibleDescription(_(u"Remove from preferred release formats"))
#endif // QT_CONFIG(accessibility)
        pass
    # retranslateUi

