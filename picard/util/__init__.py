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

import os
import re
import sys
import unicodedata
from time import time
from PyQt4 import QtCore
from encodings import rot_13
from string import Template
# Required for compatibility with lastfmplus which imports this from here rather than loading it direct.
from functools import partial
from collections import defaultdict


class LockableDefaultDict(defaultdict):

    def __init__(self, default):
        defaultdict.__init__(self, default)
        self.__lock = QtCore.QReadWriteLock()

    def lock(self):
        self.__lock.lockForWrite()

    def unlock(self):
        self.__lock.unlock()


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


_io_encoding = sys.getfilesystemencoding()


# The following was adapted from k3b's source code:
#// On a glibc system the system locale defaults to ANSI_X3.4-1968
#// It is very unlikely that one would set the locale to ANSI_X3.4-1968
#// intentionally
def check_io_encoding():
    if _io_encoding == "ANSI_X3.4-1968":
        from picard import log
        log.warning("""
System locale charset is ANSI_X3.4-1968
Your system's locale charset (i.e. the charset used to encode filenames)
is set to ANSI_X3.4-1968. It is highly unlikely that this has been done
intentionally. Most likely the locale is not set at all. An invalid setting
will result in problems when creating data projects.
To properly set the locale charset make sure the LC_* environment variables
are set. Normally the distribution setup tools take care of this.

Translation: Picard will have problems with non-english characters
               in filenames until you change your charset.
""")


def encode_filename(filename):
    """Encode unicode strings to filesystem encoding."""
    if isinstance(filename, unicode):
        if os.path.supports_unicode_filenames and sys.platform != "darwin":
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


def pathcmp(a, b):
    return os.path.normcase(a) == os.path.normcase(b)


def format_time(ms):
    """Formats time in milliseconds to a string representation."""
    ms = float(ms)
    if ms == 0:
        return "?:??"
    else:
        return "%d:%02d" % (round(ms / 1000.0) / 60, round(ms / 1000.0) % 60)


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
        if num:
            date.append(num)
    return ("", "%04d", "%04d-%02d", "%04d-%02d-%02d")[len(date)] % tuple(date)


_unaccent_dict = {u'Æ': u'AE', u'æ': u'ae', u'Œ': u'OE', u'œ': u'oe', u'ß': 'ss'}
_re_latin_letter = re.compile(r"^(LATIN [A-Z]+ LETTER [A-Z]+) WITH")
def unaccent(string):
    """Remove accents ``string``."""
    result = []
    for char in string:
        if char in _unaccent_dict:
            char = _unaccent_dict[char]
        else:
            try:
                name = unicodedata.name(char)
                match = _re_latin_letter.search(name)
                if match:
                    char = unicodedata.lookup(match.group(1))
            except:
                pass
        result.append(char)
    return "".join(result)


_re_non_ascii = re.compile(r'[^\x00-\x7F]', re.UNICODE)
def replace_non_ascii(string, repl="_"):
    """Replace non-ASCII characters from ``string`` by ``repl``."""
    return _re_non_ascii.sub(repl, asciipunct(string))


# dict has re search term (escaped re characters) as key, and normal string as value.
_win32_incompat2ascii = [
    (r'"', r"'"),
    (r"\*", r"_"),
    (r": ", r" - "),
    (r":", r"-"),
    (r"<", r"{"),
    (r">", r"}"),
    (r"\?", r"_"),
    (r"\|", r"_"),
    (r"\.\/", r"/"),
    (r"\.\\", r"\\"),
    ]
_win32_incompat2unicode = [
    (u'"', u"\u2033"), # Double-Prime
    (u"\\*", u"_"),
    (u":", u"\uFE13"), # Vertical colon
    (u"<", u"\u226A"), # Much Less-Than
    (u">", u"\u226B"), # Much Greater-Than
    (u"\\?", u"\uFE16"), # Vertical Question Mark
    (u"\\|", u"\u2223"), # Divides
    (u"\\.\\/", u"\u2215"), # Division Slash
    (u"\\.\\\\", u"\u2216"), # Set Minus
    ]

# For ascii where we have multi-char substitution, ensure supersets precede subsets
_win32_incompat2ascii.sort(key=lambda x: x[0], reverse=True)

# When we need to look up replacement character, key has been unescaped - so need to do a double lookup
_re_dict_unescape = re.compile(r"\\.")
_win32_ascii_dict = {}
for i in xrange(0, len(_win32_incompat2ascii)):
    _win32_ascii_dict[_re_dict_unescape.sub(lambda m: m.group(0)[1:], _win32_incompat2ascii[i][0])] = i
_win32_unicode_dict = {}
for i in xrange(0, len(_win32_incompat2unicode)):
    _win32_unicode_dict[_re_dict_unescape.sub(lambda m: m.group(0)[1:], _win32_incompat2unicode[i][0])] = i

_re_win32_incompat_ascii = re.compile('(' + ')|('.join([x[0] for x in _win32_incompat2ascii]) + ')')
_re_win32_incompat_unicode = re.compile('(' + ')|('.join([x[0] for x in _win32_incompat2unicode]) + ')')

def replace_win32_incompat(string, to_ascii=True):
    """Replace win32 filename incompatible characters from ``string`` by
       ``repl``."""
    if to_ascii:
        result = _re_win32_incompat_ascii.sub(lambda m: _win32_incompat2ascii[_win32_ascii_dict[m.group(0)]][1], string)
    else:
        result = _re_win32_incompat_unicode.sub(lambda m: _win32_incompat2unicode[_win32_unicode_dict[m.group(0)]][1], string)
    return result


