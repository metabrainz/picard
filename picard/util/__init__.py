# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2008-2011, 2014, 2018-2024 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 david
# Copyright (C) 2010 fatih
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012, 2014-2015 Wieland Hoffmann
# Copyright (C) 2013 Ionuț Ciocîrlan
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2013-2014, 2018-2024 Laurent Monin
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
# Copyright (C) 2022 Kamil
# Copyright (C) 2022 skelly37
# Copyright (C) 2024 Arnab Chakraborty
# Copyright (C) 2024 ShubhamBhut
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

from collections import (
    defaultdict,
    namedtuple,
)
from collections.abc import (
    Callable,
    Generator,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
)
from contextlib import (
    contextmanager,
    suppress,
)
from datetime import (
    date,
    datetime,
)
from itertools import chain
import json
import ntpath
import os
from pathlib import (
    Path,
    PurePath,
)
import re
import subprocess  # nosec: B404
import sys
import tempfile
from time import monotonic
from typing import Any
import unicodedata

from PyQt6 import QtCore
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtNetwork import QNetworkReply

from picard import (
    log,
    tagger_instance,
)
from picard.const import (
    MUSICBRAINZ_SERVERS,
    PICARD_DOCS_URLS,
    PICARD_URLS,
)
from picard.const.sys import (
    FROZEN_TEMP_PATH,
    IS_FROZEN,
    IS_MACOS,
    IS_WIN,
)
from picard.i18n import (
    gettext as _,
    gettext_constants,
)


try:
    from charset_normalizer import detect  # type: ignore[unresolved-import]
except ImportError:
    try:
        from chardet import detect  # type: ignore[unresolved-import,no-redef]
    except ImportError:
        detect = None  # type: ignore[assignment]


winreg = None
if IS_WIN:
    import winreg  # type: ignore[assignment]

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
# Prefix for long UNC share paths in Windows API
WIN_LONGPATH_PREFIX_UNC = '\\\\?\\UNC\\'


class ReadWriteLockContext:
    """Context manager wrapping a `QReadWriteLock`.

    Multiple threads can obtain a read lock, but only one can obtain a write lock.
    Read and write locks can be explicitly entered with `lock_for_read` and `lock_for_write`:

        lock = ReadWriteLockContext()
        with lock.lock_for_read():
            ...
    """

    def __init__(self):
        self.__lock = QtCore.QReadWriteLock()

    def lock_for_read(self):
        self.__lock.lockForRead()
        return self

    def lock_for_write(self):
        self.__lock.lockForWrite()
        return self

    def unlock(self):
        self.__lock.unlock()

    def __enter__(self):
        pass

    def __exit__(self, type, value, tb):
        self.__lock.unlock()


def process_events_iter(iterable: Iterable, interval: float = 0.1) -> Iterator:
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


def iter_files_from_objects(objects: Iterable, save: bool = False) -> Iterator:
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


def resolve_fs_path(filename: str | bytes | Path) -> str:
    """Resolve a filename to its actual on-disk representation.

    Call this once when a path enters the file handling pipeline. After
    resolution, all downstream code can use the result directly without
    further normalization or encoding.

    Handles Unicode normalization mismatches (NFC vs NFD) that occur when
    files are accessed across different OS/filesystem combinations (e.g.
    macOS SMB client → Linux ext4 server).  See PICARD-3331.

    Args:
        filename: A file path as str, bytes, or Path.

    Returns:
        A str path that exists on disk (if any normalization variant matches),
        or the original path as str if no match is found.
    """
    if isinstance(filename, (bytes, bytearray)):
        filename = os.fsdecode(filename)
    elif isinstance(filename, Path):
        filename = str(filename)

    if os.path.exists(filename):
        return filename

    nfc = unicodedata.normalize('NFC', filename)
    if nfc != filename and os.path.exists(nfc):
        log.debug("Resolved filename via NFC normalization: %r", filename)
        return nfc

    nfd = unicodedata.normalize('NFD', filename)
    if nfd != filename and os.path.exists(nfd):
        log.debug("Resolved filename via NFD normalization: %r", filename)
        return nfd

    return filename


