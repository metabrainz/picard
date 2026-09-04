# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2008-2011, 2014, 2018-2026 Philipp Wolfer
# Copyright (C) 2013-2014, 2018-2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

"""Qt-dependent utility helpers.

These helpers depend on PyQt6 (QtCore/QtNetwork) and are kept separate from
``picard.util`` so that importing ``picard.util`` does not pull in Qt. This
keeps the bulk of the utility helpers usable from Qt-free contexts (e.g. build
tooling or a potential headless/alternative frontend).
"""

from collections.abc import (
    Callable,
    Generator,
    Iterable,
    Iterator,
    Mapping,
)
from contextlib import contextmanager
from time import monotonic
from typing import Any

from PyQt6 import QtCore
from PyQt6.QtNetwork import QNetworkReply

from picard.const import MUSICBRAINZ_SERVERS
from picard.util import load_json


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


def parse_json(reply: QNetworkReply) -> Any:
    """Deserialize the JSON body of a ``QNetworkReply`` to a Python object."""
    return load_json(reply.readAll().data())


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
