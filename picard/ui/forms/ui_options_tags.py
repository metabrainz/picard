# Form implementation generated from reading ui file 'ui/options_tags.ui'
#
# Created by: PyQt6 UI code generator 6.11.0
#
# Automatically generated - do not edit.
# Use `python setup.py build_ui` to update it.

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.i18n import gettext as _


class Ui_TagsOptionsPage(object):
    def setupUi(self, TagsOptionsPage):
        TagsOptionsPage.setObjectName("TagsOptionsPage")
        TagsOptionsPage.resize(589, 425)
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
        self.vboxlayout.addWidget(self.before_tagging)
        self.preserved_tags_groupbox = QtWidgets.QGroupBox(parent=TagsOptionsPage)
        self.preserved_tags_groupbox.setObjectName("preserved_tags_groupbox")
        self.preserved_tags_layout = QtWidgets.QVBoxLayout(self.preserved_tags_groupbox)
        self.preserved_tags_layout.setObjectName("preserved_tags_layout")
        self.preserved_tags = TagListEditor(parent=self.preserved_tags_groupbox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.preserved_tags.sizePolicy().hasHeightForWidth())
        self.preserved_tags.setSizePolicy(sizePolicy)
        self.preserved_tags.setObjectName("preserved_tags")
        self.preserved_tags_layout.addWidget(self.preserved_tags)
        self.vboxlayout.addWidget(self.preserved_tags_groupbox)
        self.do_not_sanitize_label = QtWidgets.QLabel(parent=TagsOptionsPage)
        self.do_not_sanitize_label.setObjectName("do_not_sanitize_label")
        self.vboxlayout.addWidget(self.do_not_sanitize_label)
        self.do_not_sanitize_container = QtWidgets.QFrame(parent=TagsOptionsPage)
        self.do_not_sanitize_container.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.do_not_sanitize_container.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.do_not_sanitize_container.setObjectName("do_not_sanitize_container")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.do_not_sanitize_container)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.do_not_sanitize_layout = QtWidgets.QVBoxLayout()
        self.do_not_sanitize_layout.setSpacing(4)
        self.do_not_sanitize_layout.setObjectName("do_not_sanitize_layout")
        self.verticalLayout_2.addLayout(self.do_not_sanitize_layout)
        self.vboxlayout.addWidget(self.do_not_sanitize_container)

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
        self.preserved_tags_groupbox.setTitle(_("Preserve these tags from being cleared or overwritten with MusicBrainz data:"))
        self.do_not_sanitize_label.setText(_("Do not sanitize dates for these tag formats:"))
from picard.ui.widgets.taglisteditor import TagListEditor
