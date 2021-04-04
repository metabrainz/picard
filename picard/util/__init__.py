# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2008-2011, 2014, 2018-2021 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 david
# Copyright (C) 2010 fatih
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012, 2014-2015 Wieland Hoffmann
# Copyright (C) 2013 Ionuț Ciocîrlan
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2013-2014, 2018-2020 Laurent Monin
# Copyright (C) 2014 Johannes Dewender
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 barami
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 Bob Swift
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020 Ray Bouchard
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
import html
from itertools import chain
import json
import ntpath
from operator import attrgetter
import os
import re
import sys
from time import monotonic
import unicodedata

from dateutil.parser import parse

from PyQt5 import QtCore

from picard import log
from picard.config import get_config
from picard.const import MUSICBRAINZ_SERVERS
from picard.const.sys import (
    FROZEN_TEMP_PATH,
    IS_FROZEN,
    IS_WIN,
)


if IS_WIN:
    from ctypes import windll


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


def normpath(path):
    try:
        path = os.path.realpath(path)
    except OSError as why:
        # realpath can fail if path does not exist or is not accessible
        log.warning('Failed getting realpath for "%s": %s', path, why)
    return os.path.normpath(path)


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
    if IS_WIN:
        executables = [e + '.exe' for e in executables]
    paths = [os.path.dirname(sys.executable)] if sys.executable else []
    paths += os.environ.get('PATH', '').split(os.pathsep)
    # This is for searching for executables bundled in packaged builds
    if IS_FROZEN:
        paths += [FROZEN_TEMP_PATH]
    for path in paths:
        for executable in executables:
            f = os.path.join(path, executable)
            if os.path.isfile(f):
                return f


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
                QtCore.QTimer.singleShot(r, later)
                decorator.is_ticking = True
            mutex.unlock()

        return throttled_func

    decorator.prev = 0
    decorator.is_ticking = False
    return decorator


def uniqify(seq):
    """Uniqify a list, preserving order"""
    return list(iter_unique(seq))


def iter_unique(seq):
    """Creates an iterator only returning unique values from seq"""
    seen = set()
    return (x for x in seq if x not in seen and not seen.add(x))


# order is important
_tracknum_regexps = (
    # search for explicit track number (prefix "track")
    r"track[\s_-]*(?:no|nr)?[\s_-]*(\d+)",
    # search for 2-digit number at start of string
    r"^(\d{2})\D",
    # search for 2-digit number at end of string
    r"\D(\d{2})$",
)


def tracknum_from_filename(base_filename):
    """Guess and extract track number from filename
    Returns `None` if none found, the number as integer else
    """
    filename, _ = os.path.splitext(base_filename)
    for r in _tracknum_regexps:
        match = re.search(r, filename, re.I)
        if match:
            n = int(match.group(1))
            if n > 0:
                return n
    # find all numbers between 1 and 99
    # 4-digit or more numbers are very unlikely to be a track number
    # smaller number is preferred in any case
    numbers = sorted([int(n) for n in re.findall(r'\d+', filename) if
                      0 < int(n) <= 99])
    if numbers:
        return numbers[0]
    return None


def is_hidden(filepath):
    """Test whether a file or directory is hidden.
    A file is considered hidden if it starts with a dot
    on non-Windows systems or if it has the "hidden" flag
    set on Windows."""
    name = os.path.basename(os.path.abspath(filepath))
    return (not IS_WIN and name.startswith('.')) \
        or _has_hidden_attribute(filepath)


def _has_hidden_attribute(filepath):
    if not IS_WIN:
        return False
    # FIXME: On OSX detecting hidden files involves more
    # than just checking for dot files, see
    # https://stackoverflow.com/questions/284115/cross-platform-hidden-file-detection
    try:
        attrs = windll.kernel32.GetFileAttributesW(filepath)
        assert attrs != -1
        return bool(attrs & 2)
    except (AttributeError, AssertionError):
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
    """If album is not set, try to extract album and artist from path
    """
    if not album:
        dirs = os.path.dirname(filename).replace('\\', '/').lstrip('/').split('/')
        # Strip disc subdirectory from list
        if re.search(r'\b(?:CD|DVD|Disc)\s*\d+\b', dirs[-1], re.I):
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
    url.setPort(port)

    if host in MUSICBRAINZ_SERVERS or port == 443:
        url.setScheme("https")
        url.setPort(443)
    else:
        url.setScheme("http")

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


def htmlescape(string):
    return html.escape(string, quote=False)


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


BestMatch = namedtuple('BestMatch', 'similarity result num_results')


def sort_by_similarity(candidates):
    return sorted(
        candidates(),
        reverse=True,
        key=attrgetter('similarity')
    )


def find_best_match(candidates, no_match):
    sorted_results = sort_by_similarity(candidates)
    if sorted_results:
        result = sorted_results[0]
    else:
        result = no_match
    return BestMatch(similarity=result.similarity, result=result, num_results=len(sorted_results))


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


def cached_settings(keys, settings=None, config=None):
    """Returns a dictionary with the given keys from config.setting.
    Can be used to create a partial cache / copy of specific settings.

    Args:
        keys: Array of setting keys to return
        settings: Dict to store the settings in. If None is given a new dict will be created.
        config: Optional instance of picard.config.Config to use

    Returns:
        Returns the settings dict with the given keys set
    """
    if settings is None:
        settings = {}
    if config is None:
        config = get_config()
    for key in keys:
        settings[key] = config.setting[key]
    return settings
