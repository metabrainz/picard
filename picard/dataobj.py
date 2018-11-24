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

from picard import config
from picard.util import LockableObject


class DataObject(LockableObject):

    def __init__(self, obj_id):
        super().__init__()
        self.id = obj_id
        self.genres = {}
        self.item = None

    def add_genre(self, name, count):
        self.genres[name] = self.genres.get(name, 0) + count

    @staticmethod
    def set_genre_inc_params(inc):
        require_authentication = False
        if config.setting['use_genres']:
            use_folksonomy = config.setting['folksonomy_tags']
            if config.setting['only_my_genres']:
                require_authentication = True
                inc += ['user-tags'] if use_folksonomy else ['user-genres']
            else:
                inc += ['tags'] if use_folksonomy else ['genres']
        return require_authentication

    @staticmethod
    def merge_genres(this, that):
        for name, count in that.items():
            this[name] = this.get(name, 0) + count
