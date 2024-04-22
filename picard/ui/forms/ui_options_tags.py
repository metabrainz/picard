# Form implementation generated from reading ui file 'ui/options_tags.ui'
#
# Created by: PyQt6 UI code generator 6.6.1
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PySide6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_TagsOptionsPage(object):
    def setupUi(self, TagsOptionsPage):
        TagsOptionsPage.setObjectName("TagsOptionsPage")
        TagsOptionsPage.resize(567, 525)
        self.vboxlayout = QtWidgets.QVBoxLayout(TagsOptionsPage)
        self.vboxlayout.setObjectName("vboxlayout")
        self.write_tags = QtWidgets.QCheckBox(parent=TagsOptionsPage)
        self.write_tags.setObjectName("write_tags")
        self.vboxlayout.addWidget(self.write_tags)
        self.preserve_timestamps = QtWidgets.QCheckBox(parent=TagsOptionsPage)
        self.preserve_timestamps.setObjectName("preserve_timestamps")
        self.vboxlayout.addWidget(self.preserve_timestamps)
        self.before_tagging = QtWidgets.QGroupBox(parent=TagsOptionsPage)
        self.before_tagging.setObjectName("before_tagging")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.before_tagging)
        self.vboxlayout1.setContentsMargins(-1, 6, -1, 7)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.clear_existing_tags = QtWidgets.QCheckBox(parent=self.before_tagging)
        self.clear_existing_tags.setObjectName("clear_existing_tags")
        self.vboxlayout1.addWidget(self.clear_existing_tags)
        self.preserve_images = QtWidgets.QCheckBox(parent=self.before_tagging)
        self.preserve_images.setEnabled(False)
        self.preserve_images.setObjectName("preserve_images")
        self.vboxlayout1.addWidget(self.preserve_images)
        self.remove_id3_from_flac = QtWidgets.QCheckBox(parent=self.before_tagging)
        self.remove_id3_from_flac.setObjectName("remove_id3_from_flac")
        self.vboxlayout1.addWidget(self.remove_id3_from_flac)
        self.remove_ape_from_mp3 = QtWidgets.QCheckBox(parent=self.before_tagging)
        self.remove_ape_from_mp3.setObjectName("remove_ape_from_mp3")
        self.vboxlayout1.addWidget(self.remove_ape_from_mp3)
        self.fix_missing_seekpoints_flac = QtWidgets.QCheckBox(parent=self.before_tagging)
        self.fix_missing_seekpoints_flac.setObjectName("fix_missing_seekpoints_flac")
        self.vboxlayout1.addWidget(self.fix_missing_seekpoints_flac)
        spacerItem = QtWidgets.QSpacerItem(20, 6, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.vboxlayout1.addItem(spacerItem)
        self.preserved_tags_label = QtWidgets.QLabel(parent=self.before_tagging)
        self.preserved_tags_label.setObjectName("preserved_tags_label")
        self.vboxlayout1.addWidget(self.preserved_tags_label)
        self.preserved_tags = TagListEditor(parent=self.before_tagging)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.preserved_tags.sizePolicy().hasHeightForWidth())
        self.preserved_tags.setSizePolicy(sizePolicy)
        self.preserved_tags.setObjectName("preserved_tags")
        self.vboxlayout1.addWidget(self.preserved_tags)
        self.vboxlayout.addWidget(self.before_tagging)

        self.retranslateUi(TagsOptionsPage)
        self.clear_existing_tags.toggled['bool'].connect(self.preserve_images.setEnabled) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(TagsOptionsPage)
        TagsOptionsPage.setTabOrder(self.write_tags, self.preserve_timestamps)
        TagsOptionsPage.setTabOrder(self.preserve_timestamps, self.clear_existing_tags)
        TagsOptionsPage.setTabOrder(self.clear_existing_tags, self.preserve_images)
        TagsOptionsPage.setTabOrder(self.preserve_images, self.remove_id3_from_flac)
        TagsOptionsPage.setTabOrder(self.remove_id3_from_flac, self.remove_ape_from_mp3)
        TagsOptionsPage.setTabOrder(self.remove_ape_from_mp3, self.fix_missing_seekpoints_flac)

    def retranslateUi(self, TagsOptionsPage):
        self.write_tags.setText(_("Write tags to files"))
        self.preserve_timestamps.setText(_("Preserve timestamps of tagged files"))
        self.before_tagging.setTitle(_("Before Tagging"))
        self.clear_existing_tags.setText(_("Clear existing tags"))
        self.preserve_images.setText(_("Keep embedded images when clearing tags"))
        self.remove_id3_from_flac.setText(_("Remove ID3 tags from FLAC files"))
        self.remove_ape_from_mp3.setText(_("Remove APEv2 tags from MP3 files"))
        self.fix_missing_seekpoints_flac.setText(_("Fix missing seekpoints for FLAC files"))
        self.preserved_tags_label.setText(_("Preserve these tags from being cleared or overwritten with MusicBrainz data:"))
from picard.ui.widgets.taglisteditor import TagListEditor
