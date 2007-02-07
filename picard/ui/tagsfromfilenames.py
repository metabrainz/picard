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
from picard.util import sanitize_date, format_time
from picard.ui.util import StandardButton
from picard.ui.ui_tagsfromfilenames import Ui_TagsFromFileNamesDialog
from picard.ui.tageditor import _tag_name

class TagsFromFileNamesDialog(QtGui.QDialog):

    def __init__(self, files, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_TagsFromFileNamesDialog()
        self.ui.setupUi(self)
        self.ui.format.addItems([
            "%artist%/%album%/%tracknumber% %title%",
            "%artist%/%album%/%tracknumber% - %title%",
            "%artist%/%album - %tracknumber% - %title%",
        ])
        self.ui.buttonbox.addButton(StandardButton(StandardButton.OK), QtGui.QDialogButtonBox.AcceptRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.CANCEL), QtGui.QDialogButtonBox.RejectRole)
        self.connect(self.ui.buttonbox, QtCore.SIGNAL('accepted()'), self, QtCore.SLOT('accept()'))
        self.connect(self.ui.buttonbox, QtCore.SIGNAL('rejected()'), self, QtCore.SLOT('reject()'))
        self.connect(self.ui.preview, QtCore.SIGNAL('clicked()'), self.preview)
        self.ui.files.setHeaderLabels([_("File Name")])
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
                format_re.append('(?P<' + name + '>[^/]*?)')
            else:
                format_re.append(re.escape(part))
        format_re.append('\\.(\\w+)$')
        format_re = re.compile("".join(format_re))
        return format_re, columns

    def match_file(self, file, format):
        match = format.search('/'.join(os.path.split(file.filename)))
        if match:
            return match.groupdict()
        else:
            return {}

    def preview(self):
        format, columns = self.parse_format()
        self.ui.files.setHeaderLabels([_("File Name")] + map(_tag_name, columns))
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
                file.metadata[name] = value.strip()
            file.update()
        QtGui.QDialog.accept(self)
