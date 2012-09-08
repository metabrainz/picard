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

from PyQt4 import QtCore, QtGui
from picard.config import BoolOption, TextOption
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_tags import Ui_TagsOptionsPage
from picard.util.tags import TAG_NAMES


class TagsOptionsPage(OptionsPage):

    NAME = "tags"
    TITLE = N_("Tags")
    PARENT = None
    SORT_ORDER = 30
    ACTIVE = True

    options = [
        BoolOption("setting", "clear_existing_tags", False),
        TextOption("setting", "preserved_tags", ""),
        BoolOption("setting", "write_id3v1", True),
        BoolOption("setting", "write_id3v23", True),
        TextOption("setting", "id3v2_encoding", "utf-16"),
        BoolOption("setting", "remove_id3_from_flac", False),
        BoolOption("setting", "remove_ape_from_mp3", False),
        BoolOption("setting", "tpe2_albumartist", False),
        BoolOption("setting", "dont_write_tags", False),
        BoolOption("setting", "preserve_timestamps", False),
    ]

    def __init__(self, parent=None):
        super(TagsOptionsPage, self).__init__(parent)
        self.ui = Ui_TagsOptionsPage()
        self.ui.setupUi(self)
        self.ui.write_id3v23.clicked.connect(self.update_encodings)
        self.ui.write_id3v24.clicked.connect(self.update_encodings)
        self.completer = QtGui.QCompleter(sorted(TAG_NAMES.keys()), self)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.setWidget(self.ui.preserved_tags)
        self.ui.preserved_tags.textEdited.connect(self.preserved_tags_edited)
        self.completer.activated.connect(self.completer_activated)

    def load(self):
        self.ui.write_tags.setChecked(not self.config.setting["dont_write_tags"])
        self.ui.preserve_timestamps.setChecked(self.config.setting["preserve_timestamps"])
        self.ui.clear_existing_tags.setChecked(self.config.setting["clear_existing_tags"])
        self.ui.write_id3v1.setChecked(self.config.setting["write_id3v1"])
        self.ui.write_id3v23.setChecked(self.config.setting["write_id3v23"])
        if self.config.setting["id3v2_encoding"] == "iso-8859-1":
            self.ui.enc_iso88591.setChecked(True)
        elif self.config.setting["id3v2_encoding"] == "utf-16":
            self.ui.enc_utf16.setChecked(True)
        else:
            self.ui.enc_utf8.setChecked(True)
        self.ui.remove_ape_from_mp3.setChecked(self.config.setting["remove_ape_from_mp3"])
        self.ui.remove_id3_from_flac.setChecked(self.config.setting["remove_id3_from_flac"])
        self.ui.preserved_tags.setText(self.config.setting["preserved_tags"])
        self.update_encodings()

    def save(self):
        self.config.setting["dont_write_tags"] = not self.ui.write_tags.isChecked()
        self.config.setting["preserve_timestamps"] = self.ui.preserve_timestamps.isChecked()
        clear_existing_tags = self.ui.clear_existing_tags.isChecked()
        if clear_existing_tags != self.config.setting["clear_existing_tags"]:
            self.config.setting["clear_existing_tags"] = clear_existing_tags
            self.tagger.window.metadata_box.update()
        self.config.setting["write_id3v1"] = self.ui.write_id3v1.isChecked()
        self.config.setting["write_id3v23"] = self.ui.write_id3v23.isChecked()
        if self.ui.enc_iso88591.isChecked():
            self.config.setting["id3v2_encoding"] = "iso-8859-1"
        elif self.ui.enc_utf16.isChecked():
            self.config.setting["id3v2_encoding"] = "utf-16"
        else:
            self.config.setting["id3v2_encoding"] = "utf-8"
        self.config.setting["remove_ape_from_mp3"] = self.ui.remove_ape_from_mp3.isChecked()
        self.config.setting["remove_id3_from_flac"] = self.ui.remove_id3_from_flac.isChecked()
        self.config.setting["preserved_tags"] = unicode(self.ui.preserved_tags.text())
        self.tagger.window.enable_tag_saving_action.setChecked(not self.config.setting["dont_write_tags"])

    def update_encodings(self):
        if self.ui.write_id3v23.isChecked():
            if self.ui.enc_utf8.isChecked():
                self.ui.enc_utf16.setChecked(True)
            self.ui.enc_utf8.setEnabled(False)
        else:
            self.ui.enc_utf8.setEnabled(True)

    def preserved_tags_edited(self, text):
        prefix = unicode(text)[:self.ui.preserved_tags.cursorPosition()].split(" ")[-1]
        self.completer.setCompletionPrefix(prefix)
        if prefix:
            self.completer.complete()
        else:
            self.completer.popup().hide()

    def completer_activated(self, text):
        input = self.ui.preserved_tags
        current = unicode(input.text())
        i = input.cursorPosition()
        p = len(self.completer.completionPrefix())
        input.setText("%s%s %s" % (current[:i - p], text, current[i:]))
        input.setCursorPosition(i - p + len(text) + 1)


register_options_page(TagsOptionsPage)
