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

import os.path
import sys
from PyQt4 import QtCore
from picard.metadata import Metadata
from picard.parsefilename import parseFileName
from picard.similarity import similarity
from picard.util import LockableObject

class File(LockableObject):

    NEW = 0
    CHANGED = 1
    TO_BE_SAVED = 2
    SAVED = 3

    def __init__(self, filename):
        LockableObject.__init__(self)
        self.id = self.new_id()
        self.filename = filename
        self.base_filename = os.path.basename(filename)
        self.cluster = None
        self.track = None
        self.state = File.NEW
        self.orig_metadata = Metadata()
        self.metadata = Metadata()
        self.similarity = 1.0

    def __str__(self):
        return ('<File #%d "%s">' % (self.id, self.base_filename)).encode("UTF-8")

    __id_counter = 0

    @staticmethod
    def new_id():
        File.__id_counter += 1
        return File.__id_counter

    def save(self):
        """Save the file."""
        raise NotImplementedError

    def remove_from_cluster(self):
        if self.cluster is not None:
            self.log.debug("%s being removed from %s", self, self.cluster)
            self.cluster.remove_file(self)
            self.cluster = None
            self.update()

    def remove_from_track(self):
        if self.track is not None:
            self.log.debug("%s being removed from %s", self, self.track)
            self.track.remove_file(self)
            self.track = None
            self.update()

    def move_to_cluster(self, cluster):
        if cluster != self.cluster:
            self.remove_from_cluster()
            self.remove_from_track()
            self.log.debug("%s being moved to %s", self, cluster)
            self.state = self.CHANGED
            self.cluster = cluster
            self.cluster.add_file(self)
            self.update()

    def move_to_track(self, track):
        if track != self.track:
            self.remove_from_cluster()
            self.remove_from_track()
            self.log.debug("%s being moved to %s", self, track)
            self.state = self.CHANGED
            if self.orig_metadata["musicbrainz_trackid"] and \
               self.orig_metadata["musicbrainz_trackid"] == track.id:
                self.state = self.SAVED
            self.track = track
            self.track.add_file(self)
            self.update()

    def update(self):
        """Recalculate the similarity and set the state.
        
        This method is thread-safe and shouldn't be called on a locked object.
        """
        self.log.debug("Updating file %s", self)
        self.lock_for_write()
        try:
            self.similarity = self.orig_metadata.compare(self.metadata)
            self.state = self.CHANGED
        finally:
            self.unlock()
        self.tagger.update_file(self)

    def can_save(self):
        """Return if this object can be saved."""
        return True

    def can_remove(self):
        """Return if this object can be removed."""
        return True

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        return True

