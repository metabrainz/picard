# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2007, 2012 Lukáš Lalinský
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012 Nikolai Prokoschenko
# Copyright (C) 2013-2014, 2017-2025 Laurent Monin
# Copyright (C) 2013-2014, 2021 Sophist-UK
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2015 Wieland Hoffmann
# Copyright (C) 2015, 2018-2025 Philipp Wolfer
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020 Felix Schwarz
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2024 Arnab Chakraborty
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
    Counter,
    defaultdict,
    namedtuple,
)

from picard.i18n import ngettext
from picard.metadata import MULTI_VALUED_JOINER
from picard.util import format_time


class TagStatus:
    NONE = 0
    NOCHANGE = 1
    ADDED = 2
    REMOVED = 4
    CHANGED = ADDED | REMOVED
    EMPTY = 8
    NOTREMOVABLE = 16
    READONLY = 32


TagCounterDisplayValue = namedtuple('TagCounterDisplayValue', ('text', 'is_grouped'))


class TagCounter(dict):
    """
    A specialized dictionary for tracking and displaying tag values across multiple objects.

    This class extends the built-in `dict` to provide functionality for:
    - Counting the occurrences of tags.
    - Detecting when tag values differ across objects.
    - Generating user-friendly text representations of tag values, including
      indications of differences and missing values.
    - Store the parent object to access object count

    It is used in the `MetadataBox` to present tag information for multiple selected
    files, tracks, or albums.

    Example:
        >>> parent = TagDiff()
        >>> parent.objects = 3
        >>> counter = parent.new  # TagCounter object
        >>> counter.add("artist", ["Artist 1"])
        >>> counter.add("artist", ["Artist 1"])
        >>> counter.display_value("artist").text
        'Artist 1'
        >>> counter.add("artist", ["Artist 2"])
        >>> counter.display_value("artist").text
        '(different across 3 items)'
        >>> counter.add("album", ["Album 1"])
        >>> counter.display_value("album").text
        'Album 1 (missing from 2 items)'

    """

    __slots__ = ('parent', 'counts', 'different')

    def __init__(self, parent):
        """
        Initializes the TagCounter.

        Args:
            parent: The parent `TagDiff` object that this counter is associated with.
                    It is used to access the total number of objects being compared.
        """
        self.parent = parent
        self.counts = Counter()
        self.different = set()

    def __getitem__(self, tag):
        """
        Retrieves the value associated with a tag.

        If the tag is not found, it returns a list containing an empty string [""]
        instead of raising a KeyError.

        Args:
            tag: The tag name (string).

        Returns:
            The value associated with the tag, or [""] if the tag is not found.
        """
        return super().get(tag, [""])

    def add(self, tag, values):
        """
        Adds tag information to the counter.

        It tracks the number of times the tag is added and determines whether
        the tag's values differ across objects.

        Args:
            tag: The tag name (string).
            values: The value(s) associated with the tag (list or string).
        """
        if tag not in self.different:
            if tag not in self:
                self[tag] = values
            elif self[tag] != values:
                self.different.add(tag)
                self[tag] = [""]
        self.counts[tag] += 1

    def display_value(self, tag):
        """
        Generates a user-friendly text representation of the tag's value.

        It takes into account whether the tag has different values across
        objects, whether it is missing from some objects, and special formatting
        for the '~length' tag.

        Args:
            tag: The tag name (string).

        Returns:
            A TagCounterDisplayValue namedtuple containing:
                - text: The display text for the tag.
                - is_grouped: A boolean indicating whether the tag has different
                              values or is missing from some objects.
        """
        count = self.counts[tag]
        missing = self.parent.objects - count

        if tag in self.different:
            text = ngettext("(different across %d item)", "(different across %d items)", count) % count
            is_grouped = True
        else:
            if tag == '~length':
                msg = format_time(self.get(tag, 0))
            else:
                msg = MULTI_VALUED_JOINER.join(self[tag])

            if count > 0 and missing > 0:
                text = msg + " " + (ngettext("(missing from %d item)", "(missing from %d items)", missing) % missing)
                is_grouped = True
            else:
                text = msg
                is_grouped = False

        return TagCounterDisplayValue(text, is_grouped)


