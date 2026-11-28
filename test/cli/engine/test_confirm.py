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

from test.cli.engine.helpers import EngineCommandTestCase
from test.picardtestcase import subtest_cases

from picard.cli.engine.commands import EngineCommand
from picard.cli.engine.completion import complete
from picard.cli.engine.confirmations import (
    SessionConfirmations,
    confirmation_keys,
)
from picard.cli.engine.result import EngineResult
from picard.cli.shell import _needs_confirmation
from picard.config import get_config


# The keys of the destructive built-in commands, sorted.
ALL_KEYS = ['confirm_save', 'logout', 'option_save', 'save', 'trash']


class _ConfirmTestBase(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.set_saved_off([])

    def set_saved_off(self, keys):
        """Set the keys turned off in the configuration."""
        self.set_config_values(persist={'shell_confirmations_off': keys})

    @staticmethod
    def saved_off():
        """The keys turned off in the configuration."""
        return get_config().persist['shell_confirmations_off']

    def state(self, key):
        return 'on' if self.session.confirmations.is_enabled(key) else 'off'

    def source(self, key):
        return self.session.confirmations.source_of(key)

    def command(self, name):
        command = self.reg.get(name)
        assert command is not None
        return command

    def handles(self, line):
        """The handles of the items of the result of ``line``, which must succeed."""
        result = self.run_command(line)
        self.assertTrue(result.ok, result.error)
        return [item.handle for item in result.items]


class SessionConfirmationsTest(_ConfirmTestBase):
    def test_everything_is_on_unless_turned_off_in_the_configuration(self):
        confirmations = SessionConfirmations()
        self.assertTrue(confirmations.is_enabled('save'))
        self.assertEqual('default', confirmations.source_of('save'))
        self.set_saved_off(['save'])
        self.assertFalse(confirmations.is_enabled('save'))
        self.assertEqual('config', confirmations.source_of('save'))

    def test_the_session_overrides_the_configuration_without_changing_it(self):
        self.set_saved_off(['save'])
        confirmations = SessionConfirmations()
        confirmations.set('save', True)
        self.assertTrue(confirmations.is_enabled('save'))
        self.assertEqual('session', confirmations.source_of('save'))
        self.assertEqual(['save'], self.saved_off())

    def test_confirmation_keys(self):
        expected = {key: [key.replace('_', ' ')] for key in ALL_KEYS}
        self.assertEqual(expected, confirmation_keys(self.reg))

    def test_save_writes_the_session_values_and_forgets_them(self):
        self.set_saved_off(['other', 'save'])
        confirmations = SessionConfirmations()
        confirmations.set('save', True)
        confirmations.set('trash', False)
        confirmations.save(['save'])
        self.assertEqual(['other'], self.saved_off())
        self.assertEqual(['trash'], confirmations.overridden())
        self.assertEqual('default', confirmations.source_of('save'))

    def test_all_cannot_be_the_key_of_a_command(self):
        with self.assertRaises(ValueError):
            EngineCommand(name='all', run=lambda session, args: EngineResult(), destructive=True)


class ConfirmLsTest(_ConfirmTestBase):
    def test_lists_the_confirmations(self):
        result = self.run_command('confirm ls')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(ALL_KEYS, [item.handle for item in result.items])
        item = result.items[ALL_KEYS.index('save')]
        self.assertEqual('default', item.status)
        self.assertEqual({'value': 'on', 'commands': 'save'}, item.data)

    @subtest_cases(
        "line,saved_off,expected",
        [
            ('confirm ls save', [], [('save', 'on')]),
            ('confirm ls trash', ['trash'], [('trash', 'off')]),
            ('confirm ls logout trash', ['trash'], [('logout', 'on'), ('trash', 'off')]),
        ],
    )
    def test_lists_only_the_keys_given(self, line, saved_off, expected):
        self.set_saved_off(saved_off)
        result = self.run_command(line)
        self.assertEqual(expected, [(item.handle, item.data['value']) for item in result.items])


class ConfirmOnOffTest(_ConfirmTestBase):
    def test_turns_a_key_off_for_the_session_only(self):
        result = self.run_command('confirm off save')
        self.assertTrue(result.ok, result.error)
        (item,) = result.items
        self.assertEqual(('session', 'off'), (item.status, item.data['value']))
        self.assertEqual([], self.saved_off())
        self.assertEqual('on', self.state('trash'))
        self.run_command('confirm on save')
        self.assertEqual('on', self.state('save'))

    def test_turns_several_keys(self):
        self.run_command('confirm off save trash')
        self.assertEqual(['off', 'off', 'on'], [self.state(key) for key in ('save', 'trash', 'logout')])

    @subtest_cases("verb,state", [('off', 'off'), ('on', 'on')])
    def test_turns_all_of_them(self, verb, state):
        self.session.confirmations.set('save', verb != 'on')
        self.assertEqual(ALL_KEYS, self.handles(f'confirm {verb} all'))
        self.assertEqual({state}, {self.state(key) for key in ALL_KEYS})

    @subtest_cases("verb", ['on', 'off'])
    def test_needs_a_key_or_all(self, verb):
        result = self.run_command(f'confirm {verb}')
        self.assertFalse(result.ok)
        self.assertIn('usage', result.error.lower())
        self.assertEqual([], self.session.confirmations.overridden())

    def test_unknown_key_is_suggested_and_nothing_changes(self):
        result = self.run_command('confirm off savv trash')
        self.assertFalse(result.ok)
        self.assertIn('did you mean save', result.error)
        self.assertEqual('on', self.state('trash'))

    def test_the_shell_follows_the_session(self):
        command = self.command('save')
        self.assertTrue(_needs_confirmation(command, self.session))
        self.run_command('confirm off save')
        self.assertFalse(_needs_confirmation(command, self.session))


class ConfirmSaveTest(_ConfirmTestBase):
    def test_is_destructive_and_has_its_own_key(self):
        command = self.command('confirm save')
        self.assertTrue(command.destructive)
        self.assertEqual('confirm_save', command.confirm_key)

    def test_writes_the_keys_given_to_the_configuration(self):
        self.run_command('confirm off save trash')
        self.assertEqual(['save'], self.handles('confirm save save'))
        self.assertEqual(['save'], self.saved_off())
        self.assertEqual('config', self.source('save'))
        # The other one is still only set in the session.
        self.assertEqual('session', self.source('trash'))

    def test_without_a_key_writes_them_all(self):
        self.run_command('confirm off save trash')
        self.assertEqual(['save', 'trash'], self.handles('confirm save'))
        self.assertEqual(['save', 'trash'], self.saved_off())
        self.assertEqual([], self.session.confirmations.overridden())

    def test_can_turn_a_saved_choice_back_on(self):
        self.set_saved_off(['save'])
        self.run_command('confirm on save')
        self.run_command('confirm save')
        self.assertEqual([], self.saved_off())

    def test_with_nothing_set(self):
        result = self.run_command('confirm save')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([], result.items)
        self.assertIn('no confirmation', result.message)


class ConfirmKeysTest(_ConfirmTestBase):
    @subtest_cases(
        "line", ['confirm ls nope', 'confirm ls all', 'confirm on nope', 'confirm save nope', 'confirm save all']
    )
    def test_an_unknown_key_is_refused(self, line):
        self.assertFalse(self.run_command(line).ok)

    def words(self, line):
        text = '' if line.endswith(' ') else line.split(' ')[-1]
        return complete(line, text, self.reg, self.session)

    def test_completes_the_verbs(self):
        self.assertEqual({'ls', 'on', 'off', 'save'}, set(self.words('confirm ')))
        self.assertEqual(['off'], self.words('confirm of'))

    @subtest_cases(
        "verb,all_offered",
        [('ls', False), ('save', False), ('on', True), ('off', True)],
    )
    def test_completes_the_keys(self, verb, all_offered):
        self.assertEqual(['trash'], self.words(f'confirm {verb} tr'))
        self.assertTrue(set(ALL_KEYS) <= set(self.words(f'confirm {verb} ')))
        self.assertEqual(all_offered, 'all' in self.words(f'confirm {verb} '))
