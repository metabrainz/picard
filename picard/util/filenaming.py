# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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
import struct
import sys
import unicodedata

from PyQt5.QtCore import QStandardPaths

from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.util import (
    _io_encoding,
    decode_filename,
    encode_filename,
)


def _get_utf16_length(text):
    """Returns the number of code points used by a unicode object in its
    UTF-16 representation.
    """
    if isinstance(text, bytes):
        return len(text)
    # if this is a narrow Python build, len will in fact return exactly
    # what we're looking for
    if sys.maxunicode == 0xFFFF:
        return len(text)
    # otherwise, encode the string in UTF-16 using the system's endianness,
    # and divide the resulting length by 2
    return len(text.encode("utf-16%ce" % sys.byteorder[0])) // 2


def _shorten_to_utf16_length(text, length):
    """Truncates a str object to the given number of UTF-16 code points.
    """
    assert isinstance(text, str), "This function only works on unicode"
    # if this is a narrow Python build, regular slicing will do exactly
    # what we're looking for
    if sys.maxunicode == 0xFFFF:
        shortened = text[:length]
        # before returning, we need to check if we didn't cut in the middle
        # of a surrogate pair
        last = shortened[-1:]
        if last and 0xD800 <= ord(last) <= 0xDBFF:
            # it's a leading surrogate alright
            return shortened[:-1]
        # else...
        return shortened
    # otherwise, encode the string in UTF-16 using the system's endianness,
    # and shorten by twice the length
    enc = "utf-16%ce" % sys.byteorder[0]
    shortened = text.encode(enc)[:length * 2]
    # if we hit a surrogate pair, get rid of the last codepoint
    last = shortened[-2:]
    if last and 0xD800 <= struct.unpack("=H", last)[0] <= 0xDBFF:
        shortened = shortened[:-2]
    return shortened.decode(enc)


def _shorten_to_utf16_nfd_length(text, length):
    text = unicodedata.normalize('NFD', text)
    newtext = _shorten_to_utf16_length(text, length)
    # if the first cut-off character was a combining one, remove our last
    try:
        if unicodedata.combining(text[len(newtext)]):
            newtext = newtext[:-1]
    except IndexError:
        pass
    return unicodedata.normalize('NFC', newtext)

_re_utf8 = re.compile(r'^utf([-_]?8)$', re.IGNORECASE)
def _shorten_to_bytes_length(text, length):
    """Truncates a unicode object to the given number of bytes it would take
    when encoded in the "filesystem encoding".
    """
    assert isinstance(text, str), "This function only works on unicode"
    raw = encode_filename(text)
    # maybe there's no need to truncate anything
    if len(raw) <= length:
        return text
    # or maybe there's nothing multi-byte here
    if len(raw) == len(text):
        return text[:length]
    # if we're dealing with utf-8, we can use an efficient algorithm
    # to deal with character boundaries
    if _re_utf8.match(_io_encoding):
        i = length
        # a UTF-8 intermediate byte starts with the bits 10xxxxxx,
        # so ord(char) & 0b11000000 = 0b10000000
        while i > 0 and (raw[i] & 0xC0) == 0x80:
            i -= 1
        return decode_filename(raw[:i])
    # finally, a brute force approach
    i = length
    while i > 0:
        try:
            return decode_filename(raw[:i])
        except UnicodeDecodeError:
            pass
        i -= 1
    # hmm. we got here?
    return ""


SHORTEN_BYTES, SHORTEN_UTF16, SHORTEN_UTF16_NFD = 0, 1, 2
def shorten_filename(filename, length, mode):
    """Truncates a filename to the given number of thingies,
    as implied by `mode`.
    """
    if isinstance(filename, bytes):
        return filename[:length]
    if mode == SHORTEN_BYTES:
        return _shorten_to_bytes_length(filename, length)
    if mode == SHORTEN_UTF16:
        return _shorten_to_utf16_length(filename, length)
    if mode == SHORTEN_UTF16_NFD:
        return _shorten_to_utf16_nfd_length(filename, length)


def shorten_path(path, length, mode):
    """Reduce path nodes' length to given limit(s).

    path: Absolute or relative path to shorten.
    length: Maximum number of code points / bytes allowed in a node.
    mode: One of SHORTEN_BYTES, SHORTEN_UTF16, SHORTEN_UTF16_NFD.
    """
    def shorten(n, l): return n and shorten_filename(n, l, mode).strip() or ""
    dirpath, filename = os.path.split(path)
    fileroot, ext = os.path.splitext(filename)
    return os.path.join(
        os.path.join(*[shorten(node, length)
                       for node in dirpath.split(os.path.sep)]),
        shorten(fileroot, length - len(ext)) + ext
    )


def _shorten_to_utf16_ratio(text, ratio):
    """Shortens the string to the given ratio (and strips it)."""
    length = _get_utf16_length(text)
    limit = max(1, int(math.floor(length / ratio)))
    if isinstance(text, bytes):
        return text[:limit].strip()
    else:
        return _shorten_to_utf16_length(text, limit).strip()


