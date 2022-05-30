# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2008-2011, 2014, 2018-2022 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 david
# Copyright (C) 2010 fatih
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012, 2014-2015 Wieland Hoffmann
# Copyright (C) 2013 Ionuț Ciocîrlan
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2013-2014, 2018-2021 Laurent Monin
# Copyright (C) 2014 Johannes Dewender
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 barami
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018, 2021 Bob Swift
# Copyright (C) 2020 Ray Bouchard
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021 Louis Sautier
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


import builtins
from collections import namedtuple
from collections.abc import Mapping
from itertools import chain
import json
from locale import strxfrm as _strxfrm
import ntpath
from operator import attrgetter
import os
from pathlib import PurePath
import re
import subprocess  # nosec: B404
import sys
from time import monotonic
import unicodedata

from dateutil.parser import parse

from PyQt5 import QtCore

from picard import log
from picard.const import (
    DEFAULT_COPY_TEXT,
    DEFAULT_NUMBERED_TITLE_FORMAT,
    MUSICBRAINZ_SERVERS,
)
from picard.const.sys import (
    FROZEN_TEMP_PATH,
    IS_FROZEN,
    IS_MACOS,
    IS_WIN,
)


if IS_WIN:
    import winreg

# Windows path length constraints
# See https://docs.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation
# the entire path's length (260 - 1 null character)
WIN_MAX_FILEPATH_LEN = 259
# the entire parent directory path's length must leave room for a 8.3 filename
WIN_MAX_DIRPATH_LEN = WIN_MAX_FILEPATH_LEN - 12
# a single node's (directory or file) length
WIN_MAX_NODE_LEN = 255
# Prefix for long paths in Windows API
WIN_LONGPATH_PREFIX = '\\\\?\\'


class LockableObject(QtCore.QObject):

    """Read/write lockable object."""

    def __init__(self):
        super().__init__()
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


def process_events_iter(iterable, interval=0.1):
    """
    Creates an iterator over iterable that calls QCoreApplication.processEvents()
    after certain time intervals.

    This must only be used in the main thread.

    Args:
        iterable: iterable object to iterate over
        interval: interval in seconds to call QCoreApplication.processEvents()
    """
    if interval:
        start = monotonic()
    for item in iterable:
        if interval:
            now = monotonic()
            delta = now - start
            if delta > interval:
                start = now
                QtCore.QCoreApplication.processEvents()
        yield item
    QtCore.QCoreApplication.processEvents()


def iter_files_from_objects(objects, save=False):
    """Creates an iterator over all unique files from list of albums, clusters, tracks or files."""
    return iter_unique(chain(*(obj.iterfiles(save) for obj in objects)))


_io_encoding = sys.getfilesystemencoding()


# The following was adapted from k3b's source code:
# On a glibc system the system locale defaults to ANSI_X3.4-1968
# It is very unlikely that one would set the locale to ANSI_X3.4-1968
# intentionally
def check_io_encoding():
    if _io_encoding == "ANSI_X3.4-1968":
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
    if isinstance(filename, str):
        if os.path.supports_unicode_filenames and sys.platform != "darwin":
            return filename
        else:
            return filename.encode(_io_encoding, 'replace')
    else:
        return filename


def decode_filename(filename):
    """Decode strings from filesystem encoding to unicode."""
    if isinstance(filename, str):
        return filename
    else:
        return filename.decode(_io_encoding)


def _check_windows_min_version(major, build):
    try:
        v = sys.getwindowsversion()
        return v.major >= major and v.build >= build
    except AttributeError:
        return False


def system_supports_long_paths():
    """Detects long path support.

    On Windows returns True, only if long path support is enabled in the registry (Windows 10 1607 or later).
    All other systems return always True.
    """
    if not IS_WIN:
        return True
    try:
        # Use cached value
        return system_supports_long_paths._supported
    except AttributeError:
        pass
    try:
        # Long path support can be enabled in Windows 10 version 1607 or later
        if _check_windows_min_version(10, 14393):
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
                supported = winreg.QueryValueEx(key, "LongPathsEnabled")[0] == 1
        else:
            supported = False
        system_supports_long_paths._supported = supported
        return supported
    except OSError:
        log.info('Failed reading LongPathsEnabled from registry')
        return False


