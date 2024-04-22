# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_tags.ui'
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
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from picard.ui.widgets.taglisteditor import TagListEditor

from picard.i18n import gettext as _

class Ui_TagsOptionsPage(object):
    def setupUi(self, TagsOptionsPage):
        if not TagsOptionsPage.objectName():
            TagsOptionsPage.setObjectName(u"TagsOptionsPage")
        TagsOptionsPage.resize(567, 525)
        self.vboxLayout = QVBoxLayout(TagsOptionsPage)
        self.vboxLayout.setObjectName(u"vboxLayout")
        self.write_tags = QCheckBox(TagsOptionsPage)
        self.write_tags.setObjectName(u"write_tags")

        self.vboxLayout.addWidget(self.write_tags)

        self.preserve_timestamps = QCheckBox(TagsOptionsPage)
        self.preserve_timestamps.setObjectName(u"preserve_timestamps")

        self.vboxLayout.addWidget(self.preserve_timestamps)

        self.before_tagging = QGroupBox(TagsOptionsPage)
        self.before_tagging.setObjectName(u"before_tagging")
        self.vboxLayout1 = QVBoxLayout(self.before_tagging)
        self.vboxLayout1.setSpacing(2)
        self.vboxLayout1.setObjectName(u"vboxLayout1")
        self.vboxLayout1.setContentsMargins(-1, 6, -1, 7)
        self.clear_existing_tags = QCheckBox(self.before_tagging)
        self.clear_existing_tags.setObjectName(u"clear_existing_tags")

        self.vboxLayout1.addWidget(self.clear_existing_tags)

        self.preserve_images = QCheckBox(self.before_tagging)
        self.preserve_images.setObjectName(u"preserve_images")
        self.preserve_images.setEnabled(False)

        self.vboxLayout1.addWidget(self.preserve_images)

        self.remove_id3_from_flac = QCheckBox(self.before_tagging)
        self.remove_id3_from_flac.setObjectName(u"remove_id3_from_flac")

        self.vboxLayout1.addWidget(self.remove_id3_from_flac)

        self.remove_ape_from_mp3 = QCheckBox(self.before_tagging)
        self.remove_ape_from_mp3.setObjectName(u"remove_ape_from_mp3")

        self.vboxLayout1.addWidget(self.remove_ape_from_mp3)

        self.fix_missing_seekpoints_flac = QCheckBox(self.before_tagging)
        self.fix_missing_seekpoints_flac.setObjectName(u"fix_missing_seekpoints_flac")

        self.vboxLayout1.addWidget(self.fix_missing_seekpoints_flac)

        self.verticalSpacer = QSpacerItem(20, 6, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.vboxLayout1.addItem(self.verticalSpacer)

        self.preserved_tags_label = QLabel(self.before_tagging)
        self.preserved_tags_label.setObjectName(u"preserved_tags_label")

        self.vboxLayout1.addWidget(self.preserved_tags_label)

        self.preserved_tags = TagListEditor(self.before_tagging)
        self.preserved_tags.setObjectName(u"preserved_tags")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.preserved_tags.sizePolicy().hasHeightForWidth())
        self.preserved_tags.setSizePolicy(sizePolicy)

        self.vboxLayout1.addWidget(self.preserved_tags)


        self.vboxLayout.addWidget(self.before_tagging)

        QWidget.setTabOrder(self.write_tags, self.preserve_timestamps)
        QWidget.setTabOrder(self.preserve_timestamps, self.clear_existing_tags)
        QWidget.setTabOrder(self.clear_existing_tags, self.preserve_images)
        QWidget.setTabOrder(self.preserve_images, self.remove_id3_from_flac)
        QWidget.setTabOrder(self.remove_id3_from_flac, self.remove_ape_from_mp3)
        QWidget.setTabOrder(self.remove_ape_from_mp3, self.fix_missing_seekpoints_flac)

        self.retranslateUi(TagsOptionsPage)
        self.clear_existing_tags.toggled.connect(self.preserve_images.setEnabled)

        QMetaObject.connectSlotsByName(TagsOptionsPage)
    # setupUi

    def retranslateUi(self, TagsOptionsPage):
        self.write_tags.setText(_(u"Write tags to files"))
        self.preserve_timestamps.setText(_(u"Preserve timestamps of tagged files"))
        self.before_tagging.setTitle(_(u"Before Tagging"))
        self.clear_existing_tags.setText(_(u"Clear existing tags"))
        self.preserve_images.setText(_(u"Keep embedded images when clearing tags"))
        self.remove_id3_from_flac.setText(_(u"Remove ID3 tags from FLAC files"))
        self.remove_ape_from_mp3.setText(_(u"Remove APEv2 tags from MP3 files"))
        self.fix_missing_seekpoints_flac.setText(_(u"Fix missing seekpoints for FLAC files"))
        self.preserved_tags_label.setText(_(u"Preserve these tags from being cleared or overwritten with MusicBrainz data:"))
        pass
    # retranslateUi

