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

import os

from picard import log


def _find_root_volume():
    try:
        for entry in os.scandir("/Volumes/"):
            if entry.is_symlink() and os.path.realpath(entry.path) == "/":
                return entry.path
    except OSError:
        log.warning("Could not detect macOS boot volume", exc_info=True)
    return None


def extend_root_volume_path(path):
    if not path.startswith("/Volumes/"):
        root_volume = _find_root_volume()
        if root_volume:
            if path.startswith("/"):
                path = path[1:]
            path = os.path.join(root_volume, path)
    return path


def strip_root_volume_path(path):
    if not path.startswith("/Volumes/"):
        return path
    root_volume = _find_root_volume()
    if root_volume:
        norm_path = os.path.normpath(path)
        if norm_path.startswith(root_volume):
            path = os.path.join('/', norm_path[len(root_volume):])
    return path
