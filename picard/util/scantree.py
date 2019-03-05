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


import os
import stat

from picard.const.sys import IS_WIN


if IS_WIN:
    def _is_hidden(entry):
        attr = entry.stat().st_file_attributes
        return bool(attr & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM))
else:
    def _is_hidden(entry):
        return (entry.name[0] == '.')


def scantree(path, ignore_hidden=True, recursive=False):
    for entry in os.scandir(path):
        try:
            if ignore_hidden and _is_hidden(entry):
                continue
            if entry.is_file():
                yield entry.path
            if recursive and entry.is_dir():
                yield from scantree(
                    entry.path,
                    ignore_hidden=ignore_hidden,
                    recursive=recursive
                )
        except OSError:
            continue
