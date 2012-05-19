# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2009 Philipp Wolfer
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

MIME_TYPE_EXTENSION_MAP = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/tiff': '.tiff',
}

EXTENSION_MIME_TYPE_MAP = dict([(b, a) for a, b in MIME_TYPE_EXTENSION_MAP.items()])

def get_from_data(data, filename=None, default=None):
    """Tries to determine the mime type from the given data."""
    if data.startswith('\xff\xd8\xff'):
        return 'image/jpeg'
    elif data.startswith('\x89PNG\x0d\x0a\x1a\x0a'):
        return 'image/png'
    elif data.startswith('GIF87a') or data.startswith('GIF89a'):
        return 'image/gif'
    elif data.startswith('MM\x00*') or data.startswith('II*\x00'):
        return 'image/tiff'
    elif filename:
        return get_from_filename(filename, default)
    else:
        return default

def get_from_filename(filename, default=None):
    """Tries to determine the mime type from the given filename."""
    name, ext = os.path.splitext(os.path.basename(filename))
    return EXTENSION_MIME_TYPE_MAP.get(ext, default)

def get_extension(mimetype, default=None):
    """Returns the file extension for a given mime type."""
    return MIME_TYPE_EXTENSION_MAP.get(mimetype, default)