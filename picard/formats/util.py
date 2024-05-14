# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2012 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2010, 2014, 2018-2020, 2023-2024 Philipp Wolfer
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2013, 2017-2019, 2021, 2023-2024 Laurent Monin
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2017 Ville Skyttä
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

import os.path

from picard import log
from picard.extension_points.formats import (
    ext_point_formats,
    ext_to_format,
)


def supported_formats():
    """Returns list of supported formats."""
    return [(file_format.EXTENSIONS, file_format.NAME) for file_format in ext_point_formats]


def supported_extensions():
    """Returns list of supported extensions."""
    return [ext for exts, name in supported_formats() for ext in exts]


def guess_format(filename, options=None):
    """Select the best matching file type amongst supported formats."""
    if options is None:
        options = ext_point_formats
    results = []
    # Since we are reading only 128 bytes and then immediately closing the file,
    # use unbuffered mode.
    with open(filename, 'rb', 0) as fileobj:
        header = fileobj.read(128)
        # Calls the score method of a particular format's associated filetype
        # and assigns a positive score depending on how closely the fileobj's header matches
        # the header for a particular file format.
        results = [(option._File.score(filename, fileobj, header), option.__name__, option)
                   for option in options
                   if getattr(option, "_File", None)]
    if results:
        results.sort()
        if results[-1][0] > 0:
            # return the format with the highest matching score
            return results[-1][2](filename)

    # No positive score i.e. the fileobj's header did not match any supported format
    return None


def open_(filename):
    """Open the specified file and return a File instance with the appropriate format handler, or None."""
    try:
        # Use extension based opening as default
        _name, ext = os.path.splitext(filename)
        if ext:
            if file_format := ext_to_format(ext):
                return file_format(filename)
        # If detection by extension failed, try to guess the format based on file headers
        return guess_format(filename)
    except Exception as error:
        log.error("Error occurred:\n%s", error)
        return None
