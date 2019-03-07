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
from pathlib import Path
import stat

from picard.const.sys import IS_WIN


if IS_WIN:
    def _is_hidden(entry):
        attr = entry.stat().st_file_attributes
        return bool(attr & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM))
else:
    def _is_hidden(entry):
        return (entry.name[0] == '.')


def is_relative(what, to_path):
    try:
        unused = what.relative_to(to_path)
        return True
    except ValueError:
        return False


def scantree(path, ignore_hidden=True, recursive=False, follow_symlinks=True, _seen_symlinks=None):
    if _seen_symlinks is None:
        _seen_symlinks = set()
    p = Path(path)
    if p.is_symlink():
        if not follow_symlinks:
            return
        path = str(p.resolve())
    for entry in os.scandir(path):
        try:
            if ignore_hidden and _is_hidden(entry):
                continue
            if entry.is_symlink():
                if not follow_symlinks:
                    continue
                symlink = Path(entry.path)
                target = symlink.resolve()
                if target in _seen_symlinks:
                    # ignore loops, preventing infinite recursion
                    continue
                _seen_symlinks.add(target)
                #print("symlink %s -> %s" % (entry.path, target))
                if target.parent == path:
                    # ignore symlink pointing to a file in same dir
                    continue
                if is_relative(target, path):
                    # ignore symlink pointing to a file in a subdirectory
                    continue
                if recursive and target.is_dir():
                    # follow symlink pointing to a directory
                    yield from scantree(
                        target,
                        ignore_hidden=ignore_hidden,
                        recursive=recursive,
                        follow_symlinks=follow_symlinks,
                        _seen_symlinks=_seen_symlinks
                    )
                    continue
                if not target.is_file():
                    # ignore symlinks to anything but files
                    continue
                yield str(target)
            elif entry.is_file():
                yield entry.path
            elif recursive and entry.is_dir():
                yield from scantree(
                    entry.path,
                    ignore_hidden=ignore_hidden,
                    recursive=recursive,
                    follow_symlinks=follow_symlinks,
                    _seen_symlinks=_seen_symlinks
                )
        except OSError:
            continue
