# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'exception_script_selector.ui'
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
    QSizePolicy, QSpacerItem, QSpinBox, QToolButton,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_ExceptionScriptSelector(object):
    def setupUi(self, ExceptionScriptSelector):
        if not ExceptionScriptSelector.objectName():
            ExceptionScriptSelector.setObjectName(u"ExceptionScriptSelector")
        ExceptionScriptSelector.setWindowModality(Qt.WindowModal)
        ExceptionScriptSelector.resize(510, 250)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(ExceptionScriptSelector.sizePolicy().hasHeightForWidth())
        ExceptionScriptSelector.setSizePolicy(sizePolicy)
        ExceptionScriptSelector.setMinimumSize(QSize(510, 250))
        self.verticalLayout = QVBoxLayout(ExceptionScriptSelector)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(ExceptionScriptSelector)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.selected_scripts = QListWidget(ExceptionScriptSelector)
        self.selected_scripts.setObjectName(u"selected_scripts")
        self.selected_scripts.setMaximumSize(QSize(16777215, 16777215))

        self.verticalLayout_2.addWidget(self.selected_scripts)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.threshold_label = QLabel(ExceptionScriptSelector)
        self.threshold_label.setObjectName(u"threshold_label")

        self.horizontalLayout_2.addWidget(self.threshold_label)

        self.weighting_selector = QSpinBox(ExceptionScriptSelector)
        self.weighting_selector.setObjectName(u"weighting_selector")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.weighting_selector.sizePolicy().hasHeightForWidth())
        self.weighting_selector.setSizePolicy(sizePolicy1)
        self.weighting_selector.setMaximumSize(QSize(50, 16777215))
        self.weighting_selector.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.weighting_selector.setMaximum(100)

        self.horizontalLayout_2.addWidget(self.weighting_selector)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)

        self.move_up = QToolButton(ExceptionScriptSelector)
        self.move_up.setObjectName(u"move_up")
        icon = QIcon()
        iconThemeName = u":/images/16x16/go-up.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.move_up.setIcon(icon)

        self.verticalLayout_3.addWidget(self.move_up)

        self.add_script = QToolButton(ExceptionScriptSelector)
        self.add_script.setObjectName(u"add_script")
        icon1 = QIcon()
        iconThemeName = u":/images/16x16/go-previous.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.add_script.setIcon(icon1)

        self.verticalLayout_3.addWidget(self.add_script)

        self.remove_script = QToolButton(ExceptionScriptSelector)
        self.remove_script.setObjectName(u"remove_script")
        icon2 = QIcon()
        iconThemeName = u":/images/16x16/go-next.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.remove_script.setIcon(icon2)

        self.verticalLayout_3.addWidget(self.remove_script)

        self.move_down = QToolButton(ExceptionScriptSelector)
        self.move_down.setObjectName(u"move_down")
        icon3 = QIcon()
        iconThemeName = u":/images/16x16/go-down.png"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.move_down.setIcon(icon3)

        self.verticalLayout_3.addWidget(self.move_down)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_2 = QLabel(ExceptionScriptSelector)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_4.addWidget(self.label_2)

        self.available_scripts = QListWidget(ExceptionScriptSelector)
        self.available_scripts.setObjectName(u"available_scripts")

        self.verticalLayout_4.addWidget(self.available_scripts)


        self.horizontalLayout.addLayout(self.verticalLayout_4)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.button_box = QDialogButtonBox(ExceptionScriptSelector)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(ExceptionScriptSelector)

        QMetaObject.connectSlotsByName(ExceptionScriptSelector)
    # setupUi

    def retranslateUi(self, ExceptionScriptSelector):
        ExceptionScriptSelector.setWindowTitle(_(u"Exception Language Script Selector"))
        self.label.setText(_(u"Selected Scripts"))
        self.threshold_label.setText(_(u"Selected language script match threshold:"))
#if QT_CONFIG(tooltip)
        self.move_up.setToolTip(_(u"Move selected language script up"))
#endif // QT_CONFIG(tooltip)
        self.move_up.setText("")
#if QT_CONFIG(tooltip)
        self.add_script.setToolTip(_(u"Add to selected language scripts"))
#endif // QT_CONFIG(tooltip)
        self.add_script.setText("")
#if QT_CONFIG(tooltip)
        self.remove_script.setToolTip(_(u"Remove selected language script"))
#endif // QT_CONFIG(tooltip)
        self.remove_script.setText("")
#if QT_CONFIG(tooltip)
        self.move_down.setToolTip(_(u"Move selected language script down"))
#endif // QT_CONFIG(tooltip)
        self.move_down.setText("")
        self.label_2.setText(_(u"Available Language Scripts"))
    # retranslateUi

