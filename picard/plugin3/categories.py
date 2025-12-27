# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
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

"""Utilities for plugin categories."""

from collections.abc import MutableSet

from picard.i18n import (
    N_,
    gettext as _,
    sort_key,
)


CATEGORIES_TITLES = {
    'coverart': N_('Cover Art'),
    'formats': N_('Formats'),
    'metadata': N_('Metadata'),
    'other': N_('Other'),
    'scripting': N_('Scripting'),
    'ui': N_('UI'),
}


def category_title_i18n(category):
    """Returns the translated title for a category if possible
    else returns the category key as passed
    """
    if category in CATEGORIES_TITLES:
        return _(CATEGORIES_TITLES[category])
    else:
        return category


class PluginCategorySet(MutableSet):
    def __init__(self, categories=None):
        self._categories = set(categories) if categories else set()

    def __contains__(self, key):
        return key in self._categories

    def __iter__(self):
        return iter(self._categories)

    def __len__(self):
        return len(self._categories)

    def add(self, key):
        self._categories.add(key)

    def discard(self, key):
        self._categories.discard(key)

    def update(self, other):
        self._categories.update(other)

    def clear(self):
        self._categories.clear()

    def remove(self, key):
        self._categories.remove(key)

    def pop(self):
        return self._categories.pop()

    def copy(self):
        return PluginCategorySet(self._categories)

    def items(self):
        """
        Generator yielding (key, translated_title) sorted by title.
        """
        # Create a list of (key, translated_title) tuples
        translated_items = ((key, category_title_i18n(key)) for key in self._categories)

        # Sort using the i18n sort_key on the translated title
        yield from sorted(translated_items, key=lambda item: sort_key(item[1]))

    def __str__(self):
        """
        Returns a comma-separated string of translated titles, sorted.
        """
        return ", ".join(title for key, title in self.items())

    def __repr__(self):
        return f"{self.__class__.__name__}({list(self._categories)})"