def normpath(path):
    path = os.path.normpath(path)
    try:
        path = os.path.realpath(path)
    except OSError as why:
        # realpath can fail if path does not exist or is not accessible
        # or on Windows if drives are mounted without mount manager
        # (see https://tickets.metabrainz.org/browse/PICARD-2425).
        log.warning('Failed getting realpath for "%s": %s', path, why)
    # If the path is longer than 259 characters on Windows, prepend the \\?\
    # prefix. This enables access to long paths using the Windows API. See
    # https://docs.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation
    if (IS_WIN and len(path) > WIN_MAX_FILEPATH_LEN and not system_supports_long_paths()
        and not path.startswith(WIN_LONGPATH_PREFIX)):
        path = WIN_LONGPATH_PREFIX + path
    return path


def is_absolute_path(path):
    """Similar to os.path.isabs, but properly detects Windows shares as absolute paths
    See https://bugs.python.org/issue22302
    """
    return os.path.isabs(path) or (IS_WIN and os.path.normpath(path).startswith("\\\\"))


def samepath(path1, path2):
    return os.path.normcase(os.path.normpath(path1)) == os.path.normcase(os.path.normpath(path2))


def samefile(path1, path2):
    """Returns True, if both `path1` and `path2` refer to the same file.

    Behaves similar to os.path.samefile, but first checks identical paths including
    case insensitive comparison on Windows using os.path.normcase. This fixes issues on
    some network drives (e.g. VirtualBox mounts) where two paths different only in case
    are considered separate files by os.path.samefile.
    """
    return samepath(path1, path2) or os.path.samefile(path1, path2)


def format_time(ms, display_zero=False):
    """Formats time in milliseconds to a string representation."""
    ms = float(ms)
    if ms == 0 and not display_zero:
        return "?:??"
    duration_seconds = round(ms / 1000)
    if duration_seconds < 3600:
        minutes, seconds = divmod(duration_seconds, 60)
        return "%d:%02d" % (minutes, seconds)
    else:
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return "%d:%02d:%02d" % (hours, minutes, seconds)


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


_re_win32_incompat = re.compile(r'["*:<>?|]', re.UNICODE)
def replace_win32_incompat(string, repl="_"):  # noqa: E302
    """Replace win32 filename incompatible characters from ``string`` by
       ``repl``."""
    # Don't replace : with _ for windows drive
    if IS_WIN and os.path.isabs(string):
        drive, rest = ntpath.splitdrive(string)
        return drive + _re_win32_incompat.sub(repl, rest)
    else:
        return _re_win32_incompat.sub(repl, string)


_re_non_alphanum = re.compile(r'\W+', re.UNICODE)
def strip_non_alnum(string):  # noqa: E302
    """Remove all non-alphanumeric characters from ``string``."""
    return _re_non_alphanum.sub(" ", string).strip()


def sanitize_filename(string, repl="_", win_compat=False):
    string = string.replace(os.sep, repl)
    if os.altsep:
        string = string.replace(os.altsep, repl)
    if win_compat and os.altsep != '\\':
        string = string.replace('\\', repl)
    return string


def make_filename_from_title(title=None, default=None):
    if default is None:
        default = _("No Title")
    if not title or not title.strip():
        title = default
    filename = sanitize_filename(title, win_compat=IS_WIN)
    if IS_WIN:
        filename = replace_win32_incompat(filename)
    return filename


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


def _add_windows_executable_extension(*executables):
    return [e if e.endswith(('.py', '.exe')) else e + '.exe' for e in executables]


def find_executable(*executables):
    if IS_WIN:
        executables = _add_windows_executable_extension(*executables)
    paths = [os.path.dirname(sys.executable)] if sys.executable else []
    paths += os.environ.get('PATH', '').split(os.pathsep)
    paths.append('./')

    # This is for searching for executables bundled in packaged builds
    if IS_FROZEN:
        paths += [FROZEN_TEMP_PATH]
    for path in paths:
        for executable in executables:
            f = os.path.join(path, executable)
            if os.path.isfile(f):
                return os.path.abspath(f)


