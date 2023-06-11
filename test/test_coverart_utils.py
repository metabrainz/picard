# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019, 2021 Philipp Wolfer
# Copyright (C) 2020 Laurent Monin
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

from picard.coverart.utils import (
    image_type_as_id3_num,
    image_type_from_id3_num,
    translate_caa_type,
    types_from_id3,
)


class CaaTypeTranslationTest(PicardTestCase):
    def test_translating_unknown_types_returns_input(self):
        testtype = "ThisIsAMadeUpCoverArtTypeName"
        self.assertEqual(translate_caa_type(testtype), testtype)


class Id3TypeTranslationTest(PicardTestCase):
    def test_image_type_from_id3_num(self):
        self.assertEqual(image_type_from_id3_num(0), 'other')
        self.assertEqual(image_type_from_id3_num(3), 'front')
        self.assertEqual(image_type_from_id3_num(6), 'medium')
        self.assertEqual(image_type_from_id3_num(9999), 'other')

    def test_image_type_as_id3_num(self):
        self.assertEqual(image_type_as_id3_num('other'), 0)
        self.assertEqual(image_type_as_id3_num('front'), 3)
        self.assertEqual(image_type_as_id3_num('medium'), 6)
        self.assertEqual(image_type_as_id3_num('track'), 6)
        self.assertEqual(image_type_as_id3_num('unknowntype'), 0)

    def test_types_from_id3(self):
        self.assertEqual(types_from_id3(0), ['other'])
        self.assertEqual(types_from_id3(3), ['front'])
        self.assertEqual(types_from_id3(6), ['medium'])
        self.assertEqual(types_from_id3(9999), ['other'])
