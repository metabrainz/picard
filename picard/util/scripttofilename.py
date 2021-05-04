# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2018-2020 Philipp Wolfer
# Copyright (C) 2019-2020 Laurent Monin
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
from picard.const.sys import IS_WIN
from picard.metadata import Metadata
from picard.script import ScriptParser
from picard.util import (
    replace_win32_incompat,
    sanitize_filename,
)
from picard.util.textencoding import replace_non_ascii


def script_to_filename_with_metadata(naming_format, metadata, file=None, settings=None):
    """Creates a valid filename from a script with the given metadata.

    Args:
        naming_format: A string containing the tagger script. The result of
            executing this script will be the filename.
        metadata: A Metadata object. The metadata will not be modified.
        file: A File object (optional)
        settings: The settings. If not set config.setting will be used.

    Returns:
        A tuple with the filename as first element and the updated metadata
        with changes from the script as second.
    """
    if settings is None:
        config = get_config()
        settings = config.setting
    # make sure every metadata can safely be used in a path name
    win_compat = IS_WIN or settings["windows_compatibility"]
    new_metadata = Metadata()
    for name in metadata:
        new_metadata[name] = [sanitize_filename(str(v), win_compat=win_compat)
                              for v in metadata.getall(name)]
    naming_format = naming_format.replace("\t", "").replace("\n", "")
    filename = ScriptParser().eval(naming_format, new_metadata, file)
    if settings["ascii_filenames"]:
        filename = replace_non_ascii(filename, pathsave=True, win_compat=win_compat)
    # replace incompatible characters
    if win_compat:
        filename = replace_win32_incompat(filename)
    # remove null characters
    filename = filename.replace("\x00", "")
    return (filename, new_metadata)


def script_to_filename(naming_format, metadata, file=None, settings=None):
    """Creates a valid filename from a script with the given metadata.

    Args:
        naming_format: A string containing the tagger script. The result of
            executing this script will be the filename.
        metadata: A Metadata object. The metadata will not be modified.
        file: A File object (optional)
        settings: The settings. If not set config.setting will be used.

    Returns:
        The filename.
    """
    (filename, _unused) = script_to_filename_with_metadata(
        naming_format, metadata, file, settings)
    return filename
