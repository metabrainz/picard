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

"""The `option` commands, driven through the dispatcher."""

import io
from unittest.mock import MagicMock

from test.cli.engine.test_options import _OptionsTestBase

from picard.cli.engine.builtins import register_builtins
from picard.cli.engine.commands import EngineCommandRegistry
from picard.cli.engine.dispatch import dispatch
from picard.cli.engine.render import render_result
from picard.cli.engine.session import LocalEngineSession
from picard.cli.output import CliOutput


class _OptionCommandTestBase(_OptionsTestBase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.session = LocalEngineSession(MagicMock())

    def _run(self, line):
        return dispatch(self.session, self.reg, line)


class OptionLsTest(_OptionCommandTestBase):
    def test_nothing_is_listed_while_everything_is_at_its_default(self):
        result = self._run('option ls')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([], result.items)

    def test_options_not_at_their_default_are_listed(self):
        self.config.setting['move_files'] = True
        result = self._run('option ls')
        (item,) = result.items
        self.assertEqual(('move_files', 'config'), (item.handle, item.status))
        self.assertEqual(True, item.data['value'])
        self.assertEqual(False, item.data['default'])

    def test_pattern_lists_matching_options_whatever_their_value(self):
        result = self._run('option ls move')
        self.assertEqual(['move_files', 'move_files_to'], [item.handle for item in result.items])
        self.assertEqual({'default'}, {item.status for item in result.items})

    def test_pattern_may_be_a_glob_or_part_of_a_title(self):
        self.assertEqual(['move_files_to'], [i.handle for i in self._run('option ls *_to').items])
        self.assertEqual(['query_limit'], [i.handle for i in self._run('option ls results').items])

    def test_items_are_serializable(self):
        result = self._run('option ls move')
        self.assertEqual(
            {'value', 'default', 'type', 'title', 'settable'},
            set(result.to_dict()['items'][0]['data']),
        )

    def test_the_rendering_shows_the_value_and_the_default(self):
        self.config.setting['move_files'] = True
        buf = io.StringIO()
        render_result(self._run('option ls move_files'), CliOutput(stdout=buf, stderr=buf, color=False))
        line = buf.getvalue().splitlines()[0]
        self.assertTrue(line.startswith('move_files  config'), line)
        self.assertIn('value=True', line)
        self.assertIn('default=False', line)
        self.assertIn('title=Move files', line)


class OptionGetTest(_OptionCommandTestBase):
    def test_get(self):
        result = self._run('option get query_limit')
        self.assertTrue(result.ok, result.error)
        (item,) = result.items
        self.assertEqual(('query_limit', 'default'), (item.handle, item.status))
        self.assertEqual(
            {'value': 50, 'default': 50, 'type': 'int', 'title': "Search results limit", 'settable': True},
            item.data,
        )

    def test_get_says_where_the_value_comes_from(self):
        self.config.setting['query_limit'] = 20
        self.assertEqual('config', self._run('option get query_limit').items[0].status)

    def test_unknown_option_is_a_failure_with_suggestions(self):
        result = self._run('option get move_file')
        self.assertFalse(result.ok)
        self.assertIn("unknown option 'move_file'", result.error)
        self.assertIn('move_files', result.error)

    def test_usage(self):
        result = self._run('option get')
        self.assertFalse(result.ok)
        self.assertIn('usage', result.error)

    def test_options_are_not_taken_for_selectors(self):
        # An option name is the handle of its item; it must not be looked up as a
        # path (and so does not get one).
        self.assertEqual('', self._run('option get move_files').items[0].path)


class OptionSetTest(_OptionCommandTestBase):
    def test_set_for_the_session(self):
        result = self._run('option set move_files true')
        self.assertTrue(result.ok, result.error)
        (item,) = result.items
        self.assertEqual(('move_files', 'session'), (item.handle, item.status))
        self.assertIs(True, item.data['value'])
        self.assertIs(True, self.config.setting['move_files'])

    def test_the_value_is_seen_by_the_other_commands(self):
        self._run('option set query_limit 20')
        self.assertEqual(20, self._run('option get query_limit').items[0].data['value'])
        self.assertEqual(['query_limit'], [i.handle for i in self._run('option ls').items])

    def test_the_configuration_is_not_written(self):
        self._run('option set move_files true')
        self.assertNotIn('move_files', self._file_text())

    def test_the_value_may_have_spaces_without_quotes(self):
        self._run('option set move_files_to /tmp/my music/out')
        self.assertEqual('/tmp/my music/out', self.config.setting['move_files_to'])

    def test_quoted_value(self):
        self._run('option set move_files_to "/tmp/a  b"')
        self.assertEqual('/tmp/a  b', self.config.setting['move_files_to'])

    def test_empty_value(self):
        self._run('option set preserved_tags a,b')
        result = self._run('option set preserved_tags ""')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([], self.config.setting['preserved_tags'])

    def test_bad_value(self):
        for line, expected in (
            ('option set move_files maybe', 'true or false'),
            ('option set query_limit many', 'whole number'),
            ('option set query_limit 500', 'out of range'),
        ):
            with self.subTest(line=line):
                result = self._run(line)
                self.assertFalse(result.ok)
                self.assertTrue(result.error.startswith('option set: '), result.error)
                self.assertIn(expected, result.error)
        self.assertEqual(50, self.config.setting['query_limit'])

    def test_option_that_cannot_be_set(self):
        result = self._run('option set ui_theme dark')
        self.assertFalse(result.ok)
        self.assertIn('cannot be changed for a session', result.error)

    def test_unknown_option(self):
        result = self._run('option set move_file true')
        self.assertFalse(result.ok)
        self.assertIn('move_files', result.error)

    def test_usage(self):
        for line in ('option set', 'option set move_files'):
            with self.subTest(line=line):
                result = self._run(line)
                self.assertFalse(result.ok)
                self.assertIn('usage', result.error)


class OptionUnsetTest(_OptionCommandTestBase):
    def test_unset_goes_back_to_what_is_below(self):
        self.config.setting['query_limit'] = 20
        self._run('option set query_limit 30')
        result = self._run('option unset query_limit')
        self.assertTrue(result.ok, result.error)
        (item,) = result.items
        self.assertEqual(('query_limit', 'config', 20), (item.handle, item.status, item.data['value']))
        self.assertEqual(20, self.config.setting['query_limit'])

    def test_unknown_option(self):
        result = self._run('option unset nonsense')
        self.assertFalse(result.ok)
        self.assertIn('unknown option', result.error)

    def test_usage(self):
        result = self._run('option unset')
        self.assertFalse(result.ok)
        self.assertIn('usage', result.error)


class OptionSaveTest(_OptionCommandTestBase):
    def test_save_everything_set_in_the_session(self):
        self._run('option set move_files true')
        self._run('option set query_limit 10')
        result = self._run('option save')
        self.assertTrue(result.ok, result.error)
        self.assertEqual({'move_files': 'config', 'query_limit': 'config'}, {i.handle: i.status for i in result.items})
        self.assertIn('written', result.message)
        self.assertIn('move_files', self._file_text())
        self.assertEqual(10, self.config.setting['query_limit'])

    def test_save_only_the_options_named(self):
        self._run('option set move_files true')
        self._run('option set query_limit 10')
        result = self._run('option save move_files')
        self.assertEqual(['move_files'], [i.handle for i in result.items])
        self.assertEqual('session', self._run('option get query_limit').items[0].status)

    def test_save_of_several_names(self):
        self._run('option set move_files true')
        self._run('option set query_limit 10')
        result = self._run('option save move_files query_limit')
        self.assertEqual(['move_files', 'query_limit'], [i.handle for i in result.items])

    def test_nothing_to_save(self):
        result = self._run('option save')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([], result.items)
        self.assertIn('no option was set', result.message)

    def test_an_option_not_set_in_the_session_cannot_be_saved(self):
        self._run('option set move_files true')
        result = self._run('option save query_limit')
        self.assertFalse(result.ok)
        self.assertIn('has not been set', result.error)
        self.assertTrue(result.error.startswith('option save: '))
        self.assertNotIn('move_files', self.config.setting)

    def test_unknown_option(self):
        result = self._run('option save nonsense')
        self.assertFalse(result.ok)
        self.assertIn('unknown option', result.error)

    def test_the_shell_asks_before_saving(self):
        # It changes the configuration the GUI uses, so it is confirmed like trash.
        self.assertTrue(self.reg.get('option save').destructive)
        for name in ('option ls', 'option get', 'option set', 'option unset'):
            self.assertFalse(self.reg.get(name).destructive, name)