def run_executable(executable, *args, timeout=None):
    # Prevent new shell window from appearing
    startupinfo = None
    if IS_WIN:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    # Include python interpreter if running a python script
    if ".py" in executable:
        arguments = [sys.executable, executable, *args]
    else:
        arguments = [executable, *args]

    # Call program with arguments
    ret = subprocess.run(  # nosec: B603
        arguments,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=startupinfo,
        timeout=timeout
    )

    # Return (error code, stdout and stderr)
    return ret.returncode, ret.stdout.decode(sys.stdout.encoding), ret.stderr.decode(sys.stderr.encoding)


_mbid_format = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
_re_mbid_val = re.compile(_mbid_format, re.IGNORECASE)
def mbid_validate(string):  # noqa: E302
    """Test if passed string is a valid mbid
    """
    return _re_mbid_val.match(string) is not None


def parse_amazon_url(url):
    """Extract host and asin from an amazon url.
    It returns a dict with host and asin keys on success, None else
    """
    r = re.compile(r'^https?://(?:www.)?(?P<host>.*?)(?:\:[0-9]+)?/.*/(?P<asin>[0-9B][0-9A-Z]{9})(?:[^0-9A-Z]|$)')
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
            decorator.prev = monotonic()
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
            now = monotonic()
            r = interval - (now-decorator.prev)*1000.0
            if r <= 0:
                func(*args, **kwargs)
                decorator.prev = now
            else:
                decorator.args = args
                decorator.kwargs = kwargs
                QtCore.QTimer.singleShot(int(r), later)
                decorator.is_ticking = True
            mutex.unlock()

        return throttled_func

    decorator.prev = 0
    decorator.is_ticking = False
    return decorator


class IgnoreUpdatesContext:
    """Context manager for holding a boolean value, indicating whether updates are performed or not.
    By default the context resolves to False. If entered it is True. This allows
    to temporarily set a state on a block of code like:

        ignore_changes = IgnoreUpdatesContext()
        # Initially ignore_changes is False
        with ignore_changes:
            # Perform some tasks with ignore_changes now being True
            ...
        # ignore_changes is False again

    The code actually doing updates can check `ignore_changes` and only perform
    updates if it is `False`.
    """

    def __init__(self, onexit=None):
        self._entered = 0
        self._onexit = onexit

    def __enter__(self):
        self._entered += 1

    def __exit__(self, type, value, tb):
        self._entered -= 1
        if self._onexit:
            self._onexit()

    def __bool__(self):
        return self._entered > 0


def uniqify(seq):
    """Uniqify a list, preserving order"""
    return list(iter_unique(seq))


def iter_unique(seq):
    """Creates an iterator only returning unique values from seq"""
    seen = set()
    return (x for x in seq if x not in seen and not seen.add(x))


# order is important
_tracknum_regexps = [re.compile(r, re.I) for r in (
    # search for explicit track number (prefix "track")
    r"track[\s_-]*(?:(?:no|nr)\.?)?[\s_-]*(?P<number>\d+)",
    # search for 1- or 2-digit number at start of string (additional leading zeroes are allowed)
    # An optional disc number preceding the track number is ignored.
    r"^(?:\d+[\s_-])?(?P<number>0*\d{1,2})(?:\.)[^0-9,]",  # "99. ", but not "99.02"
    r"^(?:\d+[\s_-])?(?P<number>0*\d{1,2})[^0-9,.s]",
    # search for 2-digit number at end of string (additional leading zeroes are allowed)
    r"[^0-9,.\w](?P<number>0*\d{2})$",
    r"[^0-9,.\w]\[(?P<number>0*\d{1,2})\]$",
    r"[^0-9,.\w]\((?P<number>0*\d{2})\)$",
    # File names which consist of only a number
    r"^(?P<number>\d+)$",
)]


def tracknum_from_filename(base_filename):
    """Guess and extract track number from filename
    Returns `None` if none found, the number as integer else
    """
    filename, _ext = os.path.splitext(base_filename)
    for pattern in _tracknum_regexps:
        match = pattern.search(filename)
        if match:
            n = int(match.group('number'))
            # Numbers above 1900 are often years, track numbers should be much
            # smaller even for extensive collections
            if n > 0 and n < 1900:
                return n
    return None


