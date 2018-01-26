# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2017 Antonio Larrosa <alarrosa@suse.com>
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


class LRUCache(dict):
    """
    Helper class to cache items using a Least Recently Used policy.

    It's originally used to cache generated pixmaps in the CoverArtBox object
    but it's generic enough to be used for other purposes if necessary.
    The cache will never hold more than max_size items and the item least
    recently used will be discarded.

    >>> cache = LRUCache(3)
    >>> cache['item1'] = 'some value'
    >>> cache['item2'] = 'some other value'
    >>> cache['item3'] = 'yet another value'
    >>> cache['item1']
    'some value'
    >>> cache['item4'] = 'This will push item 2 out of the cache'
    >>> cache['item2']
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "lrucache.py", line 48, in __getitem__
        return super().__getitem__(key)
    KeyError: 'item2'
    >>> cache['item5'] = 'This will push item3 out of the cache'
    >>> cache['item3']
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "lrucache.py", line 48, in __getitem__
        return super().__getitem__(key)
    KeyError: 'item3'
    >>> cache['item1']
    'some value'
    """

    def __init__(self, max_size):
        self._ordered_keys = []
        self._max_size = max_size

    def __getitem__(self, key):
        if key in self:
            self._ordered_keys.remove(key)
            self._ordered_keys.insert(0, key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key in self:
            self._ordered_keys.remove(key)
        self._ordered_keys.insert(0, key)

        r = super().__setitem__(key, value)

        if len(self) > self._max_size:
            item = self._ordered_keys.pop()
            super().__delitem__(item)

        return r

    def __delitem__(self, key):
        self._ordered_keys.remove(key)
        super().__delitem__(key)
