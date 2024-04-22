# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_tags_compatibility_aac.ui'
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
        self.aac_tags = QGroupBox(TagsCompatibilityOptionsPage)
        self.aac_tags.setObjectName(u"aac_tags")
        self.verticalLayout = QVBoxLayout(self.aac_tags)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.info_label = QLabel(self.aac_tags)
        self.info_label.setObjectName(u"info_label")
        self.info_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.info_label)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.aac_save_ape = QRadioButton(self.aac_tags)
        self.aac_save_ape.setObjectName(u"aac_save_ape")
        self.aac_save_ape.setChecked(True)

        self.verticalLayout.addWidget(self.aac_save_ape)

        self.aac_no_tags = QRadioButton(self.aac_tags)
        self.aac_no_tags.setObjectName(u"aac_no_tags")

        self.verticalLayout.addWidget(self.aac_no_tags)

        self.remove_ape_from_aac = QCheckBox(self.aac_tags)
        self.remove_ape_from_aac.setObjectName(u"remove_ape_from_aac")

        self.verticalLayout.addWidget(self.remove_ape_from_aac)


        self.vboxLayout.addWidget(self.aac_tags)

        self.spacer = QSpacerItem(274, 41, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vboxLayout.addItem(self.spacer)


        self.retranslateUi(TagsCompatibilityOptionsPage)

        QMetaObject.connectSlotsByName(TagsCompatibilityOptionsPage)
    # setupUi

    def retranslateUi(self, TagsCompatibilityOptionsPage):
        self.aac_tags.setTitle(_(u"AAC files"))
        self.info_label.setText(_(u"Picard can save APEv2 tags to pure AAC files, which by default do not support tagging. APEv2 tags in AAC are supported by some players, but players not supporting AAC files with APEv2 tags can have issues loading and playing those files. To deal with this you can choose whether to save tags to those files."))
        self.aac_save_ape.setText(_(u"Save APEv2 tags"))
        self.aac_no_tags.setText(_(u"Do not save tags"))
        self.remove_ape_from_aac.setText(_(u"Remove APEv2 tags from AAC files"))
        pass
    # retranslateUi