GuessedFromFilename = namedtuple('GuessedFromFilename', ('tracknumber', 'title'))


def tracknum_and_title_from_filename(base_filename):
    """Guess tracknumber and title from filename.
    Uses `tracknum_from_filename` to guess the tracknumber. The filename is used
    as the title. If the tracknumber is at the beginning of the title it gets stripped.

    Returns a tuple `(tracknumber, title)`.
    """
    filename, _ext = os.path.splitext(base_filename)
    title = filename
    tracknumber = tracknum_from_filename(base_filename)
    if tracknumber is not None:
        tracknumber = str(tracknumber)
        stripped_filename = filename.lstrip('0')
        tnlen = len(tracknumber)
        if stripped_filename[:tnlen] == tracknumber:
            title = stripped_filename[tnlen:].lstrip()

    return GuessedFromFilename(tracknumber, title)


def is_hidden(filepath):
    """Test whether a file or directory is hidden.
    A file is considered hidden if it starts with a dot
    on non-Windows systems or if it has the "hidden" flag
    set on Windows."""
    name = os.path.basename(os.path.abspath(filepath))
    return (not IS_WIN and name.startswith('.')) \
        or _has_hidden_attribute(filepath)


if IS_WIN:
    from ctypes import windll

    def _has_hidden_attribute(filepath):
        try:
            attrs = windll.kernel32.GetFileAttributesW(filepath)
            assert attrs != -1
            return bool(attrs & 2)
        except (AttributeError, AssertionError):
            return False

elif IS_MACOS:
    import Foundation

    def _has_hidden_attribute(filepath):
        # On macOS detecting hidden files involves more than just checking for dot files, see
        # https://stackoverflow.com/questions/284115/cross-platform-hidden-file-detection
        url = Foundation.NSURL.fileURLWithPath_(filepath)
        result = url.getResourceValue_forKey_error_(None, Foundation.NSURLIsHiddenKey, None)
        return result[1]

else:
    def _has_hidden_attribute(filepath):
        return False


def linear_combination_of_weights(parts):
    """Produces a probability as a linear combination of weights
    Parts should be a list of tuples in the form:
        [(v0, w0), (v1, w1), ..., (vn, wn)]
    where vn is a value between 0.0 and 1.0
    and wn corresponding weight as a positive number
    """
    total = 0.0
    sum_of_products = 0.0
    for value, weight in parts:
        if value < 0.0:
            raise ValueError("Value must be greater than or equal to 0.0")
        if value > 1.0:
            raise ValueError("Value must be lesser than or equal to 1.0")
        if weight < 0:
            raise ValueError("Weight must be greater than or equal to 0.0")
        total += weight
        sum_of_products += value * weight
    if total == 0.0:
        return 0.0
    return sum_of_products / total


def album_artist_from_path(filename, album, artist):
    """If album is not set, try to extract album and artist from path.

    Args:
        filename: The full file path
        album: Default album name
        artist: Default artist name

    Returns:
        A tuple (album, artist)
    """
    if not album:
        path = PurePath(filename)
        dirs = list(path.relative_to(path.anchor).parent.parts)
        # Strip disc subdirectory from list
        if dirs and re.search(r'\b(?:CD|DVD|Disc)\s*\d+\b', dirs[-1], re.I):
            del dirs[-1]
        if dirs:
            # For clustering assume %artist%/%album%/file or %artist% - %album%/file
            album = dirs[-1]
            if ' - ' in album:
                new_artist, album = album.split(' - ', 1)
                if not artist:
                    artist = new_artist
            elif not artist and len(dirs) >= 2:
                artist = dirs[-2]
    return album, artist


def build_qurl(host, port=80, path=None, queryargs=None):
    """
    Builds and returns a QUrl object from `host`, `port` and `path` and
    automatically enables HTTPS if necessary.

    Encoded query arguments can be provided in `queryargs`, a
    dictionary mapping field names to values.
    """
    url = QtCore.QUrl()
    url.setHost(host)

    if port == 443 or host in MUSICBRAINZ_SERVERS:
        url.setScheme("https")
    elif port == 80:
        url.setScheme("http")
    else:
        url.setScheme("http")
        url.setPort(port)

    if path is not None:
        url.setPath(path)
    if queryargs is not None:
        url_query = QtCore.QUrlQuery()
        for k, v in queryargs.items():
            url_query.addQueryItem(k, str(v))
        url.setQuery(url_query)
    return url


