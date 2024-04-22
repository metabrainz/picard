# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_interface_toolbar.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QListWidget,
    QListWidgetItem, QSizePolicy, QSpacerItem, QToolButton,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_InterfaceToolbarOptionsPage(object):
    def setupUi(self, InterfaceToolbarOptionsPage):
        if not InterfaceToolbarOptionsPage.objectName():
            InterfaceToolbarOptionsPage.setObjectName(u"InterfaceToolbarOptionsPage")
        InterfaceToolbarOptionsPage.resize(466, 317)
        self.vboxLayout = QVBoxLayout(InterfaceToolbarOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.customize_toolbar_box = QGroupBox(InterfaceToolbarOptionsPage)
        self.customize_toolbar_box.setObjectName(u"customize_toolbar_box")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.customize_toolbar_box.sizePolicy().hasHeightForWidth())
        self.customize_toolbar_box.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.customize_toolbar_box)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.toolbar_layout_list = QListWidget(self.customize_toolbar_box)
        self.toolbar_layout_list.setObjectName(u"toolbar_layout_list")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.toolbar_layout_list.sizePolicy().hasHeightForWidth())
        self.toolbar_layout_list.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.toolbar_layout_list)

        self.edit_button_box = QWidget(self.customize_toolbar_box)
        self.edit_button_box.setObjectName(u"edit_button_box")
        self.edit_box_layout = QHBoxLayout(self.edit_button_box)
        self.edit_box_layout.setObjectName(u"edit_box_layout")
        self.edit_box_layout.setContentsMargins(0, 0, 0, 0)
        self.add_button = QToolButton(self.edit_button_box)
        self.add_button.setObjectName(u"add_button")

        self.edit_box_layout.addWidget(self.add_button)

        self.insert_separator_button = QToolButton(self.edit_button_box)
        self.insert_separator_button.setObjectName(u"insert_separator_button")

        self.edit_box_layout.addWidget(self.insert_separator_button)

        self.button_box_spacer = QSpacerItem(50, 20, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)

        self.edit_box_layout.addItem(self.button_box_spacer)

        self.up_button = QToolButton(self.edit_button_box)
        self.up_button.setObjectName(u"up_button")
        icon = QIcon()
        iconThemeName = u":/images/16x16/go-up.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.up_button.setIcon(icon)

        self.edit_box_layout.addWidget(self.up_button)

        self.down_button = QToolButton(self.edit_button_box)
        self.down_button.setObjectName(u"down_button")
        icon1 = QIcon()
        iconThemeName = u":/images/16x16/go-down.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.down_button.setIcon(icon1)

        self.edit_box_layout.addWidget(self.down_button)

        self.remove_button = QToolButton(self.edit_button_box)
        self.remove_button.setObjectName(u"remove_button")

        self.edit_box_layout.addWidget(self.remove_button)


        self.verticalLayout.addWidget(self.edit_button_box)


        self.vboxLayout.addWidget(self.customize_toolbar_box)

        QWidget.setTabOrder(self.toolbar_layout_list, self.add_button)
        QWidget.setTabOrder(self.add_button, self.insert_separator_button)
        QWidget.setTabOrder(self.insert_separator_button, self.up_button)
        QWidget.setTabOrder(self.up_button, self.down_button)
        QWidget.setTabOrder(self.down_button, self.remove_button)

        self.retranslateUi(InterfaceToolbarOptionsPage)

        QMetaObject.connectSlotsByName(InterfaceToolbarOptionsPage)
    # setupUi

    def retranslateUi(self, InterfaceToolbarOptionsPage):
        self.customize_toolbar_box.setTitle(_(u"Customize Action Toolbar"))
#if QT_CONFIG(tooltip)
        self.add_button.setToolTip(_(u"Add a new button to Toolbar"))
#endif // QT_CONFIG(tooltip)
        self.add_button.setText(_(u"Add Action"))
#if QT_CONFIG(tooltip)
        self.insert_separator_button.setToolTip(_(u"Insert a separator"))
#endif // QT_CONFIG(tooltip)
        self.insert_separator_button.setText(_(u"Add Separator"))
#if QT_CONFIG(tooltip)
        self.up_button.setToolTip(_(u"Move selected item up"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.down_button.setToolTip(_(u"Move selected item down"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.remove_button.setToolTip(_(u"Remove button from toolbar"))
#endif // QT_CONFIG(tooltip)
        self.remove_button.setText(_(u"Remove"))
        pass
    # retranslateUi

