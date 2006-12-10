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
from PyQt4 import QtCore, QtGui
from picard.util import sanitize_date, format_time, encode_filename

class AdvancedTagEditor(QtGui.QDialog):

    def __init__(self, file, parent=None):
        QtGui.QDialog.__init__(self, parent)
        from picard.ui.ui_advtageditor import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.tags.setHeaderLabels([u"Name", u"Value"])
        self.connect(self.ui.tags, QtCore.SIGNAL("itemActivated (QTreeWidgetItem*, int)"), self.open_editor)
        self.file = file
        self.metadata = file.metadata
        self.setup_info()
        self.load()

    def setup_info(self):
        info = []
        if '~format' in self.file.metadata:
            info.append((_('Format:'), self.file.metadata['~format']))
        if '~#length' in self.file.metadata:
            info.append((_('Length:'), format_time(self.file.metadata['~#length'])))
        if '~#bitrate' in self.file.metadata:
            info.append((_('Bitrate:'), '%d kpbs' % self.file.metadata['~#bitrate']))
        if '~#sample_rate' in self.file.metadata:
            info.append((_('Sample rate:'), '%d Hz' % self.file.metadata['~#sample_rate']))
        if '~#bits_per_sample' in self.file.metadata:
            info.append((_('Bits per sample:'), str(self.file.metadata['~#bits_per_sample'])))
        if '~#channels' in self.file.metadata:
            ch = self.file.metadata['~#channels']
            if ch == 1: ch = _('Mono')
            elif ch == 2: ch = _('Stereo')
            else: ch = str(ch)
            info.append((_('Channels:'), ch))
        info.append((_('Filename:'), self.file.filename))
        try:
            size = os.path.getsize(encode_filename(self.file.filename))
            if size < 1024:
                size = '%d B' % size
            elif size < 1024 * 1024:
                size = '%0.1f kB' % (size / 1024.0)
            else:
                size = '%0.1f MB' % (size / 1024.0 / 1024.0)
            info.append((_('Size:'), size))
        except:
            pass
        text = '<br/>'.join(map(lambda i: '<b>%s</b><br/>%s' % i, info))
        self.ui.info.setText(text)

    def accept(self):
        self.save()
        QtGui.QDialog.accept(self)

    def open_editor(self, item, column):
        print "itemActivated"

    def load(self):
        for name, value in self.metadata.items():
            if not name.startswith("~"):
                item = QtGui.QTreeWidgetItem(self.ui.tags)
                item.setText(0, name)
                item.setText(1, value)

        if "~artwork" in self.metadata:
            pictures = self.metadata.getall("~artwork")
            for mime, data in pictures:
                item = QtGui.QListWidgetItem()
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(data)
                icon = QtGui.QIcon(pixmap)
                item.setIcon(icon)
                self.ui.artwork_list.addItem(item)

    def save(self):
        for name, convert in self.fields:
            text = unicode(getattr(self.ui, name).text())
            if convert:
                text = convert(text)
            if text or name in self.metadata:
                self.metadata[name] = text
        self.file.update()