def union_sorted_lists(list1, list2):
    """
    Returns union of two sorted lists.
    >> list1 = [1, 2, 2, 2, 3]
    >> list2 = [2, 3, 4]
    >> union_sorted_lists(list1, list2)
    >> [1, 2, 2, 2, 3, 4]
    """
    union = []
    i = 0
    j = 0
    while i != len(list1) and j != len(list2):
        if list1[i] > list2[j]:
            union.append(list2[j])
            j += 1
        elif list1[i] < list2[j]:
            union.append(list1[i])
            i += 1
        else:
            union.append(list1[i])
            i += 1
            j += 1
    if i == len(list1):
        union.extend(list2[j:])
    else:
        union.extend(list1[i:])

    return union


def __convert_to_string(obj):
    """Appropriately converts the input `obj` to a string.

    Args:
        obj (QByteArray, bytes, bytearray, ...): The input object

    Returns:
        string: The appropriately decoded string

    """
    if isinstance(obj, QtCore.QByteArray):
        return bytes(obj).decode()
    elif isinstance(obj, (bytes, bytearray)):
        return obj.decode()
    else:
        return str(obj)


def convert_to_string(obj):
    log.warning("string_() and convert_to_string() are deprecated, do not use")
    return __convert_to_string(obj)


builtins.__dict__['string_'] = convert_to_string


def load_json(data):
    """Deserializes a string or bytes like json response and converts
    it to a python object.

    Args:
        data (QByteArray, bytes, bytearray, ...): The json response

    Returns:
        dict: Response data as a python dict

    """
    return json.loads(__convert_to_string(data))


def parse_json(reply):
    return load_json(reply.readAll())


def restore_method(func):
    def func_wrapper(*args, **kwargs):
        if not QtCore.QObject.tagger._no_restore:
            return func(*args, **kwargs)
    return func_wrapper


def reconnect(signal, newhandler=None, oldhandler=None):
    """
    Reconnect an handler to a signal

    It disconnects all previous handlers before connecting new one

    Credits: https://stackoverflow.com/a/21589403
    """
    while True:
        try:
            if oldhandler is not None:
                signal.disconnect(oldhandler)
            else:
                signal.disconnect()
        except TypeError:
            break
    if newhandler is not None:
        signal.connect(newhandler)


def compare_barcodes(barcode1, barcode2):
    """
    Compares two barcodes. Returns True if they are the same, False otherwise.

    Tries to normalize UPC barcodes to EAN barcodes so e.g. "727361379704"
    and "0727361379704" are considered the same.
    """
    barcode1 = barcode1 or ''
    barcode2 = barcode2 or ''
    if barcode1 == barcode2:
        return True
    if not barcode1 or not barcode2:
        return False
    return barcode1.zfill(13) == barcode2.zfill(13)


BestMatch = namedtuple('BestMatch', ('similarity', 'result'))


def sort_by_similarity(candidates):
    """Sorts the objects in candidates by similarity.

    Args:
        candidates: Iterable with objects having a `similarity`  attribute
    Returns: List of candidates sorted by similarity (highest similarity first)
    """
    return sorted(
        candidates,
        reverse=True,
        key=attrgetter('similarity')
    )


def find_best_match(candidates, no_match):
    """Returns a BestMatch based on the similarity of candidates.

    Args:
        candidates: Iterable with objects having a `similarity`  attribute
        no_match: Match to return if there was no candidate

    Returns: `BestMatch` with the similarity and the matched object as result.
    """
    best_match = max(candidates, key=attrgetter('similarity'), default=no_match)
    return BestMatch(similarity=best_match.similarity, result=best_match)


def get_qt_enum(cls, enum):
    """
    List all the names of attributes inside a Qt enum.

    Example:
        >>> from PyQt5.Qt import Qt
        >>> print(get_qt_enum(Qt, Qt.CoordinateSystem))
        ['DeviceCoordinates', 'LogicalCoordinates']
    """
    values = []
    for key in dir(cls):
        value = getattr(cls, key)
        if isinstance(value, enum):
            values.append(key)
    return values


