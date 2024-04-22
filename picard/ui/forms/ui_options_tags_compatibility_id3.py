# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_tags_compatibility_id3.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGroupBox,
    QHBoxLayout, QLabel, QRadioButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

from picard.i18n import gettext as _

class Ui_TagsCompatibilityOptionsPage(object):
    def setupUi(self, TagsCompatibilityOptionsPage):
        if not TagsCompatibilityOptionsPage.objectName():
            TagsCompatibilityOptionsPage.setObjectName(u"TagsCompatibilityOptionsPage")
        TagsCompatibilityOptionsPage.resize(539, 705)
        self.vboxLayout = QVBoxLayout(TagsCompatibilityOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.tag_compatibility = QGroupBox(TagsCompatibilityOptionsPage)
        self.tag_compatibility.setObjectName(u"tag_compatibility")
        self.vboxLayout1 = QVBoxLayout(self.tag_compatibility)
        self.vboxLayout1.setSpacing(2)
        self.vboxLayout1.setObjectName(u"vboxLayout1")
        self.vboxLayout1.setContentsMargins(-1, 6, -1, 7)
        self.id3v2_version = QGroupBox(self.tag_compatibility)
        self.id3v2_version.setObjectName(u"id3v2_version")
        self.id3v2_version.setFlat(False)
        self.id3v2_version.setCheckable(False)
        self.horizontalLayout = QHBoxLayout(self.id3v2_version)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 6, -1, 7)
        self.write_id3v24 = QRadioButton(self.id3v2_version)
        self.write_id3v24.setObjectName(u"write_id3v24")
        self.write_id3v24.setChecked(True)

        self.horizontalLayout.addWidget(self.write_id3v24)

        self.write_id3v23 = QRadioButton(self.id3v2_version)
        self.write_id3v23.setObjectName(u"write_id3v23")
        self.write_id3v23.setChecked(False)

        self.horizontalLayout.addWidget(self.write_id3v23)

        self.label = QLabel(self.id3v2_version)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.vboxLayout1.addWidget(self.id3v2_version)

        self.id3v2_text_encoding = QGroupBox(self.tag_compatibility)
        self.id3v2_text_encoding.setObjectName(u"id3v2_text_encoding")
        self.horizontalLayout_2 = QHBoxLayout(self.id3v2_text_encoding)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, 6, -1, 7)
        self.enc_utf8 = QRadioButton(self.id3v2_text_encoding)
        self.enc_utf8.setObjectName(u"enc_utf8")

        self.horizontalLayout_2.addWidget(self.enc_utf8)

        self.enc_utf16 = QRadioButton(self.id3v2_text_encoding)
        self.enc_utf16.setObjectName(u"enc_utf16")

        self.horizontalLayout_2.addWidget(self.enc_utf16)

        self.enc_iso88591 = QRadioButton(self.id3v2_text_encoding)
        self.enc_iso88591.setObjectName(u"enc_iso88591")

        self.horizontalLayout_2.addWidget(self.enc_iso88591)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.label_2 = QLabel(self.id3v2_text_encoding)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setWordWrap(True)

        self.horizontalLayout_2.addWidget(self.label_2)


        self.vboxLayout1.addWidget(self.id3v2_text_encoding)

        self.hbox_id3v23_join_with = QHBoxLayout()
        self.hbox_id3v23_join_with.setObjectName(u"hbox_id3v23_join_with")
        self.label_id3v23_join_with = QLabel(self.tag_compatibility)
        self.label_id3v23_join_with.setObjectName(u"label_id3v23_join_with")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(4)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_id3v23_join_with.sizePolicy().hasHeightForWidth())
        self.label_id3v23_join_with.setSizePolicy(sizePolicy)

        self.hbox_id3v23_join_with.addWidget(self.label_id3v23_join_with)

        self.id3v23_join_with = QComboBox(self.tag_compatibility)
        self.id3v23_join_with.addItem(u"/")
        self.id3v23_join_with.addItem(u"; ")
        self.id3v23_join_with.addItem(u" / ")
        self.id3v23_join_with.setObjectName(u"id3v23_join_with")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.id3v23_join_with.sizePolicy().hasHeightForWidth())
        self.id3v23_join_with.setSizePolicy(sizePolicy1)
        self.id3v23_join_with.setEditable(True)

        self.hbox_id3v23_join_with.addWidget(self.id3v23_join_with)


        self.vboxLayout1.addLayout(self.hbox_id3v23_join_with)

        self.itunes_compatible_grouping = QCheckBox(self.tag_compatibility)
        self.itunes_compatible_grouping.setObjectName(u"itunes_compatible_grouping")

        self.vboxLayout1.addWidget(self.itunes_compatible_grouping)

        self.write_id3v1 = QCheckBox(self.tag_compatibility)
        self.write_id3v1.setObjectName(u"write_id3v1")

        self.vboxLayout1.addWidget(self.write_id3v1)


        self.vboxLayout.addWidget(self.tag_compatibility)

        self.spacer = QSpacerItem(274, 41, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vboxLayout.addItem(self.spacer)

        QWidget.setTabOrder(self.write_id3v24, self.write_id3v23)
        QWidget.setTabOrder(self.write_id3v23, self.enc_utf8)
        QWidget.setTabOrder(self.enc_utf8, self.enc_utf16)
        QWidget.setTabOrder(self.enc_utf16, self.enc_iso88591)
        QWidget.setTabOrder(self.enc_iso88591, self.id3v23_join_with)
        QWidget.setTabOrder(self.id3v23_join_with, self.itunes_compatible_grouping)
        QWidget.setTabOrder(self.itunes_compatible_grouping, self.write_id3v1)

        self.retranslateUi(TagsCompatibilityOptionsPage)

        QMetaObject.connectSlotsByName(TagsCompatibilityOptionsPage)
    # setupUi

    def retranslateUi(self, TagsCompatibilityOptionsPage):
        self.tag_compatibility.setTitle(_(u"ID3"))
        self.id3v2_version.setTitle(_(u"ID3v2 Version"))
        self.write_id3v24.setText(_(u"2.4"))
        self.write_id3v23.setText(_(u"2.3"))
        self.label.setText("")
        self.id3v2_text_encoding.setTitle(_(u"ID3v2 text encoding"))
        self.enc_utf8.setText(_(u"UTF-8"))
        self.enc_utf16.setText(_(u"UTF-16"))
        self.enc_iso88591.setText(_(u"ISO-8859-1"))
        self.label_2.setText("")
        self.label_id3v23_join_with.setText(_(u"Join multiple ID3v2.3 tags with:"))

#if QT_CONFIG(tooltip)
        self.id3v23_join_with.setToolTip(_(u"<html><head/><body><p>Default is '/' to maintain compatibility with previous Picard releases.</p><p>New alternatives are ';_' or '_/_' or type your own. </p></body></html>"))
#endif // QT_CONFIG(tooltip)
        self.itunes_compatible_grouping.setText(_(u"Save iTunes compatible grouping and work"))
        self.write_id3v1.setText(_(u"Also include ID3v1 tags in the files"))
        pass
    # retranslateUi

