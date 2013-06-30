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
from encodings import rot_13;
from string import Template
from functools import partial


def asciipunct(s):
    mapping = {
        u"…": u"...",
        u"‘": u"'",
        u"’": u"'",
        u"‚": u"'",
        u"“": u"\"",
        u"”": u"\"",
        u"„": u"\"",
        u"′": u"'",
        u"″": u"\"",
        u"‹": u"<",
        u"›": u">",
        u"‐": u"-",
        u"‒": u"-",
        u"–": u"-",
        u"−": u"-",
        u"—": u"-",
        u"―": u"--",
    }
    for orig, repl in mapping.iteritems():
        s = s.replace(orig, repl)
    return s


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

#The following was adapted from k3b's source code:
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

_re_win32_incompat = re.compile(r'["*:<>?|]', re.UNICODE)
def replace_win32_incompat(string, repl=u"_"):
    """Replace win32 filename incompatible characters from ``string`` by
       ``repl``."""
    return _re_win32_incompat.sub(repl, string)

_re_non_alphanum = re.compile(r'\W+', re.UNICODE)
def strip_non_alnum(string):
    """Remove all non-alphanumeric characters from ``string``."""
    return _re_non_alphanum.sub(u" ", string).strip()

_re_slashes = re.compile(r'[\\/]', re.UNICODE)
def sanitize_filename(string, repl="_"):
    return _re_slashes.sub(repl, string)

def make_short_filename(prefix, filename, max_path_length=240, max_length=200,
                        mid_length=32, min_length=2):
    """
    Attempts to shorten the file name to the maximum allowed length.

    max_path_length: The maximum length of the complete path.
    max_length: The maximum length of a single file or directory name.
    mid_length: The medium preferred length of a single file or directory.
    min_length: The minimum allowed length of a single file or directory.
    """
    parts = [part.strip() for part in _re_slashes.split(filename)]
    parts.reverse()
    filename = os.path.join(*parts)
    left = len(prefix) + len(filename) + 1 - max_path_length

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

    return os.path.join(*[a.strip() for a in reversed(parts)])


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


def call_next(func):
    def func_wrapper(self, *args, **kwargs):
        next = args[0]
        result = None
        try:
            result = func(self, *args, **kwargs)
        except:
            import traceback
            from picard import log
            log.error(traceback.format_exc())
            next(error=sys.exc_info()[1])
        else:
            next(result=result)
    func_wrapper.__name__ = func.__name__
    return func_wrapper


_mbid_format = Template('$h{8}-$h$l-$h$l-$h$l-$h{12}').safe_substitute(h='[0-9a-fA-F]', l='{4}')
_re_mbid_val = re.compile(_mbid_format)
def mbid_validate(string):
    return _re_mbid_val.match(string)


def rot13(input):
    return u''.join(unichr(rot_13.encoding_map.get(ord(c), ord(c))) for c in input)


def load_release_type_scores(setting):
    scores = {}
    values = setting.split()
    for i in range(0, len(values), 2):
        scores[values[i]] = float(values[i+1]) if i+1 < len(values) else 0.0
    return scores


def save_release_type_scores(scores):
    return " ".join(["%s %.2f" % v for v in scores.iteritems()])


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
        def later(*args, **kwargs):
            mutex.lock()
            func(*args, **kwargs)
            decorator.prev = time()
            decorator.is_ticking = False
            mutex.unlock()

        def throttled_func(*args, **kwargs):
            if decorator.is_ticking:
                return
            mutex.lock()
            now = time()
            r = interval - (now-decorator.prev)*1000.0
            if r <= 0:
                func(*args, **kwargs)
                decorator.prev = now
            else:
                QtCore.QTimer.singleShot(r, partial(later, *args, **kwargs))
                decorator.is_ticking = True
            mutex.unlock()

        return throttled_func

    decorator.prev = 0
    decorator.is_ticking = False
    return decorator
