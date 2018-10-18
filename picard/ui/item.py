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
