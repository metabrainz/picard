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
from picard.util import format_time


class Track(DataObject):

    def __init__(self, id, album=None):
        DataObject.__init__(self, id)
        self.album = album
        self.linked_files = []
        self.metadata = Metadata()

    def __repr__(self):
        return '<Track %s %r>' % (self.id, self.metadata["title"])

    def add_file(self, file):
        if not file in self.linked_files:
            self.linked_files.append(file)
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
        if not file in self.linked_files:
            return
        self.linked_files.remove(file)
        file.metadata.copy(file.saved_metadata)
        self.album._remove_file(self, file)
        self.update()

    def update_file(self, file):
        self.update()

    def update(self):
        self.tagger.emit(QtCore.SIGNAL("track_updated"), self)

    def iterfiles(self, save=False):
        for file in self.linked_files:
            yield file

    def is_linked(self):
        return len(self.linked_files)>0

    def can_save(self):
        """Return if this object can be saved."""
        for file in self.linked_files:
            if file.can_save():
                return True
        return False

    def can_remove(self):
        """Return if this object can be removed."""
        for file in self.linked_files:
            if file.can_remove():
                return True
        return False

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        for file in self.linked_files:
            if file.can_edit_tags():
                return True
        return False

    def can_analyze(self):
        """Return if this object can be fingerprinted."""
        return False

    def can_refresh(self):
        return False

    def column(self, column):
        if len(self.linked_files) == 1:
            similarity = self.linked_files[0].similarity
        else:
            similarity = 1
        if column == 'title':
            return '%s. %s' % (self.metadata['tracknumber'], self.metadata['title']), similarity
        elif column == '~length':
            return format_time(self.metadata.length), similarity
        else:
            return self.metadata[column], similarity
