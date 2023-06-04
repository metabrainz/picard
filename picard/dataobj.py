# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2008 Lukáš Lalinský
# Copyright (C) 2011-2012 Michael Wiencek
# Copyright (C) 2013, 2020-2021, 2023 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018, 2021 Philipp Wolfer
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


from collections import Counter

from picard.config import get_config
from picard.util import LockableObject


class DataObject(LockableObject):

    def __init__(self, obj_id):
        super().__init__()
        self.id = obj_id
        self.genres = Counter()
        self.item = None

    def add_genre(self, name, count):
        if name:
            self.genres[name] += count

    @staticmethod
    def set_genre_inc_params(inc, config=None):
        require_authentication = False
        config = config or get_config()
        if config.setting['use_genres']:
            use_folksonomy = config.setting['folksonomy_tags']
            if config.setting['only_my_genres']:
                require_authentication = True
                inc |= {'user-tags'} if use_folksonomy else {'user-genres'}
            else:
                inc |= {'tags'} if use_folksonomy else {'genres'}
        return require_authentication