_re_non_alphanum = re.compile(r'\W+', re.UNICODE)
def strip_non_alnum(string):
    """Remove all non-alphanumeric characters from ``string``."""
    return _re_non_alphanum.sub(u" ", string).strip()


_re_slashes = re.compile(r'[\\/]', re.UNICODE)
def sanitize_filename(string, repl="-"):
    return _re_slashes.sub(repl, string)


def _reverse_sortname(sortname):
    """Reverse sortnames."""
    chunks = [a.strip() for a in sortname.split(",")]
    if len(chunks) == 2:
        return "%s %s" % (chunks[1], chunks[0])
    elif len(chunks) == 3:
        return "%s %s %s" % (chunks[2], chunks[1], chunks[0])
    elif len(chunks) == 4:
        return "%s %s, %s %s" % (chunks[1], chunks[0], chunks[3], chunks[2])
    else:
        return sortname.strip()


def translate_from_sortname(name, sortname):
    """'Translate' the artist name by reversing the sortname."""
    for c in name:
        ctg = unicodedata.category(c)
        if ctg[0] == "L" and unicodedata.name(c).find("LATIN") == -1:
            for separator in (" & ", "; ", " and ", " vs. ", " with ", " y "):
                if separator in sortname:
                    parts = sortname.split(separator)
                    break
            else:
                parts = [sortname]
                separator = ""
            return separator.join(map(_reverse_sortname, parts))
    return name


def find_existing_path(path):
    path = encode_filename(path)
    while path and not os.path.isdir(path):
        head, tail = os.path.split(path)
        if head == path:
            break
        path = head
    return decode_filename(path)


def find_executable(*executables):
    if sys.platform == 'win32':
        executables = [e + '.exe' for e in executables]
    paths = [os.path.dirname(sys.executable)] if sys.executable else []
    paths += os.environ.get('PATH', '').split(os.pathsep)
    for path in paths:
        for executable in executables:
            f = os.path.join(path, executable)
            if os.path.isfile(f):
                return f


_mbid_format = Template('$h{8}-$h$l-$h$l-$h$l-$h{12}').safe_substitute(h='[0-9a-fA-F]', l='{4}')
_re_mbid_val = re.compile(_mbid_format)
def mbid_validate(string):
    return _re_mbid_val.match(string)


def rot13(input):
    return u''.join(unichr(rot_13.encoding_map.get(ord(c), ord(c))) for c in input)


def parse_amazon_url(url):
    """Extract host and asin from an amazon url.
    It returns a dict with host and asin keys on success, None else
    """
    r = re.compile(r'^http://(?:www.)?(?P<host>.*?)(?:\:[0-9]+)?/.*/(?P<asin>[0-9B][0-9A-Z]{9})(?:[^0-9A-Z]|$)')
    match = r.match(url)
    if match is not None:
        return match.groupdict()
    return None


def throttle(interval):
    """
    Throttle a function so that it will only execute once per ``interval``
    (specified in milliseconds).
    """
    mutex = QtCore.QMutex()

    def decorator(func):
        def later():
            mutex.lock()
            func(*decorator.args, **decorator.kwargs)
            decorator.prev = time()
            decorator.is_ticking = False
            mutex.unlock()

        def throttled_func(*args, **kwargs):
            if decorator.is_ticking:
                mutex.lock()
                decorator.args = args
                decorator.kwargs = kwargs
                mutex.unlock()
                return
            mutex.lock()
            now = time()
            r = interval - (now-decorator.prev)*1000.0
            if r <= 0:
                func(*args, **kwargs)
                decorator.prev = now
            else:
                decorator.args = args
                decorator.kwargs = kwargs
                QtCore.QTimer.singleShot(r, later)
                decorator.is_ticking = True
            mutex.unlock()

        return throttled_func

    decorator.prev = 0
    decorator.is_ticking = False
    return decorator


def uniqify(seq):
    """Uniqify a list, preserving order"""
    # Courtesy of Dave Kirby
    # See http://www.peterbe.com/plog/uniqifiers-benchmark
    seen = set()
    add_seen = seen.add
    return [x for x in seq if x not in seen and not add_seen(x)]


# order is important
_tracknum_regexps = (
    # search for explicit track number (prefix "track")
    r"track[\s_-]*(?:no|nr)?[\s_-]*(\d+)",
    # search for 2-digit number at start of string
    r"^(\d{2})\D?",
    # search for 2-digit number at end of string
    r"\D?(\d{2})$",
)


def tracknum_from_filename(base_filename):
    """Guess and extract track number from filename
    Returns -1 if none found, the number as integer else
    """
    filename, _ = os.path.splitext(base_filename)
    for r in _tracknum_regexps:
        match = re.search(r, filename, re.I)
        if match:
            n = int(match.group(1))
            if n > 0:
                return n
    # find all numbers between 1 and 99
    # 4-digit or more numbers are very unlikely to be a track number
    # smaller number is prefered in any case
    numbers = sorted([int(n) for n in re.findall(r'\d+', filename) if
                      int(n) <= 99 and int(n) > 0])
    if numbers:
        return numbers[0]
    return -1

# Provide os.path.samefile equivalent which is missing in Python under Windows
if sys.platform == 'win32':
    def os_path_samefile(p1, p2):
        ap1 = os.path.abspath(p1)
        ap2 = os.path.abspath(p2)
        return ap1 == ap2
else:
    os_path_samefile = os.path.samefile


def is_hidden_path(path):
    """Returns true if at least one element of the path starts with a dot"""
    path = os.path.normpath(path)  # we need to ignore /./ and /a/../ cases
    return any(s.startswith('.') for s in path.split(os.sep))