def _make_win_short_filename(relpath, reserved=0):
    r"""Shorten a relative file path according to WinAPI quirks.

    relpath: The file's path.
    reserved: Number of characters reserved for the parent path to be joined with,
              e.g. 3 if it will be joined with "X:\", respectively 5 for "X:\y\".
              (note the inclusion of the final backslash)
    """
    # See:
    # http://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx
    #
    # The MAX_PATH is 260 characters, with this possible format for a file:
    # "X:\<244-char dir path>\<11-char filename><NUL>".

    # Our constraints:
    # the entire path's length
    MAX_FILEPATH_LEN = 259
    # the entire parent directory path's length, *excluding* the final separator
    MAX_DIRPATH_LEN = 247
    # a single node's length (this seems to be the case for older NTFS)
    MAX_NODE_LEN = 226

    # to make predictable directory paths we need to fit the directories in
    # MAX_DIRPATH_LEN, and truncate the filename to whatever's left
    remaining = MAX_DIRPATH_LEN - reserved

    # to make things more readable...
    def shorten(p, l): return shorten_path(p, l, mode=SHORTEN_UTF16)
    xlength = _get_utf16_length

    # shorten to MAX_NODE_LEN from the beginning
    relpath = shorten(relpath, MAX_NODE_LEN)
    dirpath, filename = os.path.split(relpath)
    # what if dirpath is already the right size?
    dplen = xlength(dirpath)
    if dplen <= remaining:
        filename_max = MAX_FILEPATH_LEN - (reserved + dplen + 1)  # the final separator
        filename = shorten(filename, filename_max)
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
        # allocate space for the separators,
        # but don't include the final one
        remaining -= len(dirnames) - 1
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
        totalchars = sum(map(xlength, dirnames))
        shortdirchars = sum(map(xlength, shortdirnames))

        # do we have at least 1 char for longdirs?
        if remaining > shortdirchars + len(dirnames) - len(shortdirnames):
            ratio = float(totalchars - shortdirchars) / (remaining - shortdirchars)
            for i, dn in enumerate(dirnames):
                if len(dn) > average:
                    dirnames[i] = _shorten_to_utf16_ratio(dn, ratio)
        else:
            ratio = float(totalchars) / remaining
            dirnames = [_shorten_to_utf16_ratio(dn, ratio) for dn in dirnames]

        # here it is:
        finaldirpath = os.path.join(*dirnames)

        # did we win back some chars from .floor()s and .strip()s?
        recovered = remaining - sum(map(xlength, dirnames))
        # so how much do we have left for the filename?
        filename_max = MAX_FILEPATH_LEN - MAX_DIRPATH_LEN - 1 + recovered
        #                                                   ^ the final separator

        # and don't forget to cache
        computed[(dirpath, reserved)] = (finaldirpath, filename_max)

    # finally...
    filename = shorten(filename, filename_max)
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
        # XXX http://bugs.python.org/issue18695
        try:
            limit = os.statvfs(d).f_namemax
        except UnicodeEncodeError:
            limit = os.statvfs(d.encode(_io_encoding)).f_namemax
        limits[target] = limit
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
    try:
        basedir = os.path.abspath(basedir)
    except FileNotFoundError:
        # os.path.abspath raises an exception if basedir is a relative path and
        # cwd doesn't exist anymore
        basedir = QStandardPaths.writableLocation(QStandardPaths.MusicLocation)
    # also, make sure the relative path is clean
    relpath = os.path.normpath(relpath)
    if win_compat and relative_to:
        relative_to = os.path.abspath(relative_to)
        assert basedir.startswith(relative_to) and \
            basedir.split(relative_to)[1][:1] in (os.path.sep, ''), \
            "`relative_to` must be an ancestor of `basedir`"
    # always strip the relpath parts
    relpath = os.path.join(*[part.strip() for part in relpath.split(os.path.sep)])
    # if we're on windows, delegate the work to a windows-specific function
    if IS_WIN:
        reserved = len(basedir)
        if not basedir.endswith(os.path.sep):
            reserved += 1
        return _make_win_short_filename(relpath, reserved)
    # if we're being windows compatible, figure out how much
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
        reserved = len(basedir) - len(relative_to) + 3 + 1
        #                             the drive name ^ + ^ the final separator
        relpath = _make_win_short_filename(relpath, reserved)
    # on *nix we can consider there is no path limit, but there is
    # a filename length limit.
    if IS_MACOS:
        # on OS X (i.e. HFS+), this is expressed in UTF-16 code points,
        # in NFD normalization form
        relpath = shorten_path(relpath, 255, mode=SHORTEN_UTF16_NFD)
    else:
        # on everything else the limit is expressed in bytes,
        # and filesystem-dependent
        limit = _get_filename_limit(basedir)
        relpath = shorten_path(relpath, limit, mode=SHORTEN_BYTES)
    return relpath
