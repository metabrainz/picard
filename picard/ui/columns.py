# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012 Lukáš Lalinský
# Copyright (C) 2007 Robert Kaye
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008-2011, 2014-2015, 2018-2024 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011 Tim Blechmann
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Your Name
# Copyright (C) 2012-2013 Wieland Hoffmann
# Copyright (C) 2013-2014, 2016, 2018-2025 Laurent Monin
# Copyright (C) 2013-2014, 2017, 2020 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Louis Sautier
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2023 certuna
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Suryansh Shakya
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


from collections.abc import MutableSequence
from enum import IntEnum

from PyQt6 import QtCore


class ColumnAlign(IntEnum):
    LEFT = 0
    RIGHT = 1

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f'{cls_name}.{self.name}'


class ColumnSortType(IntEnum):
    TEXT = 0
    NAT = 1
    SORTKEY = 2  # special case, use sortkey property

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f'{cls_name}.{self.name}'


class Column:
    is_icon = False
    is_default = False

    def __init__(self, title, key, size=None, align=ColumnAlign.LEFT, sort_type=ColumnSortType.TEXT, sortkey=None):
        self.title = title
        self.key = key
        self.size = size
        self.align = align
        self.sort_type = sort_type
        if self.sort_type == ColumnSortType.SORTKEY:
            if not callable(sortkey):
                raise TypeError("sortkey should be a callable")
            self.sortkey = sortkey
        else:
            self.sortkey = None

    def __repr__(self):
        def parms():
            yield from (repr(getattr(self, a)) for a in ('title', 'key'))
            yield from (a + '=' + repr(getattr(self, a)) for a in ('size', 'align', 'sort_type', 'sortkey'))

        return 'Column(' + ', '.join(parms()) + ')'

    def __str__(self):
        return repr(self)


class DefaultColumn(Column):
    is_default = True


class IconColumn(Column):
    is_icon = True
    _header_icon = None
    header_icon_func = None
    header_icon_size = QtCore.QSize(0, 0)
    header_icon_border = 0
    header_icon_size_with_border = QtCore.QSize(0, 0)

    @property
    def header_icon(self):
        # icon cannot be set before QApplication is created
        # so create it during runtime and cache it
        # Avoid error: QPixmap: Must construct a QGuiApplication before a QPixmap
        if self._header_icon is None:
            self._header_icon = self.header_icon_func()
        return self._header_icon

    def set_header_icon_size(self, width, height, border):
        self.header_icon_size = QtCore.QSize(width, height)
        self.header_icon_border = border
        self.header_icon_size_with_border = QtCore.QSize(width + 2*border, height + 2*border)

    def paint_icon(self, painter, rect):
        icon = self.header_icon
        if not icon:
            return
        h = self.header_icon_size.height()
        w = self.header_icon_size.width()
        border = self.header_icon_border
        padding_v = (rect.height() - h) // 2
        target_rect = QtCore.QRect(
            rect.x() + border, rect.y() + padding_v,
            w, h
        )
        painter.drawPixmap(target_rect, icon.pixmap(self.header_icon_size))


class Columns(MutableSequence):
    def __init__(self, iterable=None):
        self._list = list()
        self._index = dict()
        self._index_dirty = True
        if iterable is not None:
            for e in iterable:
                self.append(e)

    def __len__(self):
        return len(self._list)

    def __delitem__(self, index):
        self._index_dirty = True
        self._list.__delitem__(index)

    def insert(self, index, column):
        if not isinstance(column, Column):
            raise TypeError("Not an instance of Column")
        self._list.insert(index, column)
        self._index_dirty = True

    def __setitem__(self, index, column):
        if not isinstance(column, Column):
            raise TypeError("Not an instance of Column")
        self._list.__setitem__(index, column)
        self._index_dirty = True

    def __getitem__(self, index):
        return self._list.__getitem__(index)

    def pos(self, key):
        if self._index_dirty:
            self._index = {c.key: i for i, c in enumerate(self._list)}
            self._index_dirty = False
        return self._index[key]

    def __repr__(self):
        return "Columns([\n" + "".join("    %r,\n" % e for e in self._list) + '])'

    def __str__(self):
        return repr(self)
