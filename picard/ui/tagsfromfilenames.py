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
import os.path
from PyQt4 import QtCore, QtGui
from picard.config import Option, TextOption
from picard.ui.util import StandardButton
from picard.ui.ui_tagsfromfilenames import Ui_TagsFromFileNamesDialog
from picard.util.tags import display_tag_name

class TagsFromFileNamesDialog(QtGui.QDialog):

    options = [
        TextOption("persist", "tags_from_filenames_format", ""),
        Option("persist", "tags_from_filenames_position", QtCore.QPoint(), QtCore.QVariant.toPoint),
        Option("persist", "tags_from_filenames_size", QtCore.QSize(560, 400), QtCore.QVariant.toSize),
    ]

    def __init__(self, files, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_TagsFromFileNamesDialog()
        self.ui.setupUi(self)
        items = [
            "%artist%/%album%/%tracknumber% %title%",
            "%artist%/%album%/%tracknumber% - %title%",
            "%artist%/%album - %tracknumber% - %title%",
        ]
        format = self.config.persist["tags_from_filenames_format"]
        if format and format not in items:
            items.insert(0, format)
        self.ui.format.addItems(items)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.OK), QtGui.QDialogButtonBox.AcceptRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.CANCEL), QtGui.QDialogButtonBox.RejectRole)
        self.ui.buttonbox.accepted.connect(self.accept)
        self.ui.buttonbox.rejected.connect(self.reject)
        self.ui.preview.clicked.connect(self.preview)
        self.ui.files.setHeaderLabels([_("File Name")])
        self.restoreWindowState()
        self.files = files
        self.items = []
        for file in files:
            item = QtGui.QTreeWidgetItem(self.ui.files)
            item.setText(0, os.path.basename(file.filename))
            self.items.append(item)
        self._tag_re = re.compile("(%\w+%)")

    def parse_format(self):
        format = unicode(self.ui.format.currentText())
        columns = []
        format_re = ['(?:^|/)']
        for part in self._tag_re.split(format):
            if part.startswith('%') and part.endswith('%'):
                name = part[1:-1]
                columns.append(name)
                if name in ('tracknumber', 'totaltracks', 'discnumber', 'totaldiscs'):
                    format_re.append('(?P<' + name + '>\d+)')
                elif name in ('date'):
                    format_re.append('(?P<' + name + '>\d+(?:-\d+(?:-\d+)?)?)')
                else:
                    format_re.append('(?P<' + name + '>[^/]*?)')
            else:
                format_re.append(re.escape(part))
        format_re.append('\\.(\\w+)$')
        format_re = re.compile("".join(format_re))
        return format_re, columns

    def match_file(self, file, format):
        match = format.search('/'.join(os.path.split(file.filename)))
        if match:
            result = {}
            for name, value in match.groupdict().iteritems():
                value = value.strip()
                if self.ui.replace_underscores.isChecked():
                    value = value.replace('_', ' ')
                result[name] = value
            return result
        else:
            return {}

    def preview(self):
        format, columns = self.parse_format()
        self.ui.files.setHeaderLabels([_("File Name")] + map(display_tag_name, columns))
        for item, file in zip(self.items, self.files):
            matches = self.match_file(file, format)
            for i in range(len(columns)):
                value = matches.get(columns[i], '')
                item.setText(i + 1, value)
        self.ui.files.header().resizeSections(QtGui.QHeaderView.ResizeToContents)
        self.ui.files.header().setStretchLastSection(True)

    def accept(self):
        format, columns = self.parse_format()
        for file in self.files:
            metadata = self.match_file(file, format)
            for name, value in metadata.iteritems():
                file.metadata[name] = value
            file.update()
        self.config.persist["tags_from_filenames_format"] = self.ui.format.currentText()
        self.saveWindowState()
        QtGui.QDialog.accept(self)

    def reject(self):
        self.saveWindowState()
        QtGui.QDialog.reject(self)

    def closeEvent(self, event):
        self.saveWindowState()
        event.accept()

    def saveWindowState(self):
        pos = self.pos()
        if not pos.isNull():
            self.config.persist["tags_from_filenames_position"] = pos
        self.config.persist["tags_from_filenames_size"] = self.size()

    def restoreWindowState(self):
        pos = self.config.persist["tags_from_filenames_position"]
        if pos.x() > 0 and pos.y() > 0:
            self.move(pos)
        self.resize(self.config.persist["tags_from_filenames_size"])
