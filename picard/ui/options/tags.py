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
from PyQt4.Qt import QCompleter
from picard import config
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
        config.BoolOption("setting", "dont_write_tags", False),
        config.BoolOption("setting", "preserve_timestamps", False),
        config.BoolOption("setting", "clear_existing_tags", False),
        config.TextOption("setting", "tags_keep", ""),
        config.TextOption("setting", "tags_clear", ""),
        config.BoolOption("setting", "remove_id3_from_flac", False),
        config.BoolOption("setting", "remove_ape_from_mp3", False),
        config.TextOption("setting", "preserved_tags", ""),
        config.BoolOption("setting", "write_id3v23", True),
        config.TextOption("setting", "id3v2_encoding", "utf-16"),
        config.TextOption("setting", "id3v23_join_with", "/"),
        config.BoolOption("setting", "write_id3v1", True),
        # config.BoolOption("setting", "tpe2_albumartist", False), # Obsolete?
    ]

    def __init__(self, parent=None):
        super(TagsOptionsPage, self).__init__(parent)
        self.ui = Ui_TagsOptionsPage()
        self.ui.setupUi(self)
        self.ui.write_id3v23.clicked.connect(self.update_encodings)
        self.ui.write_id3v24.clicked.connect(self.update_encodings)
        self.ui.clear_existing_tags.clicked.connect(self.update_clear_tags)
        sorted_tag_names = sorted(TAG_NAMES.keys())

        self.tags_keep_completer = self.add_completer(
            sorted_tag_names,
            self.ui.tags_keep,
            self.tags_keep_edited,
            self.tags_keep_completer_activated,
            )

        self.tags_clear_completer = self.add_completer(
            sorted_tag_names,
            self.ui.tags_clear,
            self.tags_clear_edited,
            self.tags_clear_completer_activated,
            )

        self.preserved_tags_completer = self.add_completer(
            sorted_tag_names,
            self.ui.preserved_tags,
            self.preserved_tags_edited,
            self.preserved_tags_completer_activated,
            )

    def add_completer(self, list, field, edited, activated):
        completer = QtGui.QCompleter(list, self)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setWidget(field)
        field.textEdited.connect(edited)
        completer.activated.connect(activated)
        return completer

    def load(self):
        self.ui.write_tags.setChecked(not config.setting["dont_write_tags"])
        self.ui.preserve_timestamps.setChecked(config.setting["preserve_timestamps"])
        self.ui.clear_existing_tags.setChecked(config.setting["clear_existing_tags"])
        self.ui.tags_keep.setText(config.setting["tags_keep"])
        self.ui.tags_clear.setText(config.setting["tags_clear"])
        self.ui.remove_id3_from_flac.setChecked(config.setting["remove_id3_from_flac"])
        self.ui.remove_ape_from_mp3.setChecked(config.setting["remove_ape_from_mp3"])
        self.ui.preserved_tags.setText(config.setting["preserved_tags"])
        self.ui.write_id3v23.setChecked(config.setting["write_id3v23"])
        if config.setting["id3v2_encoding"] == "iso-8859-1":
            self.ui.enc_iso88591.setChecked(True)
        elif config.setting["id3v2_encoding"] == "utf-16":
            self.ui.enc_utf16.setChecked(True)
        else:
            self.ui.enc_utf8.setChecked(True)
        self.ui.id3v23_join_with.setEditText(config.setting["id3v23_join_with"])
        self.ui.write_id3v1.setChecked(config.setting["write_id3v1"])
        self.update_clear_tags()
        self.update_encodings()

    def save(self):
        config.setting["dont_write_tags"] = not self.ui.write_tags.isChecked()
        config.setting["preserve_timestamps"] = self.ui.preserve_timestamps.isChecked()

        clear_existing_tags = self.ui.clear_existing_tags.isChecked()
        update_metadata_box = clear_existing_tags != config.setting["clear_existing_tags"]
        config.setting["clear_existing_tags"] = clear_existing_tags

        tags_keep = unicode(self.ui.tags_keep.text())
        update_metadata_box |= tags_keep != config.setting["tags_keep"]
        config.setting["tags_keep"] = tags_keep

        tags_clear = unicode(self.ui.tags_clear.text())
        update_metadata_box |= tags_clear != config.setting["tags_clear"]
        config.setting["tags_clear"] = tags_clear

        config.setting["remove_id3_from_flac"] = self.ui.remove_id3_from_flac.isChecked()
        config.setting["remove_ape_from_mp3"] = self.ui.remove_ape_from_mp3.isChecked()

        preserved_tags = unicode(self.ui.preserved_tags.text())
        update_metadata_box |= preserved_tags != config.setting["preserved_tags"]
        config.setting["preserved_tags"] = preserved_tags

        config.setting["write_id3v23"] = self.ui.write_id3v23.isChecked()
        if self.ui.enc_iso88591.isChecked():
            config.setting["id3v2_encoding"] = "iso-8859-1"
        elif self.ui.enc_utf16.isChecked():
            config.setting["id3v2_encoding"] = "utf-16"
        else:
            config.setting["id3v2_encoding"] = "utf-8"
        config.setting["id3v23_join_with"] = unicode(self.ui.id3v23_join_with.currentText())
        config.setting["write_id3v1"] = self.ui.write_id3v1.isChecked()

        self.tagger.window.enable_tag_saving_action.setChecked(not config.setting["dont_write_tags"])
        if update_metadata_box:
            self.tagger.window.metadata_box.update()

    def update_encodings(self):
        id3v23 = self.ui.write_id3v23.isChecked()
        if id3v23:
            if self.ui.enc_utf8.isChecked():
                self.ui.enc_utf16.setChecked(True)
        else:
            if self.ui.enc_utf16.isChecked():
                self.ui.enc_utf8.setChecked(True)
        self.ui.id3v23_join_with_label.setEnabled(id3v23)
        self.ui.id3v23_join_with.setEnabled(id3v23)
        self.ui.enc_utf8.setEnabled(not id3v23)

    def update_clear_tags(self):
        clear = self.ui.clear_existing_tags.isChecked()
        self.ui.tags_keep_label.setEnabled(clear)
        self.ui.tags_keep.setEnabled(clear)
        self.ui.tags_clear_label.setEnabled(not clear)
        self.ui.tags_clear.setEnabled(not clear)

    def tags_keep_edited(self, text):
        self.tags_edited(text, self.ui.tags_keep, self.tags_keep_completer)

    def tags_keep_completer_activated(self, text):
        self.tags_completer_activated(text, self.ui.tags_keep, self.tags_keep_completer)

    def tags_clear_edited(self, text):
        self.tags_edited(text, self.ui.tags_clear, self.tags_clear_completer)

    def tags_clear_completer_activated(self, text):
        self.tags_completer_activated(text, self.ui.tags_clear, self.tags_clear_completer)

    def preserved_tags_edited(self, text):
        self.tags_edited(text, self.ui.preserved_tags, self.preserved_tags_completer)

    def preserved_tags_completer_activated(self, text):
        self.tags_completer_activated(text, self.ui.preserved_tags, self.preserved_tags_completer)

    def tags_edited(self, text, field, completer):
        prefix = unicode(text)[:field.cursorPosition()].split(",")[-1].strip()
        completer.setCompletionPrefix(prefix)
        if prefix:
            completer.complete()
        else:
            completer.popup().hide()

    def tags_completer_activated(self, text, field, completer):
        field = self.ui.preserved_tags
        current = unicode(field.text())
        i = field.cursorPosition()
        p = len(completer.completionPrefix())
        field.setText("%s%s, %s" % (current[:i - p], text, current[i:]))
        field.setCursorPosition(i - p + len(text) + 1)


register_options_page(TagsOptionsPage)
