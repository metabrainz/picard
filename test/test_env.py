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


import os

from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

from picard.env import parse_bool_env


class ParseBoolEnvTest(PicardTestCase):
    ENV_NAME = 'PICARD_TEST_BOOL_ENV'

    def _set_env(self, value):
        if value is None:
            os.environ.pop(self.ENV_NAME, None)
        else:
            os.environ[self.ENV_NAME] = value
        self.addCleanup(os.environ.pop, self.ENV_NAME, None)

    @subtest_cases(
        "value",
        {
            'one': ('1',),
            'true': ('true',),
            'true uppercase': ('TRUE',),
            'true mixed case': ('True',),
            'true with whitespace': ('  true  ',),
            'yes': ('yes',),
            'on': ('on',),
        },
    )
    def test_truthy_values(self, value):
        self._set_env(value)
        self.assertTrue(parse_bool_env(self.ENV_NAME))

    @subtest_cases(
        "value",
        {
            'zero': ('0',),
            'false': ('false',),
            'false uppercase': ('FALSE',),
            'no': ('no',),
            'off': ('off',),
            'empty': ('',),
            'whitespace only': ('   ',),
        },
    )
    def test_falsy_values(self, value):
        self._set_env(value)
        self.assertFalse(parse_bool_env(self.ENV_NAME, default=True))

    def test_unset_returns_default(self):
        self._set_env(None)
        self.assertFalse(parse_bool_env(self.ENV_NAME))
        self.assertTrue(parse_bool_env(self.ENV_NAME, default=True))

    @subtest_cases(
        "value",
        {
            'arbitrary word': ('maybe',),
            'number other than 0/1': ('2',),
            'partial': ('tru',),
        },
    )
    def test_unrecognized_returns_default(self, value):
        self._set_env(value)
        # Unrecognized values fall back to the provided default.
        self.assertFalse(parse_bool_env(self.ENV_NAME, default=False))
        self.assertTrue(parse_bool_env(self.ENV_NAME, default=True))
