# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018, 2020-2021 Laurent Monin
# Copyright (C) 2019-2020 Philipp Wolfer
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


from picard.config import get_config


class PreservedTags:

    opt_name = 'preserved_tags'

    def __init__(self):
        self._tags = self._from_config()

    def _to_config(self):
        config = get_config()
        config.setting[self.opt_name] = sorted(self._tags)

    def _from_config(self):
        config = get_config()
        tags = config.setting[self.opt_name]
        return set(filter(bool, map(self._normalize_tag, tags)))

    @staticmethod
    def _normalize_tag(tag):
        return tag.strip().lower()

    def add(self, name):
        self._tags.add(self._normalize_tag(name))
        self._to_config()

    def discard(self, name):
        self._tags.discard(self._normalize_tag(name))
        self._to_config()

    def __contains__(self, key):
        return self._normalize_tag(key) in self._tags
