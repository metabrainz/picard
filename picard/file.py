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
from PyQt4 import QtCore
from picard.metadata import Metadata
from picard.util import LockableObject, needs_write_lock, needs_read_lock, encode_filename

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
        self.state = File.NEW
        self.orig_metadata = Metadata()
        self.metadata = Metadata()
        self.similarity = 1.0
        self.parent = None

    def __str__(self):
        return '<File #%d "%s">' % (self.id, self.base_filename)

    __id_counter = 0

    @staticmethod
    def new_id():
        File.__id_counter += 1
        return File.__id_counter

    def save(self):
        """Save the file."""
        raise NotImplementedError

    def save_images(self):
        """Save the cover images to disk."""
        if not "~artwork" in self.metadata:
            return
        filename = self.config.setting["cover_image_filename"]
        if not filename:
            filename = "cover"
        filename = os.path.join(os.path.dirname(self.filename),
                                filename)
        filename = encode_filename(filename)
        images = self.metadata["~artwork"]
        i = 0
        for mime, data in images:
            image_filename = filename
            ext = ".jpg" # TODO
            if i > 0:
                image_filename = "%s (%d)" % (filename, i)
            i += 1
            while os.path.exists(image_filename + ext):
                if os.path.getsize(image_filename + ext) == len(data):
                    self.log.debug("Identical file size, not saving %r", image_filename)
                    break
                image_filename = "%s (%d)" % (filename, i)
                i += 1
            else:
                self.log.debug("Saving cover images to %r", image_filename)
                f = open(image_filename + ext, "wb")
                f.write(data)
                f.close()

    def remove(self):
        if self.parent:
            self.log.debug(
                u"Removing %s from %s", self, self.parent)
            self.parent.remove_file(self)

    def move(self, parent):
        if parent != self.parent:
            self.log.debug(
                u"Moving %s from %s to %s", self, self.parent, parent)
            if self.parent:
                self.parent.remove_file(self)
            self.parent = parent
            self.parent.add_file(self)

    def update(self, signal=True):
        self.lock_for_read()
        metadata1 = self.orig_metadata
        metadata2 = self.metadata
        self.unlock()
        similarity = metadata1.compare(metadata2)
        self.lock_for_write()
        self.similarity = similarity
        self.state = self.CHANGED
        self.unlock()
        if signal:
            self.log.debug(u"Updating file %s", self)
            self.parent.update_file(self)

    def can_save(self):
        """Return if this object can be saved."""
        return True

    def can_remove(self):
        """Return if this object can be removed."""
        return True

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        return True

    def can_analyze(self):
        """Return if this object can be fingerprinted."""
        return True

    def can_refresh(self):
        return False

