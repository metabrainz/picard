# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Laurent Monin
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

from collections.abc import MutableMapping


class SettingsOverride(MutableMapping):
    """ This class can be used to override config temporarly
        Basically it returns config[key] if key isn't found in internal dict

        Typical usage:

        settings = SettingsOverride(config.setting)
        settings["option"] = "value"
    """

    def __init__(self, orig_settings, *args, **kwargs):
        self.orig_settings = orig_settings
        self._dict = dict()
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def __getitem__(self, key):
        try:
            return self._dict[key]
        except KeyError:
            return self.orig_settings[key]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __delitem__(self, key):
        try:
            del self._dict[key]
        except KeyError:
            pass

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict)

    def __repr__(self):
        d = self.orig_settings.copy()
        d.update(self._dict)
        return repr(d)