def limited_join(a_list, limit, join_string='+', middle_string='…'):
    """Join elements of a list with `join_string`
    If list is longer than `limit`, middle elements will be dropped,
    and replaced by `middle_string`.

    Args:
        a_list: list of strings to join
        limit: maximum number of elements to join before limiting
        join_string: string used to join elements
        middle_string: string to insert in the middle if limited

    Returns:
        A string

    Example:
        >>> limited_join(['a', 'b', 'c', 'd', 'e', 'f'], 2)
        'a+…+f'
        >>> limited_join(['a', 'b', 'c', 'd', 'e', 'f'], 3)
        'a+…+f'
        >>> limited_join(['a', 'b', 'c', 'd', 'e', 'f'], 4)
        'a+b+…+e+f'
        >>> limited_join(['a', 'b', 'c', 'd', 'e', 'f'], 6)
        'a+b+c+d+e+f'
        >>> limited_join(['a', 'b', 'c', 'd', 'e', 'f'], 2, ',', '?')
        'a,?,f'
    """
    length = len(a_list)
    if limit <= 1 or limit >= length:
        return join_string.join(a_list)

    half = limit // 2
    start = a_list[:half]
    end = a_list[-half:]
    return join_string.join(start + [middle_string] + end)


def extract_year_from_date(dt):
    """ Extracts year from  passed in date either dict or string """

    try:
        if isinstance(dt, Mapping):
            return int(dt.get('year'))
        else:
            return parse(dt).year
    except (TypeError, ValueError):
        return None


def pattern_as_regex(pattern, allow_wildcards=False, flags=0):
    """Parses a string and interprets it as a matching pattern.

    - If pattern is of the form /pattern/flags it is interpreted as a regular expression (e.g. `/foo.*/`).
      The flags are optional and in addition to the flags passed in the `flags` function parameter. Supported
      flags in the expression are "i" (ignore case) and "m" (multiline)
    - Otherwise if `allow_wildcards` is True, it is interpreted as a pattern that allows wildcard matching (see below)
    - If `allow_wildcards` is False a regex matching the literal string is returned

    Wildcard matching currently supports these characters:
    - `*`: Matches an arbitrary number of characters or none, e.g. `fo*` matches "foo" or "foot".
    - `?`: Matches exactly one character, e.g. `fo?` matches "foo" or "for".
    - `[...]`: Matches any character in the set, e.g. `[fo?]` matches all of "f", "o" and "?".
    - `?`, `*`, `[`, `]` and `\\` can be escaped with a backslash \\ to match the literal
      character, e.g. `fo\\?` matches "fo?".

    Args:
        pattern: The pattern as a string
        allow_wildcards: If true and if the the pattern is not interpreted as a regex wildard matching is allowed.
        flags: Additional regex flags to set (e.g. `re.I`)

    Returns: An re.Pattern instance

    Raises: `re.error` if the regular expression could not be parsed
    """
    plain_pattern = pattern.rstrip('im')
    if len(plain_pattern) > 2 and plain_pattern[0] == '/' and plain_pattern[-1] == '/':
        extra_flags = pattern[len(plain_pattern):]
        if 'i' in extra_flags:
            flags |= re.IGNORECASE
        if 'm' in extra_flags:
            flags |= re.MULTILINE
        regex = plain_pattern[1:-1]
    elif allow_wildcards:
        regex = '^' + wildcards_to_regex_pattern(pattern) + '$'
    else:
        regex = re.escape(pattern)
    return re.compile(regex, flags)