def _check_windows_min_version(major: int, build: int) -> bool:
    try:
        v = sys.getwindowsversion()
        return v.major >= major and v.build >= build
    except AttributeError:
        return False


def system_supports_long_paths() -> bool:
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
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
                supported = winreg.QueryValueEx(key, "LongPathsEnabled")[0] == 1
        else:
            supported = False
        system_supports_long_paths._supported = supported
        return supported
    except OSError:
        log.info("Failed reading LongPathsEnabled from registry")
        return False


def normpath(path: str, realpath: bool = True) -> str:
    path = os.path.normpath(path)
    if realpath:
        try:
            path = os.path.realpath(path)
        except OSError as why:
            # realpath can fail if path does not exist or is not accessible
            # or on Windows if drives are mounted without mount manager
            # (see https://tickets.metabrainz.org/browse/PICARD-2425).
            log.warning("Failed getting realpath for `%s`: %s", path, why)
    # If the path is longer than 259 characters on Windows, prepend the \\?\
    # prefix. This enables access to long paths using the Windows API. See
    # https://docs.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation
    if IS_WIN and not system_supports_long_paths():
        path = win_prefix_longpath(path)
    return path


def is_unc_path(path: str) -> bool:
    """Returns the path refers to a Windows UNC share."""
    # UNC paths start with two slashes followed by the hostname ("\\hostname\share\path)").
    # If path is a raw path a UNC share would use "\\?\UNC\hostname\share\path".
    return path.startswith(r'\\') and (
        not path.startswith(WIN_LONGPATH_PREFIX) or path[:8].upper() == WIN_LONGPATH_PREFIX_UNC
    )


def win_prefix_longpath(path: str) -> str:
    """
    For paths longer then WIN_MAX_FILEPATH_LEN enable long path support by prefixing with WIN_LONGPATH_PREFIX.

    See https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation
    """
    if len(path) > WIN_MAX_FILEPATH_LEN and not path.startswith(WIN_LONGPATH_PREFIX):
        if is_unc_path(path):
            path = WIN_LONGPATH_PREFIX_UNC + path[2:]
        else:
            path = WIN_LONGPATH_PREFIX + path
    return path


def is_absolute_path(path: str) -> bool:
    """Similar to os.path.isabs, but properly detects Windows shares as absolute paths
    See https://bugs.python.org/issue22302
    """
    if IS_WIN:
        # UNC paths are considered absolute.
        if is_unc_path(path):
            return True
        # Consider a single slash at the start not relative. This is the default
        # for `os.path.isabs` since Python 3.13.
        elif path.startswith("\\") or path.startswith("/"):
            return False
    return os.path.isabs(path)


def samepath(path1: str, path2: str) -> bool:
    return os.path.normcase(os.path.normpath(path1)) == os.path.normcase(os.path.normpath(path2))


def samefile(path1: str, path2: str) -> bool:
    """Returns True, if both `path1` and `path2` refer to the same file.

    Behaves similar to os.path.samefile, but first checks identical paths including
    case insensitive comparison on Windows using os.path.normcase. This fixes issues on
    some network drives (e.g. VirtualBox mounts) where two paths different only in case
    are considered separate files by os.path.samefile.
    """
    return samepath(path1, path2) or os.path.samefile(path1, path2)


def format_time(ms: float | int, display_zero: bool = False) -> str:
    """Formats time in milliseconds to a string representation.

    Args:
        ms: Time in milliseconds, must be positive.
        display_zero: If False, times of 0ms are displayed as '?:??'
    Raises:
        ValueError: If `ms` is negative.
        TypeError: If `ms` is not convertable to an integer.
    """
    ms = float(ms)
    if ms < 0:
        raise ValueError("ms must be greater than or equal to 0")
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


def sanitize_date(datestr: str) -> str:
    """Sanitize date format.

    e.g.: "1980-00-00" -> "1980"
          "1980-  -  " -> "1980"
          "1980-00-23" -> "1980-00-23"
          ...
    """
    date = []
    for num in reversed(datestr.split("-")):
        try:
            num = int(num.strip())
        except ValueError:
            if num == '':
                num = 0
            else:
                break
        if num or (num == 0 and date):
            date.append(num)
    date.reverse()
    return ("", "%04d", "%04d-%02d", "%04d-%02d-%02d")[len(date)] % tuple(date)


