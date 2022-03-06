# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013-2014 Ionuț Ciocîrlan
# Copyright (C) 2013-2014, 2018-2021 Laurent Monin
# Copyright (C) 2014 Michael Wiencek
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017 Ville Skyttä
# Copyright (C) 2018 Antonio Larrosa
# Copyright (C) 2019-2022 Philipp Wolfer
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

from enum import IntEnum
import math
import os
import re
import shutil
import struct
import sys
import unicodedata

from PyQt5.QtCore import QStandardPaths

from picard import log
from picard.const.sys import (
    IS_LINUX,
    IS_MACOS,
    IS_WIN,
)
from picard.util import (
    WIN_MAX_DIRPATH_LEN,
    WIN_MAX_FILEPATH_LEN,
    WIN_MAX_NODE_LEN,
    _io_encoding,
    decode_filename,
    encode_filename,
    samefile,
)


win32api = None
if IS_WIN:
    import winreg
    try:
        import win32api  # isort:skip
        import pywintypes
    except ImportError as e:
        log.warning('pywin32 not available: %s', e)


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
def _shorten_to_bytes_length(text, length):  # noqa: E302
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


def system_supports_long_paths():
    if not IS_WIN:
        return True
    else:
        try:
            # Use cached value
            return system_supports_long_paths._supported
        except AttributeError:
            pass
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
                system_supports_long_paths._supported = winreg.QueryValueEx(key, "LongPathsEnabled")[0] == 1
                return system_supports_long_paths._supported
        except OSError:
            log.info('Failed reading LongPathsEnabled from registry')
            return False


class ShortenMode(IntEnum):
    BYTES = 0
    UTF16 = 1
    UTF16_NFD = 2


def shorten_filename(filename, length, mode):  # noqa: E302
    """Truncates a filename to the given number of thingies,
    as implied by `mode`.
    """
    if isinstance(filename, bytes):
        return filename[:length]
    if mode == ShortenMode.BYTES:
        return _shorten_to_bytes_length(filename, length)
    if mode == ShortenMode.UTF16:
        return _shorten_to_utf16_length(filename, length)
    if mode == ShortenMode.UTF16_NFD:
        return _shorten_to_utf16_nfd_length(filename, length)


def shorten_path(path, length, mode):
    """Reduce path nodes' length to given limit(s).

    path: Absolute or relative path to shorten.
    length: Maximum number of code points / bytes allowed in a node.
    mode: One of the enum values from ShortenMode.
    """
    def shorten(name, length):
        return name and shorten_filename(name, length, mode).strip() or ""
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


class WinPathTooLong(OSError):
    pass


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

    # to make predictable directory paths we need to fit the directories in
    # WIN_MAX_DIRPATH_LEN, and truncate the filename to whatever's left
    remaining = WIN_MAX_DIRPATH_LEN - reserved

    # to make things more readable...
    def shorten(path, length):
        return shorten_path(path, length, mode=ShortenMode.UTF16)
    xlength = _get_utf16_length

    # shorten to WIN_MAX_NODE_LEN from the beginning
    relpath = shorten(relpath, WIN_MAX_NODE_LEN)
    dirpath, filename = os.path.split(relpath)
    # what if dirpath is already the right size?
    dplen = xlength(dirpath)
    if dplen <= remaining:
        filename_max = WIN_MAX_FILEPATH_LEN - (reserved + dplen + 1)  # the final separator
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
            raise WinPathTooLong(
                "Path too long. "
                "You need to move renamed files to a different directory."
            )

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
        filename_max = WIN_MAX_FILEPATH_LEN - WIN_MAX_DIRPATH_LEN - 1 + recovered
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


def make_short_filename(basedir, relpath, win_shorten_path=False, relative_to=""):
    """Shorten a filename's path to proper limits.

    basedir: Absolute path of the base directory where files will be moved.
    relpath: File path, relative from the base directory.
    win_shorten_path: Enforce 259 character limit for the path for Windows compatibility.
    relative_to: An ancestor directory of basedir, against which win_shorten_path
                 will be applied.
    """
    # only deal with absolute paths. it saves a lot of grief,
    # and is the right thing to do, even for renames.
    try:
        basedir = os.path.abspath(basedir)
    except FileNotFoundError:
        # os.path.abspath raises an exception if basedir is a relative path and
        # cwd doesn't exist anymore
        basedir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MusicLocation)
    # also, make sure the relative path is clean
    relpath = os.path.normpath(relpath)
    if win_shorten_path and relative_to:
        relative_to = os.path.abspath(relative_to)
        assert basedir.startswith(relative_to) and \
            basedir.split(relative_to)[1][:1] in (os.path.sep, ''), \
            "`relative_to` must be an ancestor of `basedir`"
    # always strip the relpath parts
    relpath = os.path.join(*[part.strip() for part in relpath.split(os.path.sep)])
    # if we're on windows, delegate the work to a windows-specific function
    if IS_WIN:
        if win_shorten_path:
            reserved = len(basedir)
            if not basedir.endswith(os.path.sep):
                reserved += 1
            return _make_win_short_filename(relpath, reserved)
        else:
            return shorten_path(relpath, 255, mode=ShortenMode.UTF16)
    # if we're being windows compatible, figure out how much
    # needs to be reserved for the basedir part
    elif win_shorten_path:
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
        relpath = shorten_path(relpath, 255, mode=ShortenMode.UTF16_NFD)
    else:
        # on everything else the limit is expressed in bytes,
        # and filesystem-dependent
        limit = _get_filename_limit(basedir)
        relpath = shorten_path(relpath, limit, mode=ShortenMode.BYTES)
    return relpath


