# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

import re

from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

from picard.const.language_names import LANGUAGE_NAMES


class LanguageNamesTest(PicardTestCase):
    def test_not_empty(self):
        self.assertGreater(len(LANGUAGE_NAMES), 400)

    def test_codes_are_lowercase_iso_639_3(self):
        invalid = [code for code in LANGUAGE_NAMES if not re.fullmatch(r'[a-z]{3}', code)]
        self.assertEqual([], invalid)

    def test_names_are_non_empty_and_stripped(self):
        invalid = [code for code, name in LANGUAGE_NAMES.items() if not name or name != name.strip()]
        self.assertEqual([], invalid)

    @subtest_cases(
        "code,name",
        [
            ("eng", "English"),
            ("fra", "French"),
            ("jpn", "Japanese"),
            ("zxx", "[No linguistic content]"),
        ],
    )
    def test_known_languages(self, code, name):
        self.assertEqual(name, LANGUAGE_NAMES[code])

    def test_language_families_excluded(self):
        # Entries without an ISO 639-3 code ("iso_code_3:null") are not extracted
        self.assertNotIn('nul', LANGUAGE_NAMES)
        self.assertNotIn('null', LANGUAGE_NAMES)
