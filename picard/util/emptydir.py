# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2019 Philipp Wolfer
# Copyright (C) 2020 Laurent Monin
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
import os.path
import shutil

from PyQt5.QtCore import QStandardPaths

from picard.util import get_qt_enum


# Files not considered relevant for a directory. If a directory has only
# some of these files inside it is still considered empty and can be deleted.
JUNK_FILES = set([".DS_Store", "desktop.ini", "Desktop.ini", "Thumbs.db"])

# Special file system locations Picard should never delete.
PROTECTED_DIRECTORIES = set()
for location in get_qt_enum(QStandardPaths, QStandardPaths.StandardLocation):
    value = getattr(QStandardPaths, location)
    for path in QStandardPaths.standardLocations(value):
        PROTECTED_DIRECTORIES.add(os.path.realpath(path))


class SkipRemoveDir(Exception):
    pass


def is_empty_dir(path, ignored_files=None):
    """
    Checks if a directory is considered empty.

    Args:
        path: Path to directory to check.
        ignored_files: List of files to ignore. I only some of those files is
                       inside the directory it is still considered empty.

    Returns:
        True if path is considered an empty directory
        False if path is not considered an empty directory

    Raises:
        NotADirectoryError: path is not a directory
    """
    if ignored_files is None:
        ignored_files = JUNK_FILES
    return not set(os.listdir(path)) - set(ignored_files)


def rm_empty_dir(path):
    """
    Delete a directory if it is considered empty by is_empty_dir and if it
    is not considered a special directory (e.g. the users home dir or ~/Desktop).

    Args:
        path: Path to directory to remove.

    Raises:
        NotADirectoryError: path is not a directory
        SkipRemoveDir: path was not deleted because it is either not empty
                       or considered a special directory.
    """
    if os.path.realpath(path) in PROTECTED_DIRECTORIES:
        raise SkipRemoveDir('%s is a protected directory' % path)
    elif not is_empty_dir(path):
        raise SkipRemoveDir('%s is not empty' % path)
    else:
        shutil.rmtree(path)
