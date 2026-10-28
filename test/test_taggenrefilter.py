# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Wieland Hoffmann
# Copyright (C) 2019-2022, 2025 Laurent Monin
# Copyright (C) 2020-2021, 2024 Philipp Wolfer
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


from collections import Counter

from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

from picard.track import TagGenreFilter


class TagGenreFilterSkipTest(PicardTestCase):
    # Recurring multi-rule filter sets, reused across the skip() cases below.
    # TagGenreFilter strips each line, so the indentation here is irrelevant.
    WILDCARD_ALL_BUT_BLUES = """
        -*
        +blues
    """
    WILDCARD_PATTERNS = """
        -jazz*
        -*rock
        -*disco*
        -a*b
    """
    REGEX_PATTERNS = """
        -/^j.zz/
        -/r[io]ck$/
        -/disco+/
        +/discoooo/
    """
    REGEX_PATTERNS_KEEP_ALL = """
        -/^j.zz/
        -/r[io]ck$/
        -/disco+/
        +/discoooo/
        +/.*/
    """
    UPPERCASED_PATTERNS = """
        -JAZZ*
        -ROCK
        -/^DISCO$/
    """
    WHITESPACE_PATTERNS = """
        - jazz b*
        - * ro ck
        - /^di sco$/
    """

    @subtest_cases(
        "filters,tag,expected_skip",
        {
            'no filter (comment only)': ("# comment", 'jazz', False),
            'strict filter': ("-jazz", 'jazz', True),
            'strict filter allowlist': ("+jazz\n-jazz", 'jazz', False),
            'strict filter allowlist reverse order': ("-jazz\n+jazz", 'jazz', False),
            'wildcard all-but skips jazz': (WILDCARD_ALL_BUT_BLUES, 'jazz', True),
            'wildcard all-but skips rock': (WILDCARD_ALL_BUT_BLUES, 'rock', True),
            'wildcard all-but keeps blues': (WILDCARD_ALL_BUT_BLUES, 'blues', False),
            'wildcard prefix jazz': (WILDCARD_PATTERNS, 'jazz', True),
            'wildcard prefix jazz blues': (WILDCARD_PATTERNS, 'jazz blues', True),
            'wildcard prefix blues jazz': (WILDCARD_PATTERNS, 'blues jazz', False),
            'wildcard suffix rock': (WILDCARD_PATTERNS, 'rock', True),
            'wildcard suffix blues rock': (WILDCARD_PATTERNS, 'blues rock', True),
            'wildcard suffix rock blues': (WILDCARD_PATTERNS, 'rock blues', False),
            'wildcard contains disco': (WILDCARD_PATTERNS, 'disco', True),
            'wildcard contains xdisco': (WILDCARD_PATTERNS, 'xdisco', True),
            'wildcard contains discox': (WILDCARD_PATTERNS, 'discox', True),
            'wildcard a*b ab': (WILDCARD_PATTERNS, 'ab', True),
            'wildcard a*b axb': (WILDCARD_PATTERNS, 'axb', True),
            'wildcard a*b axxb': (WILDCARD_PATTERNS, 'axxb', True),
            'wildcard a*b xab': (WILDCARD_PATTERNS, 'xab', False),
            'regex jazz': (REGEX_PATTERNS, 'jazz', True),
            'regex jizz': (REGEX_PATTERNS, 'jizz', True),
            'regex jazz blues': (REGEX_PATTERNS, 'jazz blues', True),
            'regex blues jazz': (REGEX_PATTERNS, 'blues jazz', False),
            'regex rock': (REGEX_PATTERNS, 'rock', True),
            'regex blues rock': (REGEX_PATTERNS, 'blues rock', True),
            'regex blues rick': (REGEX_PATTERNS, 'blues rick', True),
            'regex rock blues': (REGEX_PATTERNS, 'rock blues', False),
            'regex disco': (REGEX_PATTERNS, 'disco', True),
            'regex xdiscox': (REGEX_PATTERNS, 'xdiscox', True),
            'regex xdiscooox': (REGEX_PATTERNS, 'xdiscooox', True),
            'regex xdiscoooox allowlisted': (REGEX_PATTERNS, 'xdiscoooox', False),
            'uppercased filter jazz blues': (UPPERCASED_PATTERNS, 'jazz blues', True),
            'uppercased filter JAZZ BLUES': (UPPERCASED_PATTERNS, 'JAZZ BLUES', True),
            'uppercased filter rock': (UPPERCASED_PATTERNS, 'rock', True),
            'uppercased filter ROCK': (UPPERCASED_PATTERNS, 'ROCK', True),
            'uppercased filter disco': (UPPERCASED_PATTERNS, 'disco', True),
            'uppercased filter DISCO': (UPPERCASED_PATTERNS, 'DISCO', True),
            'whitespaces jazz blues': (WHITESPACE_PATTERNS, 'jazz blues', True),
            'whitespaces blues ro ck': (WHITESPACE_PATTERNS, 'blues ro ck', True),
            'whitespaces di sco': (WHITESPACE_PATTERNS, 'di sco', True),
            'whitespaces bluesro ck': (WHITESPACE_PATTERNS, 'bluesro ck', False),
        },
    )
    def test_skip(self, filters, tag, expected_skip):
        tag_filter = TagGenreFilter(filters)
        self.assertEqual(expected_skip, tag_filter.skip(tag))

    @subtest_cases(
        "filters,tags",
        {
            # the regex patterns above, but a trailing +/.*/ allowlists everything
            'regex keep all': (
                REGEX_PATTERNS_KEEP_ALL,
                (
                    'jazz',
                    'jizz',
                    'jazz blues',
                    'blues jazz',
                    'rock',
                    'blues rock',
                    'blues rick',
                    'rock blues',
                    'disco',
                    'xdiscox',
                    'xdiscooox',
                    'xdiscoooox',
                ),
            ),
        },
    )
    def test_skip_none(self, filters, tags):
        tag_filter = TagGenreFilter(filters)
        for tag in tags:
            self.assertFalse(tag_filter.skip(tag), f"expected {tag!r} not to be skipped")


class TagGenreFilterMethodTest(PicardTestCase):
    @subtest_cases(
        "filters,genres,expected",
        {
            'drops a* prefix': ("-a*", Counter(ax=1, bx=2, ay=3, by=4), [('bx', 2), ('by', 4)]),
            'empty input': ("", Counter(), []),
            'empty result (deny all)': ("-*", Counter(ax=1, bx=2, ay=3, by=4), []),
        },
    )
    def test_filter(self, filters, genres, expected):
        tag_filter = TagGenreFilter(filters)
        result = tag_filter.filter(genres)
        self.assertEqual(expected, list(result.items()))

    def test_filter_minusage_drops_low_usage_genres(self):
        tag_filter = TagGenreFilter("-a*")
        genres = Counter(ax=4, bx=5, ay=20, by=10, bz=4)
        result = tag_filter.filter(genres, minusage=50)
        self.assertEqual([('bx', 5), ('by', 10)], list(result.items()))