def wildcards_to_regex_pattern(pattern):
    """Converts a pattern with shell like wildcards into a regular expression string.

    The following syntax is supported:
    - `*`: Matches an arbitrary number of characters or none, e.g. `fo*` matches "foo" or "foot".
    - `?`: Matches exactly one character, e.g. `fo?` matches "foo" or "for".
    - `[...]`
    - `?`, `*` and `\\` can be escaped with a backslash \\ to match the literal character, e.g. `fo\\?` matches "fo?".

    Args:
        pattern: The pattern as a string

    Returns: A string with a valid regular expression.
    """
    regex = []
    group = None
    escape = False
    for c in pattern:
        if group is not None:
            if escape:
                if c in {'\\', '[', ']'}:
                    c = '\\' + c
                else:
                    group.append('\\\\')
                escape = False
            if c == ']':
                group.append(c)
                part = ''.join(group)
                group = None
            elif c == '\\':
                escape = True
                continue
            else:
                group.append(c)
                continue
        elif escape:
            if c in {'*', '?', '\\', '[', ']'}:
                part = '\\' + c
            else:
                part = re.escape('\\' + c)
            escape = False
        elif c == '\\':
            escape = True
            continue
        elif c == '[':
            group = ['[']
            continue
        elif c == '*':
            part = '.*'
        elif c == '?':
            part = '.'
        else:
            part = re.escape(c)
        regex.append(part)

    # There might be an unclosed character group. Interpret the starting
    # bracket of the group as a literal bracket and re-evaluate the rest.
    if group is not None:
        regex.append('\\[')
        regex.append(wildcards_to_regex_pattern(''.join(group[1:])))
    return ''.join(regex)


def _regex_numbered_title_fmt(fmt, title_repl, count_repl):
    title_marker = '{title}'
    count_marker = '{count}'

    parts = fmt.split(title_marker)

    def wrap_count(p):
        if count_marker in p:
            return '(?:' + re.escape(p) + ')?'
        else:
            return p

    return (
        re.escape(title_marker).join(wrap_count(p) for p in parts)
        .replace(re.escape(title_marker), title_repl)
        .replace(re.escape(count_marker), count_repl)
    )


def unique_numbered_title(default_title, existing_titles, fmt=None):
    """Generate a new unique and numbered title
       based on given default title and existing titles
    """
    if fmt is None:
        fmt = _(DEFAULT_NUMBERED_TITLE_FORMAT)

    escaped_title = re.escape(default_title)
    reg_count = r'(\d+)'
    regstr = _regex_numbered_title_fmt(fmt, escaped_title, reg_count)
    regex = re.compile(regstr)
    count = 0
    for title in existing_titles:
        m = regex.fullmatch(title)
        if m:
            num = m.group(1)
            if num is not None:
                count = max(count, int(num))
            else:
                count += 1
    return fmt.format(title=default_title, count=count + 1)


def get_base_title_with_suffix(title, suffix, fmt=None):
    """Extract the base portion of a title,
       removing the suffix and number portion from the end.
    """
    if fmt is None:
        fmt = _(DEFAULT_NUMBERED_TITLE_FORMAT)

    escaped_suffix = re.escape(suffix)
    reg_title = r'(?P<title>.*?)(?:\s*' + escaped_suffix + ')?'
    reg_count = r'\d*'
    regstr = _regex_numbered_title_fmt(fmt, reg_title, reg_count)\
        .replace(r'\ ', r'\s+')\
        .replace(' ', r'\s+')
    match_obj = re.fullmatch(regstr, title)
    return match_obj['title'] if match_obj else title


def get_base_title(title):
    """Extract the base portion of a title, using the standard suffix.
    """
    suffix = _(DEFAULT_COPY_TEXT)
    return get_base_title_with_suffix(title, suffix)


def iter_exception_chain(err):
    """Iterate over the exception chain.
    Yields this exception and all __context__ and __cause__ exceptions"""
    yield err
    if hasattr(err, '__context__'):
        yield from iter_exception_chain(err.__context__)
    if hasattr(err, '__cause__'):
        yield from iter_exception_chain(err.__cause__)


def any_exception_isinstance(error, type_):
    """Returns True, if any exception in the exception chain is instance of type_."""
    return any(isinstance(err, type_) for err in iter_exception_chain(error))


def strxfrm(string):
    """Transforms a string to one that can be used in locale-aware comparisons.

    Wrapper around locale.strxfrm, that never throws OSError. If an OSError
    occurs this function will return the string converted to lower case.

    Args:
        string: The string to convert

    Returns: A string that can be compared locale-aware
    """
    try:
        return _strxfrm(string)
    except OSError as err:
        log.warning('strxfrm(%r) failed: %r', string, err)
        return string.lower()
