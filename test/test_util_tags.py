# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020 Philipp Wolfer
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

from picard.util.tags import (
    create_lang_desc_tag,
    display_tag_name,
    parse_comment_tag,
    parse_lang_desc_tag,
)


class UtilTagsTest(PicardTestCase):
    def test_display_tag_name(self):
        self.assertEqual('Artist', display_tag_name('artist'))
        self.assertEqual('Lyrics', display_tag_name('lyrics:'))
        self.assertEqual('Comment [Foo]', display_tag_name('comment:Foo'))

    def test_parse_comment_tag(self):
        self.assertEqual(('XXX', 'foo'), parse_comment_tag('comment:XXX:foo'))
        self.assertEqual(('eng', 'foo'), parse_comment_tag('comment:foo'))
        self.assertEqual(('eng', ''), parse_comment_tag('comment'))

    def test_parse_lang_desc_tag(self):
        self.assertEqual(('jpn', ''), parse_lang_desc_tag('lyrics:jpn'))
        self.assertEqual(('jpn', ''), parse_lang_desc_tag('lyrics:jpn:'))
        self.assertEqual(('jpn', 'foo'), parse_lang_desc_tag('lyrics:jpn:foo'))
        self.assertEqual(('xxx', 'foo'), parse_lang_desc_tag('lyrics::foo'))
        self.assertEqual(('xxx', 'notalanguage:foo'), parse_lang_desc_tag('lyrics:notalanguage:foo'))

    def test_create_lang_desc_tag(self):
        self.assertEqual('comment', create_lang_desc_tag('comment'))
        self.assertEqual('comment:eng', create_lang_desc_tag('comment', language='eng'))
        self.assertEqual('comment::foo', create_lang_desc_tag('comment', description='foo'))
        self.assertEqual('lyrics:jpn:foo', create_lang_desc_tag(
            'lyrics', language='jpn', description='foo'))
        self.assertEqual('lyrics::foo', create_lang_desc_tag(
            'lyrics', language='jpn', description='foo', default_language='jpn'))
