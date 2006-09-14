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

from picard.util import sanitize_date

_translate = {
    "Album Artist": "albumartist"
}

def read_apev2_tags(tags, metadata):
    for name, values in tags.items():
        value = ";".join(values)
        if name == "Year":
            name = "date"
            value = sanitize_date(value)
        elif name == "Track":
            name = "tracknumber"
            track = value.split("/")
            if len(track) > 1:
                metadata["totaltracks"] = track[1]
                value = track[0]
        elif name in _translate:
            name = _translate[name]
        else:
            name = name.lower()
        metadata[name] = value

def write_apev2_tags(tags, metadata):
    pass
