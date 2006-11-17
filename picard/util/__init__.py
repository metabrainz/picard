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


def needs_read_lock(func):
    """Adds a read lock around ``func``.
    
    This decorator should be used only on ``LockableObject`` methods."""
    def locked(self, *args, **kwargs):
        self.lock_for_read()
        try:
            return func(self, *args, **kwargs)
        finally:
            self.unlock()
    locked.__doc__ = func.__doc__
    locked.__name__ = func.__name__
    return locked


def needs_write_lock(func):
    """Adds a write lock around ``func``.
    
    This decorator should be used only on ``LockableObject`` methods."""
    def locked(self, *args, **kwargs):
        self.lock_for_write()
        try:
            return func(self, *args, **kwargs)
        finally:
            self.unlock()
    locked.__doc__ = func.__doc__
    locked.__name__ = func.__name__
    return locked


class LockableObject(QtCore.QObject):
    """Read/write lockable object."""

    def __init__(self):
        QtCore.QObject.__init__(self)
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


class LockableDict(dict):

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
        return filename.decode(_io_encoding)
        
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
def replace_win32_incompat(string, repl=u"_"):
    """Replace win32 filename incompatible characters from ``string`` by
       ``repl``."""
    return _re_win32_incompat.sub(repl, string)

_re_non_alphanum = re.compile(r'\W+', re.UNICODE)
def strip_non_alnum(string):
    """Remove all non-alphanumeric characters from ``string``."""
    return _re_non_alphanum.sub(u" ", string)

_re_slashes = re.compile(r'[\\/]', re.UNICODE)
def sanitize_filename(string, repl="_"):
    return _re_slashes.sub(repl, string)

def make_short_filename(prefix, filename, length=250, max_length=250,
                        mid_length=32, min_length=2):
    parts = _re_slashes.split(filename)
    parts.reverse()
    left = len(prefix) + len(filename) + 1 - length

    for i in range(len(parts)):
        left -= max(0, len(parts[i]) - max_length)
        parts[i] = parts[i][:max_length]

    if left > 0:
        for i in range(len(parts)):
            length = len(parts[i]) - mid_length
            if length > 0:
                length = min(left, length)
                parts[i] = parts[i][:-length]
                left -= length
                if left <= 0:
                    break

        if left > 0:
            for i in range(len(parts)):
                length = len(parts[i]) - min_length
                if length > 0:
                    length = min(left, length)
                    parts[i] = parts[i][:-length]
                    left -= length
                    if left <= 0:
                        break

            if left > 0:
                raise IOError, "File name is too long."

    parts.reverse()
    return os.path.join(*parts)
