# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_tags_compatibility_ac3.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QLabel,
    QRadioButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

from picard.i18n import gettext as _

class Ui_TagsCompatibilityOptionsPage(object):
    def setupUi(self, TagsCompatibilityOptionsPage):
        if not TagsCompatibilityOptionsPage.objectName():
            TagsCompatibilityOptionsPage.setObjectName(u"TagsCompatibilityOptionsPage")
        TagsCompatibilityOptionsPage.resize(539, 705)
        self.vboxLayout = QVBoxLayout(TagsCompatibilityOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.ac3_files = QGroupBox(TagsCompatibilityOptionsPage)
        self.ac3_files.setObjectName(u"ac3_files")
        self.verticalLayout_2 = QVBoxLayout(self.ac3_files)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.info_label = QLabel(self.ac3_files)
        self.info_label.setObjectName(u"info_label")
        self.info_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.info_label)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.ac3_save_ape = QRadioButton(self.ac3_files)
        self.ac3_save_ape.setObjectName(u"ac3_save_ape")
        self.ac3_save_ape.setChecked(True)

        self.verticalLayout_2.addWidget(self.ac3_save_ape)

        self.ac3_no_tags = QRadioButton(self.ac3_files)
        self.ac3_no_tags.setObjectName(u"ac3_no_tags")

        self.verticalLayout_2.addWidget(self.ac3_no_tags)

        self.remove_ape_from_ac3 = QCheckBox(self.ac3_files)
        self.remove_ape_from_ac3.setObjectName(u"remove_ape_from_ac3")

        self.verticalLayout_2.addWidget(self.remove_ape_from_ac3)


        self.vboxLayout.addWidget(self.ac3_files)

        self.spacer = QSpacerItem(274, 41, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vboxLayout.addItem(self.spacer)


        self.retranslateUi(TagsCompatibilityOptionsPage)

        QMetaObject.connectSlotsByName(TagsCompatibilityOptionsPage)
    # setupUi

    def retranslateUi(self, TagsCompatibilityOptionsPage):
        self.ac3_files.setTitle(_(u"AC3 files"))
        self.info_label.setText(_(u"Picard can save APEv2 tags to pure AC3 files, which by default do not support tagging. APEv2 tags in AC3 are supported by some players, but players not supporting AC3 files with APEv2 tags can have issues loading and playing those files. To deal with this you can choose whether to save tags to those files."))
        self.ac3_save_ape.setText(_(u"Save APEv2 tags"))
        self.ac3_no_tags.setText(_(u"Do not save tags"))
        self.remove_ape_from_ac3.setText(_(u"Remove APEv2 tags from AC3 files"))
        pass
    # retranslateUi

