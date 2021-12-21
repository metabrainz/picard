# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Laurent Monin
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

from picard.util import (
    _regex_numbered_title_fmt,
    unique_numbered_title,
)


class RegexNumberedTitleFmt(PicardTestCase):

    def test_1(self):
        fmt = ''
        result = _regex_numbered_title_fmt(fmt, 'TITLE', 'COUNT')
        self.assertEqual(result, '')

    def test_2(self):
        fmt = '{title} {count}'
        result = _regex_numbered_title_fmt(fmt, 'TITLE', 'COUNT')
        self.assertEqual(result, r'TITLE(?:\ COUNT)?')

    def test_3(self):
        fmt = 'x {count}  {title} y'
        result = _regex_numbered_title_fmt(fmt, 'TITLE', 'COUNT')
        self.assertEqual(result, r'(?:x\ COUNT\ \ )?TITLE y')

    def test_4(self):
        fmt = 'x {title}{count} y'
        result = _regex_numbered_title_fmt(fmt, 'TITLE', 'COUNT')
        self.assertEqual(result, r'x TITLE(?:COUNT\ y)?')


class UniqueNumberedTitle(PicardTestCase):
    def test_existing_titles_0(self):
        title = unique_numbered_title('title', [], fmt='{title} ({count})')
        self.assertEqual(title, 'title (1)')

    def test_existing_titles_1(self):
        title = unique_numbered_title('title', ['title'], fmt='{title} ({count})')
        self.assertEqual(title, 'title (2)')

    def test_existing_titles_2(self):
        title = unique_numbered_title('title', ['title', 'title (2)'], fmt='{title} ({count})')
        self.assertEqual(title, 'title (3)')

    def test_existing_titles_3(self):
        title = unique_numbered_title('title', ['title (1)', 'title (2)'], fmt='{title} ({count})')
        self.assertEqual(title, 'title (3)')

    def test_existing_titles_4(self):
        title = unique_numbered_title('title', ['title', 'title'], fmt='{title} ({count})')
        self.assertEqual(title, 'title (3)')

    def test_existing_titles_5(self):
        title = unique_numbered_title('title', ['x title', 'title y'], fmt='{title} ({count})')
        self.assertEqual(title, 'title (1)')

    def test_existing_titles_6(self):
        title = unique_numbered_title('title', ['title (n)'], fmt='{title} ({count})')
        self.assertEqual(title, 'title (1)')

    def test_existing_titles_7(self):
        title = unique_numbered_title('title', ['title ()'], fmt='{title} ({count})')
        self.assertEqual(title, 'title (1)')

    def test_existing_titles_8(self):
        title = unique_numbered_title('title', ['title(2)'], fmt='{title} ({count})')
        self.assertEqual(title, 'title (1)')


class UniqueNumberedTitleFmt(PicardTestCase):
    def test_existing_titles_0(self):
        title = unique_numbered_title('title', [], fmt='({count}) {title}')
        self.assertEqual(title, '(1) title')

    def test_existing_titles_1(self):
        title = unique_numbered_title('title', ['title'], fmt='({count}) {title}')
        self.assertEqual(title, '(2) title')

    def test_existing_titles_2(self):
        title = unique_numbered_title('title', ['title', '(2) title'], fmt='({count}) {title}')
        self.assertEqual(title, '(3) title')

    def test_existing_titles_3(self):
        title = unique_numbered_title('title', ['(1) title', '(2) title'], fmt='({count}) {title}')
        self.assertEqual(title, '(3) title')

    def test_existing_titles_4(self):
        title = unique_numbered_title('title', ['title', 'title'], fmt='({count}) {title}')
        self.assertEqual(title, '(3) title')

    def test_existing_titles_5(self):
        title = unique_numbered_title('title', ['x title', 'title y'], fmt='({count}) {title}')
        self.assertEqual(title, '(1) title')

    def test_existing_titles_6(self):
        title = unique_numbered_title('title', ['(n) title'], fmt='({count}) {title}')
        self.assertEqual(title, '(1) title')

    def test_existing_titles_7(self):
        title = unique_numbered_title('title', ['() title'], fmt='({count}) {title}')
        self.assertEqual(title, '(1) title')

    def test_existing_titles_8(self):
        title = unique_numbered_title('title', ['(2)title'], fmt='({count}) {title}')
        self.assertEqual(title, '(1) title')