class TagDiff:
    """
    Tracks the differences between original and new tag values across multiple objects.

    This class manages the comparison of tag values for a set of files, tracks,
    or albums. It tracks whether tags have been added, removed, changed, or
    remain unchanged. It also handles special cases like the '~length' tag
    for track duration and supports read-only and non-removable tags.

    Attributes:
        tag_names (list): A list of tag names being tracked, determining display order.
        new (TagCounter): A TagCounter instance holding the new tag values.
        orig (TagCounter): A TagCounter instance holding the original tag values.
        status (defaultdict): A dictionary mapping tag names to their TagStatus.
        objects (int): The number of objects being compared.
        max_length_delta_ms (int): The maximum allowed length difference (in ms) for
                                   tracks to be considered the same.

    """

    __slots__ = ('tag_names', 'new', 'orig', 'status', 'objects', 'max_length_delta_ms')

    def __init__(self, max_length_diff=2):
        """
        Initializes the TagDiff.

        Args:
            max_length_diff (int): The maximum allowed length difference (in seconds)
                                   for tracks to be considered the same.
        """
        self.tag_names = []
        self.new = TagCounter(self)
        self.orig = TagCounter(self)
        self.status = defaultdict(lambda: TagStatus.NONE)
        self.objects = 0
        self.max_length_delta_ms = max_length_diff * 1000

    def __tag_ne(self, tag, orig, new):
        """
        Checks if two tag values are not equal, handling the special case of '~length'.

        Args:
            tag: The tag name (string).
            orig: The original tag value.
            new: The new tag value.

        Returns:
            True if the tag values are not equal, False otherwise.
        """
        if tag == '~length':
            return abs(float(orig) - float(new)) > self.max_length_delta_ms
        else:
            return orig != new

    def is_readonly(self, tag):
        """
        Checks if a tag is read-only.

        Args:
            tag: The tag name (string).

        Returns:
            True if the tag is read-only, False otherwise.
        """
        return bool(self.status[tag] & TagStatus.READONLY)

    def add(self, tag, orig_values, new_values, removable, removed=False, readonly=False, top_tags=None):
        """
        Adds tag information to the TagDiff and updates its status.

        Args:
            tag: The tag name (string).
            orig_values: The original tag value(s).
            new_values: The new tag value(s).
            removable (bool): Whether the tag can be removed.
            removed (bool): Whether the tag was marked as removed.
            readonly (bool): Whether the tag is read-only.
            top_tags (set): Set of top level tags
        """
        if orig_values:
            self.orig.add(tag, orig_values)

        if new_values:
            self.new.add(tag, new_values)

        if not top_tags:
            top_tags = set()

        if (orig_values and not new_values) or removed:
            self.status[tag] |= TagStatus.REMOVED
        elif new_values and not orig_values:
            self.status[tag] |= TagStatus.ADDED
            removable = True
        elif orig_values and new_values and self.__tag_ne(tag, orig_values, new_values):
            self.status[tag] |= TagStatus.CHANGED
        elif not (orig_values or new_values or tag in top_tags):
            self.status[tag] |= TagStatus.EMPTY
        else:
            self.status[tag] |= TagStatus.NOCHANGE

        if not removable:
            self.status[tag] |= TagStatus.NOTREMOVABLE

        if readonly:
            self.status[tag] |= TagStatus.READONLY

    def tag_status(self, tag):
        """
        Gets the specific status of a tag.

        Checks for the flags CHANGED, ADDED, REMOVED, and EMPTY in that order
        and return the first one found.

        Args:
            tag: The tag name (string).

        Returns:
            The tag's TagStatus.
        """
        status = self.status[tag]
        for s in (TagStatus.CHANGED, TagStatus.ADDED,
                  TagStatus.REMOVED, TagStatus.EMPTY):
            if status & s == s:
                return s
        return TagStatus.NOCHANGE
