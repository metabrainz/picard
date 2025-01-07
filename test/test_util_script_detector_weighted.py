# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Philipp Wolfer
# Copyright (C) 2021-2022 Laurent Monin
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

from picard.util.script_detector_weighted import (
    detect_script_weighted,
    list_script_weighted,
)


class WeightedScriptDetectionTest(PicardTestCase):

    def test_detect_script_weighted(self):
        scripts = detect_script_weighted("Latin, кириллический, Ελληνική")
        self.assertAlmostEqual(scripts['LATIN'], 0.195, 3)
        self.assertAlmostEqual(scripts['CYRILLIC'], 0.518, 3)
        self.assertAlmostEqual(scripts['GREEK'], 0.287, 3)

        scripts = detect_script_weighted("Latin, кириллический, Ελληνική", threshold=0.5)
        script_keys = list(scripts.keys())
        self.assertEqual(script_keys, ["CYRILLIC"])

        scripts = detect_script_weighted("Latin")
        self.assertEqual(scripts["LATIN"], 1)

        scripts = detect_script_weighted("привет")
        self.assertEqual(scripts["CYRILLIC"], 1)

        scripts = detect_script_weighted("ελληνικά?")
        self.assertEqual(scripts["GREEK"], 1)

        scripts = detect_script_weighted("سماوي يدور")
        self.assertEqual(scripts["ARABIC"], 1)

        scripts = detect_script_weighted("שלום")
        self.assertEqual(scripts["HEBREW"], 1)

        scripts = detect_script_weighted("汉字")
        self.assertEqual(scripts["CJK"], 1)

        scripts = detect_script_weighted("한글")
        self.assertEqual(scripts["HANGUL"], 1)

        scripts = detect_script_weighted("ひらがな")
        self.assertEqual(scripts["HIRAGANA"], 1)

        scripts = detect_script_weighted("カタカナ")
        self.assertEqual(scripts["KATAKANA"], 1)

        scripts = detect_script_weighted("พยัญชนะ")
        self.assertEqual(scripts["THAI"], 1)

        scripts = detect_script_weighted("1234567890+-/*=,./!?")
        self.assertEqual(scripts, {})

        scripts = detect_script_weighted("")
        self.assertEqual(scripts, {})


class ListScriptWeightedTest(PicardTestCase):

    def test_list_script_weighted(self):
        scripts = list_script_weighted("Cyrillic, кириллический, 汉字")
        self.assertEqual(scripts, ['CYRILLIC', 'LATIN', 'CJK'])

        scripts = list_script_weighted("Cyrillic, кириллический, 汉字", threshold=0.3)
        self.assertEqual(scripts, ['CYRILLIC', 'LATIN'])
