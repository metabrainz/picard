# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020 Philipp Wolfer
# Copyright (C) 2020-2022 Laurent Monin
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Serial
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
    display_tag_name,
    parse_comment_tag,
    parse_subtag,
)


class UtilTagsTest(PicardTestCase):
    def test_display_tag_name(self):
        self.assertEqual('Artist', display_tag_name('artist'))
        self.assertEqual('Lyrics', display_tag_name('lyrics:'))
        self.assertEqual('Comment [Foo]', display_tag_name('comment:Foo'))

    def test_parse_comment_tag(self):
        self.assertEqual(('XXX', 'foo'), parse_comment_tag('comment:XXX:foo'))
        self.assertEqual(('eng', 'foo'), parse_comment_tag('comment:foo'))
        self.assertEqual(('XXX', ''), parse_comment_tag('comment:XXX'))
        self.assertEqual(('eng', ''), parse_comment_tag('comment'))

    def test_parse_lyrics_tag(self):
        self.assertEqual(('eng', ''), parse_subtag('lyrics'))
        self.assertEqual(('XXX', 'foo'), parse_subtag('lyrics:XXX:foo'))
        self.assertEqual(('XXX', ''), parse_subtag('lyrics:XXX'))
        self.assertEqual(('eng', 'foo'), parse_subtag('lyrics::foo'))
