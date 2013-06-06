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

import math
import os
import re
import sys
import unicodedata
from PyQt4 import QtCore
from encodings import rot_13;
from string import Template


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
        QtCore.QObject.log.warning("""
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


def shorten_filename(filename, length, byte_mode=False):
    """Shortens a filename to the specified length, and strips whitespace."""
    if not byte_mode:
        return filename[:length].strip()
    raw = encode_filename(filename)
    if len(raw) <= length:
        return filename
    i = length
    # a UTF-8 intermediate byte starts with the bits 10xxxxxx
    # courtesy of http://stackoverflow.com/a/13738452
    while i > 0 and (ord(raw[i]) & 0xC0) == 0x80:
        i -= 1
    return decode_filename(raw[:i]).strip()


def shorten_path(path, d_namemax, f_namemax=None, byte_mode=False):
    """Reduce path nodes' length to given limit(s).

    path: Absolute or relative path to shorten.
    d_namemax: Maximum number of characters allowed in a directory name.
    f_namemax: Maximum number of characters allowed in a file name.
    byte_mode: Operate on bytes instead of characters.
    """
    if f_namemax is None:
        f_namemax = d_namemax
    dirpath, filename = os.path.split(path)
    fileroot, ext = os.path.splitext(filename)
    return os.path.join(
        os.path.join(*(shorten_filename(node, d_namemax, byte_mode) \
                       for node in dirpath.split(os.path.sep))),
        shorten_filename(fileroot, f_namemax - len(encode_filename(ext)),
                         byte_mode) + ext
    )


def _shorten_to_ratio(lst, ratio):
    """Shortens list items to the given ratio (and strips them)."""
    return map(
        lambda item: item[:max(1, int(math.floor(len(item) / ratio)))].strip(),
        lst
    )


def make_win_short_filename(target, relpath, gain=0):
    """Shorten a filename according to WinAPI quirks."""
    # See:
    # http://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx
    #
    # The MAX_PATH is 260 characters, with this possible format for a file:
    # "X:\<244-char dir path>\<11-char filename><NUL>".
    # This means on Windows we'll need to generate a result of the form:
    # "<247-char dir path>, <11-char filename>".
    # If we're on *nix we'll reserve 3 chars for "X:\".

    # Our constraints:
    MAX_FILEPATH_LEN = 259
    MAX_DIRPATH_LEN = 247
    MAX_NODE_LEN = 226 # This seems to be the case for older NTFS

    if sys.platform == "win32":
        reserved = len(target) + 1 # ending slash
    else:
        reserved = len(target) - gain + 3 # "X:\"

    remaining = MAX_DIRPATH_LEN - reserved
    relpath = shorten_path(relpath, MAX_NODE_LEN)
    if remaining >= len(relpath):
        # we're home free
        return os.path.join(target, relpath)

    # compute the directory path and the maximum number of characters
    # in a filename, and cache them
    dirpath, filename = os.path.split(relpath)
    try:
        computed = make_win_short_filename._computed
    except AttributeError:
        computed = make_win_short_filename._computed = {}
    try:
        fulldirpath, filename_max = computed[(target, dirpath, gain)]
    except KeyError:
        dirnames = dirpath.split(os.path.sep)
        # allocate space for the separators
        remaining -= len(dirnames) # this includes the final separator
        # make sure we can have at least single-character dirnames
        average = float(remaining) / len(dirnames)
        if average < 1:
            # TODO: a nice exception
            raise IOError("Path too long. You need to move renamed files \
                       to a different directory.")

        # the gist of it: reduce directories exceeding average with a ratio
        # proportional to how much they exceed with; if not possible, reduce all
        # dirs proportionally to their initial length
        shortdirnames = [dn for dn in dirnames if len(dn) <= average]
        totalchars = sum(map(len, dirnames))
        shortdirchars = sum(map(len, shortdirnames))

        # do we have at least 1 char for longdirs?
        if remaining > shortdirchars + len(dirnames) - len(shortdirnames):
            # we'll need to split the long dirs away and remember their index:
            longdirs, indices = [], []
            for i, dn in enumerate(dirnames):
                if len(dn) > average:
                    # store the index (we can't pop while enumerating)
                    indices.append(i)
            # and now pop them
            for i in reversed(indices):
                longdirs.append(dirnames.pop(i))
            longdirs.reverse()
            # shorten them
            longdirs = _shorten_to_ratio(longdirs, float(totalchars - shortdirchars) / (remaining - shortdirchars))
            # and merge them back
            while indices:
                dirnames.insert(indices.pop(0), longdirs.pop(0))
        else:
            dirnames = _shorten_to_ratio(dirnames, float(totalchars) / remaining)

        # here it is:
        fulldirpath = os.path.join(target, *dirnames)

        # did we win back some chars from .floor()s and .strip()s?
        recovered = remaining - sum(map(len, dirnames))
        # so how much do we have left for the filename?
        filename_max = MAX_FILEPATH_LEN - MAX_DIRPATH_LEN - 1 + recovered
        #                                                   ^ the ending separator

        # and don't forget to cache
        computed[(target, dirpath, gain)] = (fulldirpath, filename_max)

    # finally...
    fileroot, ext = os.path.splitext(filename)
    filename = fileroot[:filename_max - len(ext)].strip() + ext

    return os.path.join(fulldirpath, filename)


def make_short_filename(target, relpath, win_compat=False, relative_to=""):
    """Shorten a filename's path to proper limits.

    target: Absolute path of the base directory where files will be moved.
    relpath: File path, relative from the base directory.
    win_compat: Windows is quirky.
    relative_to: An ancestor directory of target, against which win_compat
                 will be applied.
    """
    target = os.path.abspath(target)
    if win_compat and relative_to:
        relative_to = os.path.abspath(relative_to)
        assert target.startswith(relative_to) and \
               target.split(relative_to)[1][:1] in (os.path.sep, ''), \
               "`relative_to` must be an ancestor of `target`"
    # if we're on windows, fire away
    if sys.platform == "win32":
        return make_win_short_filename(target, relpath)
    # if we're being compatible, we can gain some characters
    if win_compat:
        if target and not relative_to:
            # try to find out the parent mount point,
            # caching it for future lookups
            try:
                mounts = make_short_filename._mounts
            except AttributeError:
                mounts = make_short_filename._mounts = {}
            try:
                relative_to = mounts[target]
            except KeyError:
                relative_to = target
                while relative_to and not os.path.ismount(relative_to):
                    relative_to = os.path.dirname(relative_to)
                # did we hit root?
                if relative_to == os.path.sep:
                    # then presume the parent will be copied over to windows,
                    # and hope for the best
                    relative_to = os.path.dirname(target)
                # cache it
                mounts[target] = relative_to
        gain = len(target) - len(relative_to)
        return make_win_short_filename(target, relpath, gain=gain)
    # on regular *nix, find the name length limit (or at most 255 bytes),
    # and cache it
    try:
        limits = make_short_filename._limits
    except AttributeError:
        limits = make_short_filename._limits = {}
    try:
        limit = limits[target]
    except KeyError:
        # we need to call statvfs on an existing target
        d = target
        while not os.path.exists(d):
            d = os.path.dirname(d)
        limit = limits[target] = min(os.statvfs(d).f_namemax, 255)
    return os.path.join(target, shorten_path(relpath, limit, byte_mode=True))


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


try:
    from functools import partial
except ImportError:
    def partial(func, *args, **keywords):
        def newfunc(*fargs, **fkeywords):
            newkeywords = keywords.copy()
            newkeywords.update(fkeywords)
            return func(*(args + fargs), **newkeywords)
        newfunc.func = func
        newfunc.args = args
        newfunc.keywords = keywords
        return newfunc


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
            self.log.error(traceback.format_exc())
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
