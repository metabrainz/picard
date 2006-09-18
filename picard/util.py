# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
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

import os.path
import re
import sys
import unicodedata
from PyQt4 import QtCore

class LockableObject(QtCore.QObject):
    """Read/write lockable object."""

    def __init__(self):
        self.__lock = QtCore.QReadWriteLock()

    def lock_for_read(self):
        """Lock the object for read operations."""
        self.__lock.lockForRead()

    def lock_for_write(self):
        """Lock the object for write operations."""
        self.__lock.lockForWrite()

    def unlock(self):
        """Unlock the object."""
        self.__lock.unlock()


_io_encoding = sys.getfilesystemencoding() 

def set_io_encoding(encoding):
    """Sets the encoding used in file names."""
    _io_encoding = encoding

def encode_filename(filename):
    """Encode unicode strings to filesystem encoding."""
    if isinstance(filename, unicode):
        if os.path.supports_unicode_filenames:
            return filename
        else:
            return filename.encode(_io_encoding, 'replace')
    else:
        return filename

def decode_filename(filename):
    """Decode strings from filesystem encoding to unicode."""
    if isinstance(filename, unicode):
        return filename
    else:
        return filename.decode(_ioEncoding)
        
def format_time(ms):
    """Formats time in milliseconds to a string representation."""
    if ms == 0:
        return "?:??"
    else:
        return "%d:%02d" % (ms / 60000, (ms / 1000) % 60)

def sanitize_date(datestr):
    """Sanitize date format.
    
    e.g.: "YYYY-00-00" -> "YYYY"
          "YYYY-  -  " -> "YYYY"
          ...
    """
    date = []
    for num in datestr.split("-"):
        try:
            num = int(num.strip())
        except ValueError:
            break
        date.append(num)
    return ("", "%04d", "%04d-%02d", "%04d-%02d-%02d")[len(date)] % tuple(date)

_re_latin_letter = re.compile(r"^(LATIN [A-Z]+ LETTER [A-Z]+) WITH")
def unaccent(string):
    """Remove accents ``string``."""
    result = []
    for char in string:
        name = unicodedata.name(char)
        match = _re_latin_letter.search(name)
        if match:
            char = unicodedata.lookup(match.group(1))
        result.append(char)
    return "".join(result)

_re_non_ascii = re.compile(r'[^\x00-\x7F]', re.UNICODE)
def replace_non_ascii(string, repl="_"):
    """Replace non-ASCII characters from ``string`` by ``repl``."""
    return _re_non_ascii.sub(repl, string)

_re_win32_incompat = re.compile(r'[\\"*/:<>?|]', re.UNICODE)
def replace_win32_incompat(string, repl="_"):
    """Replace win32 filename incompatible characters from ``string`` by
       ``repl``."""
    return _re_win32_incompat.sub(repl, string)

