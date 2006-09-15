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
from picard.util import sanitize_date

class TagEditor(QtGui.QDialog):

    fields = [
        ("title", None),
        ("album", None),
        ("artist", None),
        ("tracknumber", None),
        ("totaltracks", None),
        ("discnumber", None),
        ("totaldiscs", None),
        ("date", sanitize_date),
        ("albumartist", None),
        ("composer", None),
        ("conductor", None),
        ("ensemble", None),
        ("lyricist", None),
        ("arranger", None),
        ("producer", None),
        ("engineer", None),
        ("remixer", None),
        ("musicbrainz_trackid", None),
        ("musicbrainz_albumid", None),
        ("musicbrainz_artistid", None),
        ("musicbrainz_albumartistid", None),
        ("musicip_puid", None),
    ]

    def __init__(self, metadata, parent=None):
        QtGui.QDialog.__init__(self, parent)

        from picard.ui.ui_tageditor import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.metadata = metadata
        self.load()

    def accept(self):
        self.save()
        QtGui.QDialog.accept(self)

    def load(self):
        for name, convert in self.fields:
            text = self.metadata[name]
            getattr(self.ui, name).setText(text)

        if "~artwork" in self.metadata:
            pictures = self.metadata["~artwork"]
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