def replace_win32_incompat(string: str, repl: str = "_", replacements: dict[str, str] | None = None) -> str:
    """Replace win32 filename incompatible characters from ``string`` by
    ``repl``."""
    # Don't replace : for windows drive
    if IS_WIN and os.path.isabs(string):
        drive, string = ntpath.splitdrive(string)
    else:
        drive = ''

    replacements = defaultdict(lambda: repl, replacements or {})
    for char in {'"', '*', ':', '<', '>', '?', '|'}:
        if char in string:
            string = string.replace(char, replacements[char])

    return drive + string


_re_non_alphanum = re.compile(r'\W+', re.UNICODE)


def strip_non_alnum(string: str) -> str:
    """Remove all non-alphanumeric characters from ``string``."""
    return _re_non_alphanum.sub(" ", string).strip()


def sanitize_filename(string: str, repl: str = "_", win_compat: bool = False) -> str:
    string = string.replace(os.sep, repl)
    if os.altsep:
        string = string.replace(os.altsep, repl)
    if win_compat and os.altsep != '\\':
        string = string.replace('\\', repl)
    return string


def make_filename_from_title(title: str | None = None, default: str | None = None) -> str:
    if default is None:
        default = _("No Title")
    if not title or not title.strip():
        title = default
    filename = sanitize_filename(title, win_compat=IS_WIN)
    if IS_WIN:
        filename = replace_win32_incompat(filename)
    return filename


def _reverse_sortname(sortname: str) -> str:
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


def translate_from_sortname(name: str, sortname: str) -> str:
    """'Translate' the artist name by reversing the sortname."""
    for c in name:
        ctg = unicodedata.category(c)
        if ctg[0] == "L" and unicodedata.name(c).find('LATIN') == -1:
            for separator in (" & ", "; ", " and ", " vs. ", " with ", " y "):
                if separator in sortname:
                    parts = sortname.split(separator)
                    break
            else:
                parts = [sortname]
                separator = ""
            return separator.join(map(_reverse_sortname, parts))
    return name


def find_existing_path(path: str) -> str:
    while path and not os.path.isdir(path):
        head, tail = os.path.split(path)
        if head == path:
            break
        path = head
    return path


def _add_windows_executable_extension(*executables: str) -> tuple[str, ...]:
    return tuple(e if e.endswith(('.py', '.exe')) else e + '.exe' for e in executables)


def find_executable(*executables: str) -> str | None:
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


def run_executable(executable: str, *args, timeout: int | float | None = None) -> tuple[int, str, str]:
    # Prevent new shell window from appearing
    startupinfo = None
    if IS_WIN:
        startupinfo = subprocess.STARTUPINFO()  # ty: ignore[unresolved-attribute]
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # ty: ignore[unresolved-attribute]

    # Include python interpreter if running a python script
    if ".py" in executable:
        arguments = [sys.executable, executable, *args]
    else:
        arguments = [executable, *args]

    # Call program with arguments
    ret = subprocess.run(  # nosec: B603
        arguments,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        startupinfo=startupinfo,
        timeout=timeout,
    )

    # Return (error code, stdout and stderr)
    return ret.returncode, ret.stdout.decode(sys.stdout.encoding), ret.stderr.decode(sys.stderr.encoding)


def open_local_path(path: str) -> None:
    url = QtCore.QUrl.fromLocalFile(path)
    if os.environ.get('SNAP'):
        run_executable('xdg-open', url.toString())
    else:
        QDesktopServices.openUrl(url)


_mbid_format = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
_re_mbid_val = re.compile(_mbid_format, re.IGNORECASE)


def mbid_validate(string: str) -> bool:
    """Test if passed string is a valid mbid"""
    return _re_mbid_val.match(string) is not None


def parse_amazon_url(url: str) -> dict[str, str] | None:
    """Extract host and asin from an amazon url.
    It returns a dict with host and asin keys on success, None else
    """
    r = re.compile(r'^https?://(?:www.)?(?P<host>.*?)(?:\:[0-9]+)?/.*/(?P<asin>[0-9B][0-9A-Z]{9})(?:[^0-9A-Z]|$)')
    match_ = r.match(url)
    if match_ is not None:
        return match_.groupdict()
    return None


