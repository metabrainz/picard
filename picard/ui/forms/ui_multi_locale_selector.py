# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'multi_locale_selector.ui'
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
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout,
    QWidget)

from picard.i18n import gettext as _

class Ui_MultiLocaleSelector(object):
    def setupUi(self, MultiLocaleSelector):
        if not MultiLocaleSelector.objectName():
            MultiLocaleSelector.setObjectName(u"MultiLocaleSelector")
        MultiLocaleSelector.setWindowModality(Qt.WindowModal)
        MultiLocaleSelector.resize(507, 284)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(MultiLocaleSelector.sizePolicy().hasHeightForWidth())
        MultiLocaleSelector.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(MultiLocaleSelector)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(MultiLocaleSelector)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.selected_locales = QListWidget(MultiLocaleSelector)
        self.selected_locales.setObjectName(u"selected_locales")

        self.verticalLayout_2.addWidget(self.selected_locales)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)

        self.move_up = QToolButton(MultiLocaleSelector)
        self.move_up.setObjectName(u"move_up")
        icon = QIcon(QIcon.fromTheme(u":/images/16x16/go-up.png"))
        self.move_up.setIcon(icon)

        self.verticalLayout_3.addWidget(self.move_up)

        self.add_locale = QToolButton(MultiLocaleSelector)
        self.add_locale.setObjectName(u"add_locale")
        icon1 = QIcon(QIcon.fromTheme(u":/images/16x16/go-previous.png"))
        self.add_locale.setIcon(icon1)

        self.verticalLayout_3.addWidget(self.add_locale)

        self.remove_locale = QToolButton(MultiLocaleSelector)
        self.remove_locale.setObjectName(u"remove_locale")
        icon2 = QIcon(QIcon.fromTheme(u":/images/16x16/go-next.png"))
        self.remove_locale.setIcon(icon2)

        self.verticalLayout_3.addWidget(self.remove_locale)

        self.move_down = QToolButton(MultiLocaleSelector)
        self.move_down.setObjectName(u"move_down")
        icon3 = QIcon(QIcon.fromTheme(u":/images/16x16/go-down.png"))
        self.move_down.setIcon(icon3)

        self.verticalLayout_3.addWidget(self.move_down)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_2 = QLabel(MultiLocaleSelector)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_4.addWidget(self.label_2)

        self.available_locales = QListWidget(MultiLocaleSelector)
        self.available_locales.setObjectName(u"available_locales")

        self.verticalLayout_4.addWidget(self.available_locales)


        self.horizontalLayout.addLayout(self.verticalLayout_4)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.button_box = QDialogButtonBox(MultiLocaleSelector)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(MultiLocaleSelector)

        QMetaObject.connectSlotsByName(MultiLocaleSelector)
    # setupUi

    def retranslateUi(self, MultiLocaleSelector):
        MultiLocaleSelector.setWindowTitle(_(u"Locale Selector"))
        self.label.setText(_(u"Selected Locales"))
#if QT_CONFIG(tooltip)
        self.move_up.setToolTip(_(u"Move selected locale up"))
#endif // QT_CONFIG(tooltip)
        self.move_up.setText("")
#if QT_CONFIG(tooltip)
        self.add_locale.setToolTip(_(u"Add to selected locales"))
#endif // QT_CONFIG(tooltip)
        self.add_locale.setText("")
#if QT_CONFIG(tooltip)
        self.remove_locale.setToolTip(_(u"Remove selected locale"))
#endif // QT_CONFIG(tooltip)
        self.remove_locale.setText("")
#if QT_CONFIG(tooltip)
        self.move_down.setToolTip(_(u"Move selected locale down"))
#endif // QT_CONFIG(tooltip)
        self.move_down.setText("")
        self.label_2.setText(_(u"Available Locales"))
    # retranslateUi

