# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2010, 2018, 2020 Philipp Wolfer
# Copyright (C) 2011-2012 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013 Laurent Monin
# Copyright (C) 2014 Sophist-UK
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

from picard import log
from picard.util.imagelist import update_metadata_images


class Item(object):

    def can_save(self):
        """Return if this object can be saved."""
        return False

    def can_remove(self):
        """Return if this object can be removed."""
        return False

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        return False

    def can_analyze(self):
        """Return if this object can be fingerprinted."""
        return False

    def can_autotag(self):
        """Return if this object can be autotagged."""
        return False

    def can_refresh(self):
        """Return if this object can be refreshed."""
        return False

    def can_view_info(self):
        return False

    @property
    def can_show_coverart(self):
        """Return if this object supports cover art."""
        return self.can_edit_tags()

    def can_browser_lookup(self):
        return True

    def is_album_like(self):
        return False

    def load(self, priority=False, refresh=False):
        pass

    @property
    def tracknumber(self):
        """The track number as an int."""
        try:
            return int(self.metadata["tracknumber"])
        except BaseException:
            return 0

    @property
    def discnumber(self):
        """The disc number as an int."""
        try:
            return int(self.metadata["discnumber"])
        except BaseException:
            return 0

    @property
    def errors(self):
        if not hasattr(self, '_errors'):
            self._errors = []
        return self._errors

    def error_append(self, msg):
        log.error('%r: %s', self, msg)
        self.errors.append(msg)

    def clear_errors(self):
        self._errors = []


class FileListItem(Item):

    def __init__(self, files=None):
        super().__init__()
        self.files = files or []
        self.update_metadata_images_enabled = True

    def iterfiles(self, save=False):
        for file in self.files:
            yield file

    def enable_update_metadata_images(self, enabled):
        self.update_metadata_images_enabled = enabled

    def update_metadata_images(self):
        if self.update_metadata_images_enabled and self.can_show_coverart:
            if update_metadata_images(self):
                self.metadata_images_changed.emit()

    def keep_original_images(self):
        self.enable_update_metadata_images(False)
        for file in list(self.files):
            if file.can_show_coverart:
                file.keep_original_images()
        self.enable_update_metadata_images(True)
        self.update_metadata_images()