def throttle(interval: float | int) -> Callable:
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
            r = interval - (now - decorator.prev) * 1000.0
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

    def __init__(
        self,
        on_exit: Callable | None = None,
        on_enter: Callable | None = None,
        on_first_enter: Callable | None = None,
        on_last_exit: Callable | None = None,
    ):
        self._entered = 0
        self._on_exit = on_exit
        self._on_last_exit = on_last_exit
        self._on_enter = on_enter
        self._on_first_enter = on_first_enter

    def __enter__(self):
        self._entered += 1
        if self._on_enter:
            self._on_enter()
        if self._entered == 1 and self._on_first_enter:
            self._on_first_enter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._entered -= 1
        if self._on_exit:
            self._on_exit()
        if self._entered == 0 and self._on_last_exit:
            self._on_last_exit()

    def __bool__(self):
        return self._entered > 0


def uniqify(seq: Iterable) -> list:
    """Uniqify a list, preserving order"""
    return list(iter_unique(seq))


def iter_unique(seq: Iterable) -> Iterator:
    """Creates an iterator only returning unique values from seq"""
    seen = set()
    return (x for x in seq if x not in seen and not seen.add(x))


# order is important
_tracknum_regexps = [
    re.compile(r, re.I)
    for r in (
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
    )
]


def tracknum_from_filename(base_filename: str) -> int | None:
    """Guess and extract track number from filename
    Returns `None` if none found, the number as integer else
    """
    filename, _ext = os.path.splitext(base_filename)
    for pattern in _tracknum_regexps:
        match_ = pattern.search(filename)
        if match_:
            n = int(match_.group('number'))
            # Numbers above 1900 are often years, track numbers should be much
            # smaller even for extensive collections
            if n > 0 and n < 1900:
                return n
    return None


GuessedFromFilename = namedtuple('GuessedFromFilename', ('tracknumber', 'title'))


def tracknum_and_title_from_filename(base_filename: str) -> GuessedFromFilename:
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
            # Strip track number from title
            title = stripped_filename[tnlen:]
            # Strip the dot after the tracknumber, if present
            title = title.lstrip('.').lstrip()

    return GuessedFromFilename(tracknumber, title)


def is_hidden(filepath: str) -> bool:
    """Test whether a file or directory is hidden.
    A file is considered hidden if it starts with a dot
    on non-Windows systems or if it has the "hidden" flag
    set on Windows."""
    name = os.path.basename(os.path.abspath(filepath))
    return (not IS_WIN and name.startswith('.')) or _has_hidden_attribute(filepath)


if IS_WIN:
    from ctypes import windll  # type: ignore[attr-defined]

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


def linear_combination_of_weights(parts: list[tuple[float, int]]) -> float:
    """Produces a probability as a linear combination of weights
    Parts should be a list of tuples in the form:
        [(v0, w0), (v1, w1), ..., (vn, wn)]
    where vn is a value between 0.0 and 1.0
    and wn corresponding weight as a positive number
    """
    total = 0.0
    sum_of_products = 0.0
    for value, weight in parts:
        assert 0.0 <= value <= 1.0, f"Value {value} out of range [0.0, 1.0]"
        assert weight >= 0, f"Weight {weight} must be >= 0"
        total += weight
        sum_of_products += value * weight
    if total == 0.0:
        return 0.0
    return sum_of_products / total


def album_artist_from_path(filename: str, album: str, artist: str) -> tuple[str, str]:
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


def encoded_queryargs(queryargs: Mapping[str, Any]) -> dict[str, str]:
    """
    Percent-encode all values from passed dictionary
    Keys are left unmodified
    """
    return {name: QtCore.QUrl.toPercentEncoding(str(value)).data().decode() for name, value in queryargs.items()}


