# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_TagsOptionsPage(object):
    def setupUi(self, TagsOptionsPage):
        TagsOptionsPage.setObjectName("TagsOptionsPage")
        TagsOptionsPage.resize(539, 525)
        self.vboxlayout = QtWidgets.QVBoxLayout(TagsOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.write_tags = QtWidgets.QCheckBox(TagsOptionsPage)
        self.write_tags.setObjectName("write_tags")
        self.vboxlayout.addWidget(self.write_tags)
        self.preserve_timestamps = QtWidgets.QCheckBox(TagsOptionsPage)
        self.preserve_timestamps.setObjectName("preserve_timestamps")
        self.vboxlayout.addWidget(self.preserve_timestamps)
        self.before_tagging = QtWidgets.QGroupBox(TagsOptionsPage)
        self.before_tagging.setObjectName("before_tagging")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.before_tagging)
        self.vboxlayout1.setContentsMargins(-1, 6, -1, 7)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.clear_existing_tags = QtWidgets.QCheckBox(self.before_tagging)
        self.clear_existing_tags.setObjectName("clear_existing_tags")
        self.vboxlayout1.addWidget(self.clear_existing_tags)
        self.remove_id3_from_flac = QtWidgets.QCheckBox(self.before_tagging)
        self.remove_id3_from_flac.setObjectName("remove_id3_from_flac")
        self.vboxlayout1.addWidget(self.remove_id3_from_flac)
        self.remove_ape_from_mp3 = QtWidgets.QCheckBox(self.before_tagging)
        self.remove_ape_from_mp3.setObjectName("remove_ape_from_mp3")
        self.vboxlayout1.addWidget(self.remove_ape_from_mp3)
        spacerItem = QtWidgets.QSpacerItem(20, 6, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.vboxlayout1.addItem(spacerItem)
        self.preserved_tags_label = QtWidgets.QLabel(self.before_tagging)
        self.preserved_tags_label.setObjectName("preserved_tags_label")
        self.vboxlayout1.addWidget(self.preserved_tags_label)
        self.preserved_tags = TagListEditor(self.before_tagging)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.preserved_tags.sizePolicy().hasHeightForWidth())
        self.preserved_tags.setSizePolicy(sizePolicy)
        self.preserved_tags.setObjectName("preserved_tags")
        self.vboxlayout1.addWidget(self.preserved_tags)
        self.vboxlayout.addWidget(self.before_tagging)

        self.retranslateUi(TagsOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(TagsOptionsPage)
        TagsOptionsPage.setTabOrder(self.write_tags, self.preserve_timestamps)
        TagsOptionsPage.setTabOrder(self.preserve_timestamps, self.clear_existing_tags)
        TagsOptionsPage.setTabOrder(self.clear_existing_tags, self.remove_id3_from_flac)
        TagsOptionsPage.setTabOrder(self.remove_id3_from_flac, self.remove_ape_from_mp3)
        TagsOptionsPage.setTabOrder(self.remove_ape_from_mp3, self.preserved_tags)

    def retranslateUi(self, TagsOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.write_tags.setText(_("Write tags to files"))
        self.preserve_timestamps.setText(_("Preserve timestamps of tagged files"))
        self.before_tagging.setTitle(_("Before Tagging"))
        self.clear_existing_tags.setText(_("Clear existing tags"))
        self.remove_id3_from_flac.setText(_("Remove ID3 tags from FLAC files"))
        self.remove_ape_from_mp3.setText(_("Remove APEv2 tags from MP3 files"))
        self.preserved_tags_label.setText(_("Preserve these tags from being cleared or overwritten with MusicBrainz data:"))
from picard.ui.widgets.taglisteditor import TagListEditor
