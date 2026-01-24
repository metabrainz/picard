# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Laurent Monin
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


from test.picardtestcase import PicardTestCase

from picard.ui.columns import (
    Column,
    ColumnAlign,
    Columns,
    ColumnSortType,
    DefaultColumn,
    ImageColumn,
)
from picard.ui.itemviews.custom_columns import IconColumn


class ColumnTest(PicardTestCase):
    def test_init_simple_column(self):
        column = Column('title', 'key')
        self.assertEqual(column.title, 'title')
        self.assertEqual(column.key, 'key')
        self.assertFalse(column.is_default)
        self.assertEqual(column.align, ColumnAlign.LEFT)
        self.assertEqual(column.sort_type, ColumnSortType.TEXT)
        self.assertFalse(column.always_visible)
        self.assertFalse(column.status_icon)
        self.assertIsNone(column.sortkey)
        expected_repr = (
            "Column('title', 'key', width=None, align=ColumnAlign.LEFT, "
            "sort_type=ColumnSortType.TEXT, sortkey=None, always_visible=False, status_icon=False, "
            "column_group=ColumnGroupItem(index=99, title='Custom Columns'))"
        )
        self.assertEqual(repr(column), expected_repr)
        self.assertEqual(str(column), expected_repr)

    def test_init_column_align_sort_type(self):
        def dummy():
            pass

        column = Column('title', 'key', align=ColumnAlign.RIGHT, sort_type=ColumnSortType.SORTKEY, sortkey=dummy)
        self.assertEqual(column.align, ColumnAlign.RIGHT)
        self.assertEqual(column.sort_type, ColumnSortType.SORTKEY)
        self.assertEqual(column.sortkey, dummy)

    def test_init_column_invalid_sortkey(self):
        with self.assertRaisesRegex(TypeError, 'sortkey should be a callable'):
            Column('title', 'key', align=ColumnAlign.RIGHT, sort_type=ColumnSortType.SORTKEY, sortkey='invalid')

    def test_default_column(self):
        column = DefaultColumn('title', 'key')
        self.assertTrue(column.is_default)

    def test_icon_column(self):
        class _Provider:
            def __init__(self):
                self._icon = None

            def get_icon(self):
                if self._icon is None:
                    self._icon = 'icon'
                return self._icon

        provider = _Provider()
        column = IconColumn('title', 'key', provider)
        self.assertIsInstance(column, ImageColumn)
        self.assertEqual(column.header_icon, 'icon')
        column.set_header_icon_size(10, 20, 2)
        self.assertEqual(column.header_icon_size.width(), 10)
        self.assertEqual(column.header_icon_size.height(), 20)
        self.assertEqual(column.width, 14)
        self.assertEqual(
            repr(column),
            "IconColumn('title', 'key', width=14, align=ColumnAlign.LEFT, "
            "sort_type=ColumnSortType.TEXT, sortkey=None, always_visible=False, status_icon=False, "
            "column_group=ColumnGroupItem(index=4, title='Miscellaneous'))",
        )


class ColumnsTest(PicardTestCase):
    def test_init_columns(self):
        c1 = Column('t1', 'k1', width=50)
        c2 = Column('t2', 'k2', always_visible=True)
        c3 = Column('t3', 'k3', status_icon=True)
        columns = Columns([c1, c2])
        self.assertEqual(columns[0], c1)
        self.assertEqual(columns[1], c2)
        self.assertEqual(len(columns), 2)
        self.assertEqual(columns.pos('k2'), 1)
        self.assertEqual(columns.get_column_by_key('k2'), (1, c2))

        self.assertEqual(columns[0].width, 50)
        self.assertEqual(columns[1].width, None)

        columns = Columns([c1, c2], default_width=100)
        self.assertEqual(columns[0].width, 50)
        self.assertEqual(columns[1].width, 100)

        columns.append(c3)
        self.assertEqual(columns[2], c3)
        self.assertEqual(len(columns), 3)
        self.assertEqual(columns.pos('k3'), 2)

        del columns[0]
        self.assertEqual(columns[0], c2)
        self.assertEqual(len(columns), 2)
        self.assertEqual(columns.pos('k3'), 1)

        expected_repr = """Columns([
    Column('t2', 'k2', width=100, align=ColumnAlign.LEFT, sort_type=ColumnSortType.TEXT, sortkey=None, always_visible=True, status_icon=False, column_group=ColumnGroupItem(index=99, title='Custom Columns')),
    Column('t3', 'k3', width=100, align=ColumnAlign.LEFT, sort_type=ColumnSortType.TEXT, sortkey=None, always_visible=False, status_icon=True, column_group=ColumnGroupItem(index=99, title='Custom Columns')),
])"""
        self.assertEqual(repr(columns), expected_repr)
        self.assertEqual(str(columns), expected_repr)
        self.assertEqual(columns.status_icon_column, 2)
        self.assertEqual(tuple(columns.always_visible_columns()), (0,))

    def test_append_non_column(self):
        columns = Columns()
        with self.assertRaisesRegex(TypeError, "^Not an instance of Column$"):
            columns.append('x')

    def test_set_non_column(self):
        columns = Columns([Column('t1', 'k1')])
        with self.assertRaisesRegex(TypeError, "^Not an instance of Column$"):
            columns[0] = 'x'

    def test_more_than_one_status_icon(self):
        c1 = Column('t1', 'k1', status_icon=True)
        c2 = Column('t2', 'k2', status_icon=True)
        with self.assertRaisesRegex(TypeError, "^Only one status icon column is supported$"):
            columns = Columns([c1, c2])
            self.assertEqual(tuple(columns), (c1,))
