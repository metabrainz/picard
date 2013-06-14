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


_re_utf8 = re.compile(r'^utf([-_]?8)$', re.IGNORECASE)
#_re_utf16 = re.compile(r'^utf[-_]?16([-_]?(b|l)e)?$', re.IGNORECASE)
def shorten_filename(filename, length):
    """Truncates a filename to the given number of either bytes or characters,
    depending on the system operating on.
    If operating on bytes, it takes into account character boundaries for the
    current encoding.
    """
    # NOTE: this is in fact a function of operating system and filesystem,
    # so this approach is simplistic

    # modern windows operates with unicode
    if os.path.supports_unicode_filenames:
        if sys.platform != "darwin":
            return filename[:length]
        else:
            # TODO: HFS+ needs special handling, as it can in fact
            # store 255 UTF-16 code units
            pass
    raw = encode_filename(filename)
    # maybe there's no need to truncate anything
    if len(raw) <= length:
        return filename
    # or maybe there's nothing multi-byte here
    if len(raw) == len(filename):
        return filename[:length]
    # are we dealing with utf-8? because that can use an efficient algorithm
    if _re_utf8.match(_io_encoding): 
        i = length
        # a UTF-8 intermediate byte starts with the bits 10xxxxxx
        while i > 0 and (ord(raw[i]) & 0xC0) == 0x80:
            i -= 1
        return decode_filename(raw[:i])
    # TODO: if the BOM doesn't get stored in file names, uncomment below
    ## if using utf-16, ignore the BOM
    #if _re_utf16.match(_io_encoding) and raw[:2] in ("\xff\xfe", "\xfe\xff"):
    #    length += 2
    # finally, a brute force approach
    i = length
    while i > 0:
        try:
            return decode_filename(raw[:i])
        except UnicodeDecodeError:
            pass
        i -= 1
    # hmm. we got here?
    return u""


def shorten_path(path, length, char_mode=False):
    """Reduce path nodes' length to given limit(s).

    path: Absolute or relative path to shorten.
    length: Maximum number of characters / bytes allowed in a node.
    char_mode: Force operating on characters instead of auto-deciding.
    """
    if char_mode:
        shorten = lambda n, l: n[:l].strip()
    else:
        shorten = lambda n, l: shorten_filename(n, l).strip()
    dirpath, filename = os.path.split(path)
    fileroot, ext = os.path.splitext(filename)
    return os.path.join(
        os.path.join(*[shorten(node, length) \
                       for node in dirpath.split(os.path.sep)]),
        shorten(fileroot, length - len(ext)) + ext
    )


def _shorten_to_ratio(text, ratio):
    """Shortens the string to the given ratio (and strips it)."""
    return text[:max(1, int(math.floor(len(text) / ratio)))].strip()


def _make_win_short_filename(relpath, reserved=0):
    """Shorten a relative file path according to WinAPI quirks.

    relpath: The file's path.
    reserved: Number of characters which will be reserved.
    """
    # See:
    # http://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx
    #
    # The MAX_PATH is 260 characters, with this possible format for a file:
    # "X:\<244-char dir path>\<11-char filename><NUL>".

    # Our constraints:
    MAX_FILEPATH_LEN = 259
    MAX_DIRPATH_LEN = 247
    MAX_NODE_LEN = 226 # This seems to be the case for older NTFS

    # to make predictable directory paths we need to fit the directories in
    # MAX_DIRPATH_LEN, and truncate the filename to whatever's left
    remaining = MAX_DIRPATH_LEN - reserved

    # shorten to MAX_NODE_LEN from the beginning
    relpath = shorten_path(relpath, MAX_NODE_LEN, char_mode=True)
    dirpath, filename = os.path.split(relpath)
    # what if dirpath is already the right size?
    if len(dirpath) <= remaining:
        filename_max = MAX_FILEPATH_LEN - len(dirpath) - 1 # the final separator
        filename = shorten_path(filename, filename_max, char_mode=True)
        return os.path.join(dirpath, filename)

    # compute the directory path and the maximum number of characters
    # in a filename, and cache them
    try:
        computed = _make_win_short_filename._computed
    except AttributeError:
        computed = _make_win_short_filename._computed = {}
    try:
        finaldirpath, filename_max = computed[(dirpath, reserved)]
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

        # try to reduce directories exceeding average with a ratio proportional
        # to how much they exceed with; if not possible, reduce all dirs
        # proportionally to their initial length
        shortdirnames = [dn for dn in dirnames if len(dn) <= average]
        totalchars = sum(map(len, dirnames))
        shortdirchars = sum(map(len, shortdirnames))

        # do we have at least 1 char for longdirs?
        if remaining > shortdirchars + len(dirnames) - len(shortdirnames):
            ratio = float(totalchars - shortdirchars) / (remaining - shortdirchars)
            for i, dn in enumerate(dirnames):
                if len(dn) > average:
                    dirnames[i] = _shorten_to_ratio(dn, ratio)
        else:
            ratio = float(totalchars) / remaining
            dirnames = [_shorten_to_ratio(dn, ratio) for dn in dirnames]

        # here it is:
        finaldirpath = os.path.join(*dirnames)

        # did we win back some chars from .floor()s and .strip()s?
        recovered = remaining - sum(map(len, dirnames))
        # so how much do we have left for the filename?
        filename_max = MAX_FILEPATH_LEN - MAX_DIRPATH_LEN - 1 + recovered
        #                                                   ^ the final separator

        # and don't forget to cache
        computed[(dirpath, reserved)] = (finaldirpath, filename_max)

    # finally...
    filename = shorten_path(filename, filename_max, char_mode=True)
    return os.path.join(finaldirpath, filename)


