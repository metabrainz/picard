# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Laurent Monin
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


from enum import Enum

from picard.i18n import N_


class DebugOptEnum(int, Enum):
    __registry__ = set()

    def __new__(cls, value: int, title: str, description: str) -> None:
        value = int(value)
        obj = super().__new__(cls, value)
        obj._value_ = value
        obj.title = title
        obj.description = description
        return obj

    @property
    def optname(self):
        return self.name.lower()

    @property
    def enabled(self):
        return self in self.__registry__

    @enabled.setter
    def enabled(self, enable: bool):
        if enable:
            self.__registry__.add(self)
        else:
            self.__registry__.discard(self)

    @classmethod
    def opt_names(cls):
        """Returns a comma-separated list of all possible debug options"""
        return ','.join(sorted(o.optname for o in cls))

    @classmethod
    def from_string(cls, string: str):
        """Parse command line argument, a string with comma-separated values,
        and enable corresponding debug options"""
        opts = {str(o).strip().lower() for o in string.split(',')}
        for o in cls:
            o.enabled = o.optname in opts

    @classmethod
    def to_string(cls):
        """Returns a comma-separated list of all enabled debug options"""
        return ','.join(sorted(o.optname for o in cls.__registry__))

    @classmethod
    def set_registry(cls, registry: set):
        """Defines a new set to store enabled debug options"""
        cls.__registry__ = registry

    @classmethod
    def get_registry(cls):
        """Returns current storage for enabled debug options"""
        return cls.__registry__


class DebugOpt(DebugOptEnum):
    PLUGIN_FULLPATH = 1, N_('Plugin Fullpath'), N_('Log plugin full paths')
    WS_POST = 2, N_('Web Service Post Data'), N_('Log data of web service post requests')
    WS_REPLIES = 3, N_('Web Service Replies'), N_('Log content of web service replies')
