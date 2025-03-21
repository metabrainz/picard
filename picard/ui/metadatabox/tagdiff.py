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
from picard.util.tags import display_tag_name


class TagStatus:
    NONE = 0
    UNCHANGED = 1
    ADDED = 2
    REMOVED = 4
    CHANGED = ADDED | REMOVED
    EMPTY = 8
    NOTREMOVABLE = 16
    READONLY = 32


TagCounterDisplayValue = namedtuple('TagCounterDisplayValue', ('text', 'is_grouped'))
TagCounterStatus = namedtuple('TagCounterStatus', ('is_grouped', 'count', 'is_different', 'missing'))


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

    def status(self, tag):
        """
        Returns tag status as a named tuple TagCounterStatus

        Args:
            tag: The tag name (string).

        Returns:
            The status (TagCounterStatus),
        """
        count = self.counts[tag]
        missing = self.parent.objects - count
        is_different = tag in self.different
        is_grouped = is_different or (count > 0 and missing > 0)
        return TagCounterStatus(is_grouped, count, is_different, missing)

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
        status = self.status(tag)

        if status.is_different:
            text = ngettext("(different across %d item)", "(different across %d items)", status.count) % status.count
        else:
            if tag == '~length':
                text = format_time(self.get(tag, 0))
            else:
                text = MULTI_VALUED_JOINER.join(self[tag])

            if status.is_grouped:
                text += " " + (ngettext("(missing from %d item)", "(missing from %d items)", status.missing) % status.missing)

        return TagCounterDisplayValue(text, status.is_grouped)


class TagDiff:
    """
    Tracks the differences between old and new tag values across multiple objects.

    This class manages the comparison of tag values for a set of files, tracks,
    or albums. It tracks whether tags have been added, removed, changed, or
    remain unchanged. It also handles special cases like the '~length' tag
    for track duration and supports read-only and non-removable tags.

    Attributes:
        tag_names (list): A list of tag names being tracked, determining display order.
        new (TagCounter): A TagCounter instance holding the new tag values.
        old (TagCounter): A TagCounter instance holding the old tag values.
        status (defaultdict): A dictionary mapping tag names to their TagStatus.
        objects (int): The number of objects being compared.
        max_length_delta_ms (int): The maximum allowed length difference (in ms) for
                                   tracks to be considered the same.

    """

    __slots__ = ('tag_names', 'new', 'old', 'status', 'objects', 'tag_ne_handlers')

    def __init__(self, max_length_diff=2):
        """
        Initializes the TagDiff.

        Args:
            max_length_diff (int): The maximum allowed length difference (in seconds)
                                   for tracks to be considered the same.
        """
        self.tag_names = []
        self.new = TagCounter(self)
        self.old = TagCounter(self)
        self.status = defaultdict(lambda: TagStatus.NONE)
        self.objects = 0
        self.tag_ne_handlers = defaultdict(lambda: lambda old, new: old != new)
        # handling the special case of '~length'
        max_length_delta_ms = max_length_diff * 1000
        self.tag_ne_handlers['~length'] = lambda old, new: abs(int(old) - int(new)) > max_length_delta_ms

    def __tag_ne(self, tag, old, new):
        """
        Checks if two tag values are not equal.

        Args:
            tag: The tag name (string).
            old: The old tag value.
            new: The new tag value.

        Returns:
            True if the tag values are not equal, False otherwise.
        """
        return self.tag_ne_handlers[tag](old, new)

    def is_readonly(self, tag):
        """
        Checks if a tag is read-only.

        Args:
            tag: The tag name (string).

        Returns:
            True if the tag is read-only, False otherwise.
        """
        return bool(self.status[tag] & TagStatus.READONLY)

    def add(self, tag, old=None, new=None, removable=True, removed=False, readonly=False, top_tags=None):
        """
        Adds tag information to the TagDiff and updates its status.

        Args:
            tag: The tag name (string).
            old: The old tag value(s).
            new: The new tag value(s).
            removable (bool): Whether the tag can be removed.
            removed (bool): Whether the tag was marked as removed.
            readonly (bool): Whether the tag is read-only.
            top_tags (set): Set of top level tags
        """
        if old:
            self.old.add(tag, old)

        if new:
            self.new.add(tag, new)

        if not top_tags:
            top_tags = set()

        if (old and not new) or removed:
            self.status[tag] |= TagStatus.REMOVED
        elif new and not old:
            self.status[tag] |= TagStatus.ADDED
            removable = True
        elif old and new and self.__tag_ne(tag, old, new):
            self.status[tag] |= TagStatus.CHANGED
        elif not (old or new or tag in top_tags):
            self.status[tag] |= TagStatus.EMPTY
        else:
            self.status[tag] |= TagStatus.UNCHANGED

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
        return TagStatus.UNCHANGED

    def update_tag_names(self, changes_first=False, top_tags=None):
        """
        Updates the list of tag names to be displayed.

        The tag names are sorted based on their name with the top_tags, and optionally
        the changed tags, first.

        Args:
            changes_first (bool): Whether to display changed tags first.
            top_tags (set): Set of tags to always be displayed at the top.
        """
        all_tags = set(list(self.old) + list(self.new))
        common_tags = [tag for tag in top_tags if tag in all_tags] if top_tags else []
        tag_names = common_tags + sorted(all_tags.difference(common_tags),
                                         key=lambda x: display_tag_name(x).lower())

        if changes_first:
            tags_by_status = {}

            for tag in tag_names:
                tags_by_status.setdefault(self.tag_status(tag), []).append(tag)

            for status in (TagStatus.CHANGED, TagStatus.ADDED,
                           TagStatus.REMOVED, TagStatus.UNCHANGED):
                self.tag_names += tags_by_status.pop(status, [])
        else:
            self.tag_names = [
                tag for tag in tag_names if
                self.status[tag] != TagStatus.EMPTY]
