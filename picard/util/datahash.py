# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007-2011, 2014, 2018-2026 Philipp Wolfer
# Copyright (C) 2013-2015, 2018-2026 Laurent Monin
# Copyright (C) 2026 Laurent Monin
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

"""Content-addressed binary data backed by temporary files.

``DataHash`` keeps arbitrary binary data out of RAM by storing it in a
temporary file and holding only a hash and filename in memory. Identical data
is deduplicated: constructing a ``DataHash`` for bytes that already have a live
instance returns that instance (and the same temp file). The temp file is
removed once the last reference to its ``DataHash`` is dropped.

Originally written for cover-art image data; it is format-agnostic and can back
any large blob (e.g. serialized JSON) that should not stay resident in memory.
"""

import gc
from hashlib import blake2b
import os
import tempfile
from weakref import WeakValueDictionary

from PyQt6.QtCore import QMutex

from picard import log
from picard.util import periodictouch


class DataHash:
    """Holds binary data backed by a temporary file on the file system.

    This class can efficiently handle large binary data. Instead of holding the
    data in memory it is stored in a temporary file. Identical binary data
    results in the same DataHash instance and hence the same temporary file.

    Temporary files are automatically cleared once the last reference to a
    DataHash instance gets deleted.
    """

    __datahashes: WeakValueDictionary[str, 'DataHash'] = WeakValueDictionary()
    __datafile_mutex = QMutex()

    # Set during construction in _write_data(); annotated here so the types are
    # visible without reading that method.
    _hash: str
    _filename: str

    def __new__(cls, data: bytes, prefix: str = 'picard', suffix: str = '') -> 'DataHash':
        """Creates a new instance of DataHash for data.

        If there is already an existing instance with the same data then this
        instance will be returned. Otherwise a new instance will be created
        together with a temporary file to hold the data.
        """
        if not isinstance(data, bytes):
            raise TypeError('data must be bytes')

        hash = blake2b(data).hexdigest()

        # prevent garbage collection while lock is acquired
        gc.disable()
        DataHash.__datafile_mutex.lock()
        try:
            if instance := DataHash.__datahashes.get(hash, None):
                return instance
            instance = super().__new__(cls)
            instance._write_data(hash, data, prefix, suffix)
            DataHash.__datahashes[hash] = instance
            return instance
        finally:
            DataHash.__datafile_mutex.unlock()
            gc.enable()

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        return self._hash == getattr(other, '_hash', None)

    def __lt__(self, other: 'DataHash') -> bool:
        return self._hash < other._hash

    def __repr__(self) -> str:
        return f'<DataHash {self.shorthash}>'

    def __str__(self) -> str:
        return self._hash

    def __hash__(self) -> int:
        return hash(self._hash)

    def __del__(self) -> None:
        self._delete_file()

    @property
    def hash(self) -> str:
        """The hash value of the data."""
        return self._hash

    @property
    def shorthash(self) -> str:
        """A shortened version of the hash for display purposes."""
        return self._hash[:16]

    def data(self) -> bytes:
        """Returns the stored data.

        The data is read from the file system. Might raise OSError.
        """
        with open(self._filename, 'rb') as datafile:
            return datafile.read()

    @property
    def filename(self) -> str | None:
        """The filename of the temporary file."""
        return self._filename

    def _write_data(self, hash: str, data: bytes, prefix: str, suffix: str) -> None:
        self._hash = hash
        (fd, filepath) = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        self._filename = filepath
        # On some systems (notably macOS) temporary files are removed after
        # a certain period of time without access.
        periodictouch.register_file(filepath)
        with os.fdopen(fd, 'wb') as datafile:
            datafile.write(data)
        log.debug("Saving data %s to %r", self.shorthash, filepath)

    def _delete_file(self) -> None:
        if not self._filename:
            return

        DataHash.__datafile_mutex.lock()
        try:
            os.unlink(self._filename)
            periodictouch.unregister_file(self._filename)
        except BaseException as e:
            log.debug("Failed to delete file %r: %s", self._filename, e)
        finally:
            DataHash.__datafile_mutex.unlock()

    @staticmethod
    def remove_all_files() -> None:
        """Remove all temporary DataHash files stored on disk.

        Warning: This will leave all existing DataHash instances without file
        data. This method is not meant to be called during normal operation,
        but might be called as part of the cleanup routine during application
        shutdown.
        """
        for hash in DataHash.__datahashes.values():
            hash._delete_file()