def samefile_different_casing(path1, path2):
    """Returns True if path1 and path2 refer to the same file, but differ in casing of the filename.
    Returns False if path1 and path2 refer to different files or there case is identical.
    """
    path1 = os.path.normpath(path1)
    path2 = os.path.normpath(path2)
    if path1 == path2 or not os.path.exists(path1) or not os.path.exists(path2):
        return False
    dir1 = os.path.normcase(os.path.dirname(path1))
    dir2 = os.path.normcase(os.path.dirname(path2))
    try:
        dir1 = os.path.realpath(dir1)
        dir2 = os.path.realpath(dir2)
    except OSError:
        # os.path.realpath can fail if cwd does not exist and path is relative
        # or on Windows if drives are mounted without mount manager.
        pass
    if dir1 != dir2 or not samefile(path1, path2):
        return False
    file1 = os.path.basename(path1)
    file2 = os.path.basename(path2)
    return file1 != file2 and file1.lower() == file2.lower()


def _make_unique_temp_name(target_path):
    i = 0
    target_dir = os.path.dirname(target_path)
    target_filename = os.path.basename(target_path)
    while True:
        # Attempt to get a non-existant temporary name for the file
        # without changing path length.
        temp_filename = '.%s%02d' % (target_filename[:-3], i)
        temp_path = os.path.join(target_dir, temp_filename)
        if not os.path.exists(temp_path):
            return temp_path
        i += 1


def _move_force_rename(source_path, target_path):
    """Moves a file by renaming it first to a temporary name.
    Ensure file casing changes on system's not natively supporting this.
    """
    temp_path = _make_unique_temp_name(target_path)
    shutil.move(source_path, temp_path)
    os.rename(temp_path, target_path)


def move_ensure_casing(source_path, target_path):
    """Moves a file from source_path to target_path.
    If the move would result just in the name changing the case apply workarounds
    for Linux and Windows to ensure the case change is applied on case-insensitive
    file systems. Otherwise use shutil.move to move the file.
    """
    source_path = os.path.normpath(source_path)
    target_path = os.path.normpath(target_path)
    if source_path == target_path:
        return
    # Special handling is only required if both paths refer to the same file
    # but the file name differs in casing.
    # Also macOS does allow renaming only the casing and does not need special
    # handling.
    if not IS_MACOS and samefile_different_casing(source_path, target_path):
        if IS_LINUX:
            # On Linux always force a double move
            _move_force_rename(source_path, target_path)
            return
        elif IS_WIN and win32api:
            # Windows supports case renaming for NTFS and SMB shares, but not
            # on FAT32 or exFAT file systems. Perform a normal move first,
            # then check the result.
            shutil.move(source_path, target_path)
            try:
                # Get the path in the actual casing as stored on disk
                actual_path = win32api.GetLongPathNameW(win32api.GetShortPathName(target_path))
                if samefile_different_casing(target_path, actual_path):
                    _move_force_rename(source_path, target_path)
            except pywintypes.error:
                pass
            return
    # Just perform a normal move
    try:
        shutil.move(source_path, target_path)
    except shutil.SameFileError:
        # Sometimes different paths refer to the same file (e.g. network path / local path on Windows)
        pass


def make_save_path(path, win_compat=False, mac_compat=False):
    """Performs a couple of cleanups on a path to avoid side effects and incompatibilities.

    - If win_compat is True, trailing dots in file and directory names will
      be removed, as they are unsupported on Windows (dot is a delimiter for the file extension)
    - Leading dots in file and directory names will be removed. These files cannot be properly
      handled by Windows Explorer and on Unix like systems they count as hidden
    - If mac_compat is True, normalize precomposed Unicode characters on macOS

    Args:
        path: filename or path to clean
        win_compat: Set to True, if Windows compatibility is required
        mac_compat: Set to True, if macOS compatibility is required

    Returns: sanitized path
    """
    if win_compat:
        path = path.replace('./', '_/').replace('.\\', '_\\')
        if path.endswith('.'):
            path = path[:-1] + '_'
    # replace . at the beginning of file and directory names
    path = path.replace('/.', '/_').replace('\\.', '\\_')
    if path.startswith('.'):
        path = '_' + path[1:]
    # Fix for precomposed characters on macOS.
    if mac_compat:
        path = unicodedata.normalize("NFD", path)
    return path


def get_available_filename(new_path, old_path=None):
    """Returns an available file name.

    If new_path does already exist it appends " (N)" to the file name, where
    N is an integer counted upwards.

    If `old_path` is given the `new_path` is only changed if it does not point
    to the same file location.

    Args:
      new_path: The requested file name for the file
      old_path: The previous name of the file

    Returns: A unique available file name.
    """
    tmp_filename, ext = os.path.splitext(new_path)
    i = 1
    compare_old_path = old_path and os.path.exists(old_path)
    while (os.path.exists(new_path)
               and (not compare_old_path or not samefile(old_path, new_path))):
        new_path = "%s (%d)%s" % (tmp_filename, i, ext)
        i += 1
    return new_path


def replace_extension(filename, new_ext):
    """Replaces the extension in filename with new_ext.

    If the file has no extension the extension is added.

    Args:
        filename: A file name
        new_ext: New file extension

    Returns: filename with replaced file extension
    """
    name, ext = os.path.splitext(filename)
    return name + '.' + new_ext.lstrip('.')
