# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from functools import partial

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard import config
from picard.util.tags import TAG_NAMES

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_tags import Ui_TagsOptionsPage


class TagsOptionsPage(OptionsPage):

    NAME = "tags"
    TITLE = N_("Tags")
    PARENT = None
    SORT_ORDER = 30
    ACTIVE = True

    options = [
        config.BoolOption("setting", "clear_existing_tags", False),
        config.TextOption("setting", "preserved_tags", ""),
        config.BoolOption("setting", "write_id3v1", True),
        config.BoolOption("setting", "write_id3v23", True),
        config.TextOption("setting", "id3v2_encoding", "utf-16"),
        config.TextOption("setting", "id3v23_join_with", "/"),
        config.BoolOption("setting", "remove_id3_from_flac", False),
        config.BoolOption("setting", "remove_ape_from_mp3", False),
        config.BoolOption("setting", "tpe2_albumartist", False),
        config.BoolOption("setting", "itunes_compatible_grouping", False),
        config.BoolOption("setting", "dont_write_tags", False),
        config.BoolOption("setting", "preserve_timestamps", False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TagsOptionsPage()
        self.ui.setupUi(self)
        self.ui.write_id3v23.clicked.connect(self.update_encodings)
        self.ui.write_id3v24.clicked.connect(partial(self.update_encodings, force_utf8=True))
        self.completer = QtWidgets.QCompleter(sorted(TAG_NAMES.keys()), self)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.setWidget(self.ui.preserved_tags)
        self.ui.preserved_tags.textEdited.connect(self.preserved_tags_edited)
        self.completer.activated.connect(self.completer_activated)

    def load(self):
        self.ui.write_tags.setChecked(not config.setting["dont_write_tags"])
        self.ui.preserve_timestamps.setChecked(config.setting["preserve_timestamps"])
        self.ui.clear_existing_tags.setChecked(config.setting["clear_existing_tags"])
        self.ui.write_id3v1.setChecked(config.setting["write_id3v1"])
        if config.setting["write_id3v23"]:
            self.ui.write_id3v23.setChecked(True)
        else:
            self.ui.write_id3v24.setChecked(True)
        if config.setting["id3v2_encoding"] == "iso-8859-1":
            self.ui.enc_iso88591.setChecked(True)
        elif config.setting["id3v2_encoding"] == "utf-16":
            self.ui.enc_utf16.setChecked(True)
        else:
            self.ui.enc_utf8.setChecked(True)
        self.ui.id3v23_join_with.setEditText(config.setting["id3v23_join_with"])
        self.ui.remove_ape_from_mp3.setChecked(config.setting["remove_ape_from_mp3"])
        self.ui.remove_id3_from_flac.setChecked(config.setting["remove_id3_from_flac"])
        self.ui.itunes_compatible_grouping.setChecked(config.setting["itunes_compatible_grouping"])
        self.ui.preserved_tags.setText(config.setting["preserved_tags"])
        self.update_encodings()

    def save(self):
        config.setting["dont_write_tags"] = not self.ui.write_tags.isChecked()
        config.setting["preserve_timestamps"] = self.ui.preserve_timestamps.isChecked()
        clear_existing_tags = self.ui.clear_existing_tags.isChecked()
        if clear_existing_tags != config.setting["clear_existing_tags"]:
            config.setting["clear_existing_tags"] = clear_existing_tags
            self.tagger.window.metadata_box.update()
        config.setting["write_id3v1"] = self.ui.write_id3v1.isChecked()
        config.setting["write_id3v23"] = self.ui.write_id3v23.isChecked()
        config.setting["id3v23_join_with"] = self.ui.id3v23_join_with.currentText()
        if self.ui.enc_iso88591.isChecked():
            config.setting["id3v2_encoding"] = "iso-8859-1"
        elif self.ui.enc_utf16.isChecked():
            config.setting["id3v2_encoding"] = "utf-16"
        else:
            config.setting["id3v2_encoding"] = "utf-8"
        config.setting["remove_ape_from_mp3"] = self.ui.remove_ape_from_mp3.isChecked()
        config.setting["remove_id3_from_flac"] = self.ui.remove_id3_from_flac.isChecked()
        config.setting["itunes_compatible_grouping"] = self.ui.itunes_compatible_grouping.isChecked()
        config.setting["preserved_tags"] = self.ui.preserved_tags.text()
        self.tagger.window.enable_tag_saving_action.setChecked(not config.setting["dont_write_tags"])

    def update_encodings(self, force_utf8=False):
        if self.ui.write_id3v23.isChecked():
            if self.ui.enc_utf8.isChecked():
                self.ui.enc_utf16.setChecked(True)
            self.ui.enc_utf8.setEnabled(False)
            self.ui.label_id3v23_join_with.setEnabled(True)
            self.ui.id3v23_join_with.setEnabled(True)
        else:
            self.ui.enc_utf8.setEnabled(True)
            if force_utf8:
                self.ui.enc_utf8.setChecked(True)
            self.ui.label_id3v23_join_with.setEnabled(False)
            self.ui.id3v23_join_with.setEnabled(False)

    def preserved_tags_edited(self, text):
        prefix = text[:self.ui.preserved_tags.cursorPosition()].split(",")[-1]
        self.completer.setCompletionPrefix(prefix)
        if prefix:
            self.completer.complete()
        else:
            self.completer.popup().hide()

    def completer_activated(self, text):
        input_field = self.ui.preserved_tags
        current = input_field.text()
        i = input_field.cursorPosition()
        p = len(self.completer.completionPrefix())
        input_field.setText("%s%s %s" % (current[:i - p], text, current[i:]))
        input_field.setCursorPosition(i - p + len(text) + 1)


register_options_page(TagsOptionsPage)
