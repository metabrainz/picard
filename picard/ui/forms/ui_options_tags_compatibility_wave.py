# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_tags_compatibility_wave.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QHBoxLayout,
    QLabel, QRadioButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_TagsCompatibilityOptionsPage(object):
    def setupUi(self, TagsCompatibilityOptionsPage):
        if not TagsCompatibilityOptionsPage.objectName():
            TagsCompatibilityOptionsPage.setObjectName(u"TagsCompatibilityOptionsPage")
        TagsCompatibilityOptionsPage.resize(539, 705)
        self.vboxLayout = QVBoxLayout(TagsCompatibilityOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.wave_files = QGroupBox(TagsCompatibilityOptionsPage)
        self.wave_files.setObjectName(u"wave_files")
        self.verticalLayout_3 = QVBoxLayout(self.wave_files)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label = QLabel(self.wave_files)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.label)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.write_wave_riff_info = QCheckBox(self.wave_files)
        self.write_wave_riff_info.setObjectName(u"write_wave_riff_info")

        self.verticalLayout_3.addWidget(self.write_wave_riff_info)

        self.remove_wave_riff_info = QCheckBox(self.wave_files)
        self.remove_wave_riff_info.setObjectName(u"remove_wave_riff_info")

        self.verticalLayout_3.addWidget(self.remove_wave_riff_info)

        self.wave_riff_info_encoding = QGroupBox(self.wave_files)
        self.wave_riff_info_encoding.setObjectName(u"wave_riff_info_encoding")
        self.horizontalLayout_3 = QHBoxLayout(self.wave_riff_info_encoding)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.wave_riff_info_enc_cp1252 = QRadioButton(self.wave_riff_info_encoding)
        self.wave_riff_info_enc_cp1252.setObjectName(u"wave_riff_info_enc_cp1252")
        self.wave_riff_info_enc_cp1252.setChecked(True)

        self.horizontalLayout_3.addWidget(self.wave_riff_info_enc_cp1252)

        self.wave_riff_info_enc_utf8 = QRadioButton(self.wave_riff_info_encoding)
        self.wave_riff_info_enc_utf8.setObjectName(u"wave_riff_info_enc_utf8")

        self.horizontalLayout_3.addWidget(self.wave_riff_info_enc_utf8)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.verticalLayout_3.addWidget(self.wave_riff_info_encoding)


        self.vboxLayout.addWidget(self.wave_files)

        self.spacer = QSpacerItem(274, 41, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vboxLayout.addItem(self.spacer)


        self.retranslateUi(TagsCompatibilityOptionsPage)
        self.write_wave_riff_info.toggled.connect(self.remove_wave_riff_info.setDisabled)

        QMetaObject.connectSlotsByName(TagsCompatibilityOptionsPage)
    # setupUi

    def retranslateUi(self, TagsCompatibilityOptionsPage):
        self.wave_files.setTitle(_(u"WAVE files"))
        self.label.setText(_(u"Picard will tag WAVE files using ID3v2 tags. This is not supported by all software. For compatibility with software which does not support ID3v2 tags in WAVE files additional RIFF INFO tags can be written to the files. RIFF INFO has only limited support for tags and character encodings."))
        self.write_wave_riff_info.setText(_(u"Also include RIFF INFO tags in the files"))
        self.remove_wave_riff_info.setText(_(u"Remove existing RIFF INFO tags from WAVE files"))
        self.wave_riff_info_encoding.setTitle(_(u"RIFF INFO text encoding"))
        self.wave_riff_info_enc_cp1252.setText(_(u"Windows-1252"))
        self.wave_riff_info_enc_utf8.setText(_(u"UTF-8"))
        pass
    # retranslateUi

