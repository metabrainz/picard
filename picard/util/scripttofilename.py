# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2018 Philipp Wolfer
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

from picard import config
from picard.const.sys import IS_WIN
from picard.script import ScriptParser
from picard.util import (
    replace_win32_incompat,
    sanitize_filename,
)
from picard.util.textencoding import replace_non_ascii


def script_to_filename(naming_format, metadata, file=None, settings=None):
    if settings is None:
        settings = config.setting
    # make sure every metadata can safely be used in a path name
    for name in metadata:
        values = [sanitize_filename(str(v)) for v in metadata.getall(name)]
        metadata.set(name, values)
    naming_format = naming_format.replace("\t", "").replace("\n", "")
    filename = ScriptParser().eval(naming_format, metadata, file)
    if settings["ascii_filenames"]:
        filename = replace_non_ascii(filename, pathsave=True)
    # replace incompatible characters
    if settings["windows_compatibility"] or IS_WIN:
        filename = replace_win32_incompat(filename)
    # remove null characters
    filename = filename.replace("\x00", "")
    return filename
