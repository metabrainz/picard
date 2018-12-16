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

import os.path
import re

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard import config
from picard.util.tags import display_tag_name

from picard.ui import PicardDialog
from picard.ui.ui_tagsfromfilenames import Ui_TagsFromFileNamesDialog
from picard.ui.util import StandardButton


class TagsFromFileNamesDialog(PicardDialog):

    defaultsize = QtCore.QSize(560, 400)

    options = [
        config.TextOption("persist", "tags_from_filenames_format", ""),
    ]

    def __init__(self, files, parent=None):
        super().__init__(parent)
        self.ui = Ui_TagsFromFileNamesDialog()
        self.ui.setupUi(self)
        items = [
            "%artist%/%album%/%title%",
            "%artist%/%album%/%tracknumber% %title%",
            "%artist%/%album%/%tracknumber% - %title%",
            "%artist%/%album% - %tracknumber% - %title%",
            "%artist% - %album%/%title%",
            "%artist% - %album%/%tracknumber% %title%",
            "%artist% - %album%/%tracknumber% - %title%",
        ]
        tff_format = config.persist["tags_from_filenames_format"]
        if tff_format not in items:
            selected_index = 0
            if tff_format:
                items.insert(0, tff_format)
        else:
            selected_index = items.index(tff_format)
        self.ui.format.addItems(items)
        self.ui.format.setCurrentIndex(selected_index)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.OK), QtWidgets.QDialogButtonBox.AcceptRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.CANCEL), QtWidgets.QDialogButtonBox.RejectRole)
        self.ui.buttonbox.accepted.connect(self.accept)
        self.ui.buttonbox.rejected.connect(self.reject)
        self.ui.preview.clicked.connect(self.preview)
        self.ui.files.setHeaderLabels([_("File Name")])
        self.files = files
        self.items = []
        for file in files:
            item = QtWidgets.QTreeWidgetItem(self.ui.files)
            item.setText(0, os.path.basename(file.filename))
            self.items.append(item)
        self._tag_re = re.compile(r"(%\w+%)")
        self.numeric_tags = ('tracknumber', 'totaltracks', 'discnumber', 'totaldiscs')

    def parse_response(self):
        tff_format = self.ui.format.currentText()
        columns = []
        format_re = ['(?:^|/)']
        for part in self._tag_re.split(tff_format):
            if part.startswith('%') and part.endswith('%'):
                name = part[1:-1]
                columns.append(name)
                if name in self.numeric_tags:
                    format_re.append('(?P<' + name + r'>\d+)')
                elif name == 'date':
                    format_re.append('(?P<' + name + r'>\d+(?:-\d+(?:-\d+)?)?)')
                else:
                    format_re.append('(?P<' + name + '>[^/]*?)')
            else:
                format_re.append(re.escape(part))
        format_re.append(r'\.(\w+)$')
        format_re = re.compile("".join(format_re))
        return format_re, columns

    def match_file(self, file, tff_format):
        match = tff_format.search(file.filename.replace('\\', '/'))
        if match:
            result = {}
            for name, value in match.groupdict().items():
                value = value.strip()
                if name in self.numeric_tags:
                    value = value.lstrip("0")
                if self.ui.replace_underscores.isChecked():
                    value = value.replace('_', ' ')
                result[name] = value
            return result
        else:
            return {}

    def preview(self):
        tff_format, columns = self.parse_response()
        self.ui.files.setHeaderLabels([_("File Name")] + list(map(display_tag_name, columns)))
        for item, file in zip(self.items, self.files):
            matches = self.match_file(file, tff_format)
            for i, column in enumerate(columns):
                item.setText(i + 1, matches.get(column, ''))
        self.ui.files.header().resizeSections(QtWidgets.QHeaderView.ResizeToContents)
        self.ui.files.header().setStretchLastSection(True)

    def accept(self):
        tff_format, columns = self.parse_response()
        for file in self.files:
            metadata = self.match_file(file, tff_format)
            for name, value in metadata.items():
                file.metadata[name] = value
            file.update()
        config.persist["tags_from_filenames_format"] = self.ui.format.currentText()
        super().accept()