def _get_mount_point(target):
    """Finds the target's mountpoint."""
    # and caches it for future lookups
    try:
        mounts = _get_mount_point._mounts
    except AttributeError:
        mounts = _get_mount_point._mounts = {}
    try:
        mount = mounts[target]
    except KeyError:
        mount = target
        while mount and not os.path.ismount(mount):
            mount = os.path.dirname(mount)
        mounts[target] = mount
    return mount

# NOTE: this could be merged with the function above, and get all needed info
# in a single call, returning the filesystem type as well. (but python's
# posix.statvfs_result doesn't implement f_fsid)
def _get_filename_limit(target):
    """Finds the maximum filename length under the given directory."""
    # and caches it
    try:
        limits = _get_filename_limit._limits
    except AttributeError:
        limits = _get_filename_limit._limits = {}
    try:
        limit = limits[target]
    except KeyError:
        # we need to call statvfs on an existing target
        d = target
        while not os.path.exists(d):
            d = os.path.dirname(d)
        limit = limits[target] = os.statvfs(d).f_namemax
    return limit


def make_short_filename(basedir, relpath, win_compat=False, relative_to=""):
    """Shorten a filename's path to proper limits.

    basedir: Absolute path of the base directory where files will be moved.
    relpath: File path, relative from the base directory.
    win_compat: Windows is quirky.
    relative_to: An ancestor directory of basedir, against which win_compat
                 will be applied.
    """
    # only deal with absolute paths. it saves a lot of grief,
    # and is the right thing to do, even for renames.
    basedir = os.path.abspath(basedir)
    if win_compat and relative_to:
        relative_to = os.path.abspath(relative_to)
        assert basedir.startswith(relative_to) and \
               basedir.split(relative_to)[1][:1] in (os.path.sep, ''), \
               "`relative_to` must be an ancestor of `basedir`"
    # always strip the relpath parts
    relpath = os.path.join(*[part.strip() for part in relpath.split(os.path.sep)])
    # if we're on windows, delegate the work to a windows-specific function
    if sys.platform == "win32":
        reserved = len(basedir)
        if not basedir.endswith(os.path.sep):
            reserved += 1
        return os.path.join(basedir, _make_win_short_filename(relpath, reserved))
    # if we're being compatible, figure out how much
    # needs to be reserved for the basedir part
    if win_compat:
        # if a relative ancestor wasn't provided,
        # use the basedir's mount point
        if not relative_to:
            relative_to = _get_mount_point(basedir)
            # if it's root, presume the parent will be copied over
            # to windows, and hope for the best
            if relative_to == os.path.sep:
                relative_to = os.path.dirname(basedir)
        reserved = len(basedir) - len(relative_to) + 3 # for the drive name
        relpath = _make_win_short_filename(relpath, reserved)
    # on *nix we can consider there is no path limit, but there is a
    # filename length limit which is expressed in bytes
    limit = _get_filename_limit(basedir)
    return os.path.join(basedir, shorten_path(relpath, limit))


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
