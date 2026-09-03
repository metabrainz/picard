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
    Iterable,
    Iterator,
)
from time import monotonic

from PyQt6 import QtCore


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