def get_url(url_key: str) -> str:
    """Gets the URL from the key, with {language} and {version} substitutions.
    Args:
        url_key (str): URL key.
    Returns:
        str: Updated URL, or provided URL key if not matched.
    """
    from picard.util.readthedocs import ReadTheDocs  # Local import to avoid circular import

    if url_key.startswith('/'):
        return (
            PICARD_DOCS_URLS['documentation'].format(
                language=ReadTheDocs.matched_language, version=ReadTheDocs.matched_version
            )
            + url_key
        )

    if url_key in PICARD_DOCS_URLS:
        return PICARD_DOCS_URLS[url_key].format(
            language=ReadTheDocs.matched_language, version=ReadTheDocs.matched_version
        )

    if url_key in PICARD_URLS:
        return PICARD_URLS[url_key]

    # No match in defined Picard URLs
    return url_key


def build_qurl(
    host: str, port: int = 80, path: str | None = None, queryargs: Mapping[str, Any] | None = None
) -> QtCore.QUrl:
    """
    Builds and returns a QUrl object from `host`, `port` and `path` and
    automatically enables HTTPS if necessary.

    Encoded query arguments can be provided in `queryargs`, a
    dictionary mapping field names to values.
    """
    url = QtCore.QUrl()
    url.setHost(host)

    if port == 443 or host in MUSICBRAINZ_SERVERS:
        url.setScheme('https')
    elif port == 80:
        url.setScheme('http')
    else:
        url.setScheme('http')
        url.setPort(port)

    if path is not None:
        url.setPath(path)
    if queryargs is not None:
        url_query = QtCore.QUrlQuery()
        for k, v in queryargs.items():
            url_query.addQueryItem(k, str(v))
        url.setQuery(url_query)
    return url


def union_sorted_lists(list1: Sequence, list2: Sequence) -> list:
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


def __convert_to_string(obj: Any) -> str:
    """Appropriately converts the input `obj` to a string.

    Args:
        obj (QByteArray, bytes, bytearray, ...): The input object

    Returns:
        string: The appropriately decoded string

    """
    if isinstance(obj, QtCore.QByteArray):
        return obj.data().decode()
    elif isinstance(obj, (bytes, bytearray)):
        return obj.decode()
    else:
        return str(obj)


def load_json(data: bytes | QtCore.QByteArray | str) -> Any:
    """Deserializes a string or bytes like json response and converts
    it to a python object.

    Args:
        data (QByteArray, bytes, bytearray, ...): The json response

    Returns:
        dict: Response data as a python dict

    """
    return json.loads(__convert_to_string(data))


def parse_json(reply: QNetworkReply) -> Any:
    return load_json(reply.readAll())


def restore_method(func: Callable) -> Callable:
    def func_wrapper(*args, **kwargs):
        tagger = tagger_instance()
        if not tagger._no_restore:
            return func(*args, **kwargs)

    return func_wrapper


def reconnect(
    signal: QtCore.pyqtBoundSignal, newhandler: Callable | None = None, oldhandler: Callable | None = None
) -> None:
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


@contextmanager
def temporary_disconnect(signal: QtCore.pyqtBoundSignal, *handlers: Callable) -> Generator[None, None, None]:
    """
    Create context to temporarly disconnect one or more signal handlers
    """
    try:
        for handler in handlers:
            signal.disconnect(handler)
        yield
    finally:
        for handler in handlers:
            signal.connect(handler)


def compare_barcodes(barcode1: str, barcode2: str) -> bool:
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


def limited_join(a_list: list[str], limit: int, join_string: str = '+', middle_string: str = '…') -> str:
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


def countries_shortlist(countries: list[str]) -> str:
    return limited_join(countries, 6, '+', '…')


def extract_year_from_date(dt: str | date | Mapping) -> int | None:
    """Extracts year from  passed in date either dict or string"""

    try:
        if isinstance(dt, date):
            return dt.year
        elif isinstance(dt, Mapping):
            if 'year' not in dt:
                return None
            return int(dt['year'])
        else:
            if isinstance(dt, str):
                dt = dt.strip()
            if parsed_date := parse_date(dt):
                return parsed_date.year
            else:
                return None
    except (OverflowError, TypeError, ValueError):
        return None


_DATE_FORMATS = (
    "%Y",
    "%Y-%m",
    "%Y-%m-%d",
    "%Y.%m",
    "%Y.%m",
    "%Y/%m/%d",
    "%Y/%m/%d",
    "%d.%m.%Y",
    "%m/%d/%Y",
    "%m.%d.%Y",
    "%d/%m/%Y",
)


