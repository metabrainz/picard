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

import re

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
        config.BoolOption("setting", "dont_write_tags", False),
        config.BoolOption("setting", "preserve_timestamps", False),
        config.BoolOption("setting", "clear_existing_tags", False),
        config.BoolOption("setting", "remove_id3_from_flac", False),
        config.BoolOption("setting", "remove_ape_from_mp3", False),
        config.TextOption("setting", "preserved_tags", ""),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TagsOptionsPage()
        self.ui.setupUi(self)
        self.completer = QtWidgets.QCompleter(sorted(TAG_NAMES.keys()), self)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.setWidget(self.ui.preserved_tags)
        self.ui.preserved_tags.textEdited.connect(self.preserved_tags_edited)
        self.completer.activated.connect(self.completer_activated)

    def load(self):
        self.ui.write_tags.setChecked(not config.setting["dont_write_tags"])
        self.ui.preserve_timestamps.setChecked(config.setting["preserve_timestamps"])
        self.ui.clear_existing_tags.setChecked(config.setting["clear_existing_tags"])
        self.ui.remove_ape_from_mp3.setChecked(config.setting["remove_ape_from_mp3"])
        self.ui.remove_id3_from_flac.setChecked(config.setting["remove_id3_from_flac"])
        self.ui.preserved_tags.setText(config.setting["preserved_tags"])

    def save(self):
        config.setting["dont_write_tags"] = not self.ui.write_tags.isChecked()
        config.setting["preserve_timestamps"] = self.ui.preserve_timestamps.isChecked()
        clear_existing_tags = self.ui.clear_existing_tags.isChecked()
        if clear_existing_tags != config.setting["clear_existing_tags"]:
            config.setting["clear_existing_tags"] = clear_existing_tags
            self.tagger.window.metadata_box.update()
        config.setting["remove_ape_from_mp3"] = self.ui.remove_ape_from_mp3.isChecked()
        config.setting["remove_id3_from_flac"] = self.ui.remove_id3_from_flac.isChecked()
        config.setting["preserved_tags"] = re.sub(r"[,\s]+$", "", self.ui.preserved_tags.text())
        self.tagger.window.enable_tag_saving_action.setChecked(not config.setting["dont_write_tags"])

    def preserved_tags_edited(self, text):
        prefix = text[:self.ui.preserved_tags.cursorPosition()].split(",")[-1]
        self.completer.setCompletionPrefix(prefix.strip())
        if prefix:
            self.completer.complete()
        else:
            self.completer.popup().hide()

    def completer_activated(self, text):
        input_field = self.ui.preserved_tags
        current = input_field.text()
        cursor_pos = input_field.cursorPosition()
        prefix_len = len(self.completer.completionPrefix())
        leading_text = current[:cursor_pos - prefix_len].rstrip()
        trailing_text = current[cursor_pos:].lstrip()
        # Replace the autocompletion prefix with the autocompleted text,
        # append a comma so the user can easily enter the next entry
        replacement = ("%s %s, " % (leading_text, text)).lstrip()
        input_field.setText(replacement + trailing_text)
        # Set cursor position to end of autocompleted input
        input_field.setCursorPosition(len(replacement))


register_options_page(TagsOptionsPage)
