# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Philipp Wolfer
# Copyright (C) 2021-2022, 2025 Laurent Monin
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


from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

from picard.util import (
    _regex_numbered_title_fmt,
    unique_numbered_title,
)


class RegexNumberedTitleFmt(PicardTestCase):
    @subtest_cases(
        "fmt,expected",
        {
            'empty': ('', ''),
            'title then count': ('{title} {count}', r'TITLE(?:\ COUNT)?'),
            'count before title': ('x {count}  {title} y', r'(?:x\ COUNT\ \ )?TITLE y'),
            'count after title': ('x {title}{count} y', r'x TITLE(?:COUNT\ y)?'),
        },
    )
    def test_regex_numbered_title_fmt(self, fmt, expected):
        self.assertEqual(expected, _regex_numbered_title_fmt(fmt, 'TITLE', 'COUNT'))


class UniqueNumberedTitle(PicardTestCase):
    @subtest_cases(
        "existing,expected",
        {
            'no existing': ([], 'title (1)'),
            'one existing': (['title'], 'title (2)'),
            'existing with number': (['title', 'title (2)'], 'title (3)'),
            'two numbered': (['title (1)', 'title (2)'], 'title (3)'),
            'duplicates': (['title', 'title'], 'title (3)'),
            'non-matching neighbours': (['x title', 'title y'], 'title (1)'),
            'non-numeric count': (['title (n)'], 'title (1)'),
            'empty count': (['title ()'], 'title (1)'),
            'no separator': (['title(2)'], 'title (1)'),
        },
    )
    def test_unique_numbered_title_suffix(self, existing, expected):
        self.assertEqual(expected, unique_numbered_title('title', existing, fmt='{title} ({count})'))

    @subtest_cases(
        "existing,expected",
        {
            'no existing': ([], '(1) title'),
            'one existing': (['title'], '(2) title'),
            'existing with number': (['title', '(2) title'], '(3) title'),
            'two numbered': (['(1) title', '(2) title'], '(3) title'),
            'duplicates': (['title', 'title'], '(3) title'),
            'non-matching neighbours': (['x title', 'title y'], '(1) title'),
            'non-numeric count': (['(n) title'], '(1) title'),
            'empty count': (['() title'], '(1) title'),
            'no separator': (['(2)title'], '(1) title'),
        },
    )
    def test_unique_numbered_title_prefix(self, existing, expected):
        self.assertEqual(expected, unique_numbered_title('title', existing, fmt='({count}) {title}'))
