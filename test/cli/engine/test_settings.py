#
# Picard, the next-generation MusicBrainz tagger
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

from test.cli.engine.helpers import EngineCommandTestCase
from test.picardtestcase import PicardTestCase

from picard.cli.engine.settings import (
    ConsoleSettings,
    SettingError,
)


class ConsoleSettingsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.settings = ConsoleSettings()

    def test_defaults(self):
        self.assertEqual((5, 12), (self.settings.get('open_max'), self.settings.get('minted_max')))

    def test_set(self):
        self.settings.set('open_max', '10')
        self.assertEqual(10, self.settings.get('open_max'))
        self.assertEqual('session', self.settings.describe('open_max')['source'])
        self.assertEqual('default', self.settings.describe('minted_max')['source'])

    def test_minus_one_is_no_limit(self):
        self.assertEqual(5, self.settings.limit('open_max'))
        self.settings.set('open_max', '-1')
        self.assertIsNone(self.settings.limit('open_max'))

    def test_zero_is_a_limit(self):
        self.settings.set('minted_max', '0')
        self.assertEqual(0, self.settings.limit('minted_max'))

    def test_bad_names_and_values(self):
        for name, value in (
            ('nope', '1'),
            ('open_max', 'many'),
            ('open_max', '1.5'),
            ('open_max', '-2'),
            ('open_max', ''),
        ):
            with self.subTest(name=name, value=value), self.assertRaises(SettingError):
                self.settings.set(name, value)

    def test_a_bad_value_leaves_the_setting_as_it_was(self):
        self.settings.set('open_max', '7')
        with self.assertRaises(SettingError):
            self.settings.set('open_max', 'x')
        self.assertEqual(7, self.settings.get('open_max'))

    def test_each_session_has_its_own_settings(self):
        other = ConsoleSettings()
        self.settings.set('open_max', '9')
        self.assertEqual(5, other.get('open_max'))


class ShellCommandsTest(EngineCommandTestCase):
    def test_shell_get_lists_the_settings(self):
        result = self.run_command('shell get')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(['open_max', 'minted_max'], [item.handle for item in result.items])
        self.assertEqual(['default', 'default'], [item.status for item in result.items])
        self.assertEqual((5, 5), (result.items[0].data['value'], result.items[0].data['default']))

    def test_shell_get_one_setting(self):
        (item,) = self.run_command('shell get minted_max').items
        self.assertEqual(12, item.data['value'])

    def test_shell_set_changes_the_session(self):
        result = self.run_command('shell set open_max 10')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(
            ('open_max', 'session', 10), (result.items[0].handle, result.items[0].status, result.items[0].data['value'])
        )
        self.assertEqual(10, self.session.settings.get('open_max'))
        self.assertEqual('session', self.run_command('shell get open_max').items[0].status)

    def test_shell_set_accepts_no_limit(self):
        self.run_command('shell set open_max -1')
        self.assertIsNone(self.session.settings.limit('open_max'))

    def test_shell_set_reports_what_is_wrong(self):
        for line, word in (
            ('shell set nope 1', 'unknown setting'),
            ('shell set open_max many', 'number'),
            ('shell set open_max -5', 'less than'),
            ('shell get nope', 'unknown setting'),
        ):
            with self.subTest(line=line):
                result = self.run_command(line)
                self.assertFalse(result.ok)
                self.assertIn(word, result.error)

    def test_shell_set_usage(self):
        for line in ('shell set', 'shell set open_max'):
            with self.subTest(line=line):
                self.assertIn('usage', self.run_command(line).error)
