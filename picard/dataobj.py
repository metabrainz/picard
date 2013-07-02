# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
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

from picard.util import LockableObject


class DataObject(LockableObject):

    def __init__(self, id):
        LockableObject.__init__(self)
        self.id = id
        self.folksonomy_tags = {}
        self.item = None

    def add_folksonomy_tag(self, name, count):
        self.folksonomy_tags[name] = self.folksonomy_tags.get(name, 0) + count

    @staticmethod
    def merge_folksonomy_tags(this, that):
        for name, count in that.iteritems():
            this[name] = this.get(name, 0) + count