def parse_date(dt: str) -> datetime | None:
    """Tries to parse a string into a datetime object.
    Returns None if the value could not be parsed.
    """
    # Try ISO formats first
    try:
        return datetime.fromisoformat(dt)
    except ValueError:
        pass

    # Fallback formats
    for format in _DATE_FORMATS:
        try:
            return datetime.strptime(dt, format)
        except ValueError:
            continue
    return None


def pattern_as_regex(pattern: str, allow_wildcards: bool = False, flags: int = 0) -> re.Pattern[str]:
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
        allow_wildcards: If true and if the pattern is not interpreted as a regex wildcard matching is allowed.
        flags: Additional regex flags to set (e.g. `re.I`)

    Returns: An re.Pattern instance

    Raises: `re.error` if the regular expression could not be parsed
    """
    plain_pattern = pattern.rstrip('im')
    if len(plain_pattern) > 2 and plain_pattern[0] == '/' and plain_pattern[-1] == '/':
        extra_flags = pattern[len(plain_pattern) :]
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


def wildcards_to_regex_pattern(pattern: str) -> str:
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


def _regex_numbered_title_fmt(fmt: str, title_repl: str, count_repl: str) -> str:
    title_marker = '{title}'
    count_marker = '{count}'

    parts = fmt.split(title_marker)

    def wrap_count(p):
        if count_marker in p:
            return '(?:' + re.escape(p) + ')?'
        else:
            return p

    return (
        re.escape(title_marker)
        .join(wrap_count(p) for p in parts)
        .replace(re.escape(title_marker), title_repl)
        .replace(re.escape(count_marker), count_repl)
    )


def _get_default_numbered_title_format() -> str:
    # Avoid circular import: util → const.defaults → util
    from picard.const.defaults import DEFAULT_NUMBERED_TITLE_FORMAT

    return gettext_constants(DEFAULT_NUMBERED_TITLE_FORMAT)


def unique_numbered_title(default_title: str, existing_titles: set[str], fmt: str | None = None) -> str:
    """Generate a new unique and numbered title
    based on given default title and existing titles
    """
    if fmt is None:
        fmt = _get_default_numbered_title_format()

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


def get_base_title_with_suffix(title: str, suffix: str, fmt: str | None = None) -> str:
    """Extract the base portion of a title,
    removing the suffix and number portion from the end.
    """
    if fmt is None:
        fmt = _get_default_numbered_title_format()

    escaped_suffix = re.escape(suffix)
    reg_title = r'(?P<title>.*?)(?:\s*' + escaped_suffix + ')?'
    reg_count = r'\d*'
    regstr = _regex_numbered_title_fmt(fmt, reg_title, reg_count).replace(r'\ ', r'\s+').replace(' ', r'\s+')
    match_obj = re.fullmatch(regstr, title)
    return match_obj['title'] if match_obj else title


def get_base_title(title: str) -> str:
    """Extract the base portion of a title, using the standard suffix."""
    # Avoid circular import: util → const.defaults → util
    from picard.const.defaults import DEFAULT_COPY_TEXT

    suffix = gettext_constants(DEFAULT_COPY_TEXT)
    return get_base_title_with_suffix(title, suffix)


def iter_exception_chain(err: BaseException) -> Iterator[BaseException]:
    """Iterate over the exception chain.
    Yields this exception and all __context__ and __cause__ exceptions"""
    yield err
    if context := getattr(err, '__context__', None):
        yield from iter_exception_chain(context)
    if cause := getattr(err, '__cause__', None):
        yield from iter_exception_chain(cause)


def any_exception_isinstance(error: BaseException, type_: type):
    """Returns True, if any exception in the exception chain is instance of type_."""
    return any(isinstance(err, type_) for err in iter_exception_chain(error))


ENCODING_BOMS = {
    b'\xff\xfe\x00\x00': 'utf-32-le',
    b'\x00\x00\xfe\xff': 'utf-32-be',
    b'\xef\xbb\xbf': 'utf-8-sig',
    b'\xff\xfe': 'utf-16-le',
    b'\xfe\xff': 'utf-16-be',
}


def detect_file_encoding(path: str, max_bytes_to_read: int = 1024 * 256) -> str:
    """Attempts to guess the unicode encoding of a file based on the BOM, and
    depending on avalibility, using a charset detection method.

    Assumes UTF-8 by default if no other encoding is detected.

    Args:
        path: The path to the file
        max_bytes_to_read: Maximum bytes to read from the file during encoding
        detection.

    Returns: The encoding as a string, e.g. "utf-16-le" or "utf-8"
    """
    with open(path, 'rb') as f:
        first_bytes = f.read(4)
        for bom, encoding in ENCODING_BOMS.items():
            if first_bytes.startswith(bom):
                return encoding

        if detect is None:
            return 'utf-8'

        f.seek(0)
        result = detect(f.read(max_bytes_to_read))
        if result['encoding'] is None:
            log.warning("Couldn't detect encoding for file %r", path)
            encoding = 'utf-8'
        elif result['encoding'].lower() == 'ascii':
            # Treat ASCII as UTF-8 (an ASCII document is also valid UTF-8)
            encoding = 'utf-8'
        else:
            encoding = result['encoding'].lower()

        return encoding


def iswbound(char: str) -> bool:
    # GPL 2.0 licensed code by Javier Kohen, Sambhav Kothari
    # from https://github.com/metabrainz/picard-plugins/blob/2.0/plugins/titlecase/titlecase.py
    """Checks whether the given character is a word boundary"""
    category = unicodedata.category(char)
    return 'Zs' == category or 'Sk' == category or 'P' == category[0]


def titlecase(text: str) -> str:
    # GPL 2.0 licensed code by Javier Kohen, Sambhav Kothari
    # from https://github.com/metabrainz/picard-plugins/blob/2.0/plugins/titlecase/titlecase.py
    """Converts text to title case following word boundary rules.

    Capitalizes the first character of each word in the input text, where words
    are determined by Unicode word boundaries. Preserves existing capitalization
    after the first character of each word.

    Args:
        text (str): The input text to convert to title case.

    Returns:
        str: The text converted to title case. Returns empty string if input is empty.

    Examples:
        >>> titlecase("hello world")
        'Hello World'
        >>> titlecase("children's music")
        'Children's Music'
    """
    if not text:
        return text
    capitalized = text[0].capitalize()
    capital = False
    for i in range(1, len(text)):
        t = text[i]
        if t in "’'" and text[i - 1].isalpha():
            capital = False
        elif iswbound(t):
            capital = True
        elif capital and t.isalpha():
            capital = False
            t = t.capitalize()
        else:
            capital = False
        capitalized += t
    return capitalized


def parse_versioning_scheme(versioning_scheme: str) -> re.Pattern | None:
    """Parse versioning scheme into compiled regex pattern.

    Args:
        versioning_scheme: Versioning scheme (semver, calver, or regex:<pattern>)

    Returns:
        re.Pattern: Compiled regex pattern or None if unknown/invalid scheme
    """
    if versioning_scheme == 'semver':
        pattern = r'^\D*\d+\.\d+(\.\d+)?$'
    elif versioning_scheme == 'calver':
        pattern = r'^\d{4}\.\d{2}\.\d{2}$'
    elif versioning_scheme.startswith('regex:'):
        pattern = versioning_scheme[6:]
    else:
        log.warning('Unknown versioning scheme: %s', versioning_scheme)
        return None

    try:
        return re.compile(pattern)
    except re.error as e:
        log.error('Invalid regex pattern in versioning scheme %s: %s', versioning_scheme, e)
        return None


def atomic_write(path: str, data: bytes) -> None:
    """Write bytes atomically to the given path.

    Writes to a temporary file in the destination directory and replaces
    the target file to ensure atomicity. On failure, cleans up the
    temporary file and re-raises the exception.

    Args:
        path: Target file path (str or Path)
        data: Bytes to write
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=p.parent,
            prefix=p.stem + '_',
            suffix=p.suffix,
            delete=False,
        ) as f:
            temp_path = Path(f.name)
            f.write(data)
        temp_path.replace(p)
    except (OSError, PermissionError):
        if temp_path and temp_path.exists():
            with suppress(OSError, PermissionError):
                temp_path.unlink()
        raise
