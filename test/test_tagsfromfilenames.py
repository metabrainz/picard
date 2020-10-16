# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Philipp Wolfer
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

from picard.ui.tagsfromfilenames import TagMatchExpression


class TagMatchExpressionTest(PicardTestCase):

    def test_parse_tags(self):
        expression = TagMatchExpression(r'%tracknumber% - %title%')
        expected_tags = ['tracknumber', 'title']
        self.assertEqual(expected_tags, expression.matched_tags)
        files = [
            '042 - The Title',
            '042 - The Title.mp3',
            '/foo/042 - The Title'
            '/foo/042 - The Title.mp3'
            '/042 - The Title'
            '/042 - The Title.mp3'
            'C:\\foo\\042 - The Title.mp3'
        ]
        for filename in files:
            matches = expression.match_file(filename)
            self.assertEqual(['42'], matches['tracknumber'])
            self.assertEqual(['The Title'], matches['title'])

    def test_parse_tags_with_path(self):
        expression = TagMatchExpression(r'%artist%/%album%/%tracknumber% - %title%')
        expected_tags = ['artist', 'album', 'tracknumber', 'title']
        self.assertEqual(expected_tags, expression.matched_tags)
        files = [
            'The Artist/The Album/01 - The Title',
            'The Artist/The Album/01 - The Title.wv',
            'C:\\foo\\The Artist\\The Album\\01 - The Title.wv',
        ]
        for filename in files:
            matches = expression.match_file(filename)
            self.assertEqual(['The Artist'], matches['artist'])
            self.assertEqual(['The Album'], matches['album'])
            self.assertEqual(['1'], matches['tracknumber'])
            self.assertEqual(['The Title'], matches['title'])

    def test_parse_replace_underscores(self):
        expression = TagMatchExpression(r'%artist%-%title%', replace_underscores=True)
        matches = expression.match_file('Some_Artist-Some_Title.ogg')
        self.assertEqual(['Some Artist'], matches['artist'])
        self.assertEqual(['Some Title'], matches['title'])

    def test_parse_tags_duplicates(self):
        expression = TagMatchExpression(r'%dummy% %title% %dummy%')
        expected_tags = ['dummy', 'title']
        self.assertEqual(expected_tags, expression.matched_tags)
        matches = expression.match_file('foo title bar')
        self.assertEqual(['title'], matches['title'])
        self.assertEqual(['foo', 'bar'], matches['dummy'])

    def test_parse_tags_hidden(self):
        expression = TagMatchExpression(r'%_dummy% %title% %_dummy%')
        expected_tags = ['~dummy', 'title']
        self.assertEqual(expected_tags, expression.matched_tags)
        matches = expression.match_file('foo title bar')
        self.assertEqual(['title'], matches['title'])
        self.assertEqual(['foo', 'bar'], matches['~dummy'])

    def test_parse_empty(self):
        expression = TagMatchExpression(r'')
        expected_tags = []
        self.assertEqual(expected_tags, expression.matched_tags)
