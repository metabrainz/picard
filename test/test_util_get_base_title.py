# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
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

from picard.util import get_base_title_with_suffix


class GetBaseTitle(PicardTestCase):
    @subtest_cases(
        "title,suffix,expected",
        {
            'no matching suffix': ('title', '(copy)', 'title'),
            'matching suffix but no number section': ('title (copy)', '(copy)', 'title'),
            'matching suffix and number': ('title (copy) (1)', '(copy)', 'title'),
            'missing space between suffix and number': ('title (copy)(1)', '(copy)', 'title (copy)(1)'),
            'missing space and missing number': ('title (copy)()', '(copy)', 'title (copy)()'),
            'missing number': ('title (copy) ()', '(copy)', 'title'),
            'invalid number': ('title (copy) (x)', '(copy)', 'title (copy) (x)'),
            'extra character after number section': ('title (copy) (1)x', '(copy)', 'title (copy) (1)x'),
            'suffix is escaped': ('title (copy) (1)', '(c?py)', 'title (copy)'),
        },
    )
    def test_base_title_with_title_first_format(self, title, suffix, expected):
        self.assertEqual(get_base_title_with_suffix(title, suffix, '{title} ({count})'), expected)

    @subtest_cases(
        "title,suffix,expected",
        {
            'matching suffix but no number section': ('title (copy)', '(copy)', 'title'),
            'number section in wrong location': ('title (copy) (1)', '(copy)', 'title (copy) (1)'),
            'matching suffix and number section': ('(1) title (copy)', '(copy)', 'title'),
            'additional characters after suffix': ('(1) title (copy) (1)', '(copy)', 'title (copy) (1)'),
        },
    )
    def test_base_title_with_count_first_format(self, title, suffix, expected):
        self.assertEqual(get_base_title_with_suffix(title, suffix, '({count}) {title}'), expected)
