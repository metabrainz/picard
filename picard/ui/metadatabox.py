# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
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
from picard.util import format_time

class MetadataBox(QtGui.QGroupBox):
    
    def __init__(self, parent, title, readOnly=False):
        QtGui.QGroupBox.__init__(self, title)
        self.metadata = None
        self.readOnly = readOnly

        from picard.ui.ui_metadata import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.title.setReadOnly(self.readOnly)
        self.ui.artist.setReadOnly(self.readOnly)
        self.ui.album.setReadOnly(self.readOnly)
        self.ui.tracknumber.setReadOnly(self.readOnly)
        self.ui.date.setReadOnly(self.readOnly)

        self.connect(self.ui.lookup, QtCore.SIGNAL("clicked()"), self.lookup)
        self.connect(self.ui.title, QtCore.SIGNAL("editingFinished()"),
                     self.update_metadata_title)
        self.connect(self.ui.album, QtCore.SIGNAL("editingFinished()"),
                     self.update_metadata_album)
        self.connect(self.ui.artist, QtCore.SIGNAL("editingFinished()"),
                     self.update_metadata_artist)
        self.connect(self.ui.tracknumber, QtCore.SIGNAL("editingFinished()"),
                     self.update_metadata_tracknum)
        self.connect(self.ui.date, QtCore.SIGNAL("editingFinished()"),
                     self.update_metadata_date)

        self.disable()

    def enable(self, album):
        if not album:
            self.ui.title.setDisabled(False)
            self.ui.tracknumber.setDisabled(False)
        else:
            self.ui.title.setDisabled(True)
            self.ui.tracknumber.setDisabled(True)
        self.ui.artist.setDisabled(False)
        self.ui.album.setDisabled(False)
        self.ui.length.setDisabled(False)
        self.ui.date.setDisabled(False)
        self.ui.lookup.setDisabled(False)

    def disable(self):
        self.ui.title.setDisabled(True)
        self.ui.artist.setDisabled(True)
        self.ui.album.setDisabled(True)
        self.ui.tracknumber.setDisabled(True)
        self.ui.length.setDisabled(True)
        self.ui.date.setDisabled(True)
        self.ui.lookup.setDisabled(True)

    def clear(self):
        self.ui.title.clear()
        self.ui.artist.clear()
        self.ui.album.clear()
        self.ui.length.clear()
        self.ui.tracknumber.clear()
        self.ui.date.clear()

    def setMetadata(self, metadata, album=False, file=None):
        self.metadata = metadata
        self.file = file
        if metadata:
            text = metadata.get(u"TITLE", u"")
            self.ui.title.setText(text)
            text = metadata.get(u"ARTIST", u"")
            self.ui.artist.setText(text)
            text = metadata.get(u"ALBUM", u"")
            self.ui.album.setText(text)
            text = metadata.get(u"TRACKNUMBER", u"")
            self.ui.tracknumber.setText(text)
            text = format_time(metadata.get("~#length", 0))
            self.ui.length.setText(text)
            text = metadata.get(u"DATE", u"")
            self.ui.date.setText(text)
            self.enable(album)
        else:
            self.clear()
            self.disable()

    def lookup(self):
        """Tell the tagger to lookup the metadata."""
        self.tagger.lookup(self.metadata)

    def update_metadata(self, edit, name):
        self.metadata[name] = unicode(edit.text())
        self.file.update()

    def update_metadata_title(self):
        self.update_metadata(self.ui.title, "title")

    def update_metadata_album(self):
        self.update_metadata(self.ui.album, "album")

    def update_metadata_artist(self):
        self.update_metadata(self.ui.artist, "artist")

    def update_metadata_tracknum(self):
        self.update_metadata(self.ui.tracknumber, "tracknumber")
        
    def update_metadata_date(self):
        self.update_metadata(self.ui.date, "date")

