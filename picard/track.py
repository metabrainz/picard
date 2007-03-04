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

from PyQt4 import QtCore
from picard.metadata import Metadata
from picard.dataobj import DataObject


class Track(DataObject):

    def __init__(self, id, album=None):
        DataObject.__init__(self, id)
        self.album = album
        self.linked_file = None
        self.metadata = Metadata()

    def __repr__(self):
        return '<Track %s %r>' % (self.id, self.metadata["title"])

    def add_file(self, file):
        if self.linked_file:
            self.linked_file.move(self.album.unmatched_files)
        self.linked_file = file
        file.saved_metadata.copy(file.metadata)
        file.metadata.copy(self.metadata)
        if 'musicip_puid' in file.saved_metadata:
            file.metadata['musicip_puid'] = file.saved_metadata['musicip_puid']
        file.metadata['~extension'] = file.orig_metadata['~extension']
        file.metadata.changed = True
        self.album._add_file(self, file)
        file.update(signal=False)
        self.update()

    def remove_file(self, file):
        file = self.linked_file
        file.metadata.copy(file.saved_metadata)
        self.linked_file = None
        self.album._remove_file(self, file)
        self.update()
        return file

    def update_file(self, file):
        self.update()

    def update(self):
        self.tagger.emit(QtCore.SIGNAL("track_updated"), self)

    def is_linked(self):
        return (self.linked_file is not None)

    def can_save(self):
        """Return if this object can be saved."""
        if self.linked_file:
            return self.linked_file.can_save()
        return False

    def can_remove(self):
        """Return if this object can be removed."""
        if self.linked_file:
            return self.linked_file.can_remove()
        return False

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        if self.linked_file:
            return self.linked_file.can_edit_tags()
        return False

    def can_analyze(self):
        """Return if this object can be fingerprinted."""
        return False

    def can_refresh(self):
        return False

    def column(self, column):
        if self.linked_file is None:
            similarity = 1
        else:
            similarity = self.linked_file.similarity
        if column == 'title':
            text = '%s. %s' % (self.metadata['tracknumber'], self.metadata['title'])
        else:
            text = self.metadata[column]
        return text, similarity
