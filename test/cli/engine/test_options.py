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

"""Options of a session: set for the session, over the user's configuration."""

import os

from test.picardtestcase import PicardTestCase

from picard import config
from picard.cli.engine.options import (
    OptionCommandError,
    SessionOptions,
    parse_value,
)
from picard.config import (
    BoolOption,
    Config,
    FloatOption,
    IntOption,
    ListOption,
    Option,
    SettingConfigSection,
    TextOption,
)


class _OptionsTestBase(PicardTestCase):
    """A real configuration (profiles included) with a few options registered."""

    def setUp(self):
        super().setUp()
        old_registry = dict(Option.registry)
        Option.registry = {}
        self.addCleanup(setattr, Option, 'registry', old_registry)

        BoolOption('setting', 'move_files', False, title="Move files", in_profile=True)
        TextOption('setting', 'move_files_to', '/music', title="Destination of moved files", in_profile=True)
        IntOption('setting', 'query_limit', 50, title="Search results limit", in_profile=True, bounds=(1, 100))
        FloatOption('setting', 'min_similarity', 0.5, title="Minimum similarity", in_profile=True, bounds=(0, 1))
        ListOption('setting', 'preserved_tags', [], title="Preserved tags", in_profile=True)
        TextOption('setting', 'ui_theme', 'default', title="Theme")
        Option('setting', 'file_renaming_scripts', {}, title="Scripts")

        self.configpath = os.path.join(self.mktmpdir(), 'test.ini')
        self.config = Config.from_file(None, self.configpath)
        self.addCleanup(self._cleanup_config)
        config.config = self.config
        config.setting = self.config.setting
        config.persist = self.config.persist
        config.profiles = self.config.profiles
        self.options = SessionOptions()

    def _cleanup_config(self):
        # Make sure QSettings does not recreate the file on exit.
        self.config.sync()
        del self.config

    def _add_user_profile(self, title, settings, enabled=True):
        profile_id = f'profile-{title}'
        profiles = list(self.config.profiles[SettingConfigSection.PROFILES_KEY])
        profiles.append({'id': profile_id, 'title': title, 'enabled': enabled})
        self.config.profiles[SettingConfigSection.PROFILES_KEY] = profiles
        saved = dict(self.config.profiles[SettingConfigSection.SETTINGS_KEY])
        saved[profile_id] = settings
        self.config.profiles[SettingConfigSection.SETTINGS_KEY] = saved
        return profile_id

    def _file_text(self):
        """The content of the configuration file ('' if nothing was ever written to it)."""
        self.config.sync()
        if not os.path.exists(self.configpath):
            return ''
        with open(self.configpath, encoding='utf-8') as f:
            return f.read()


class DescribeTest(_OptionsTestBase):
    def test_names_are_those_of_the_setting_section_sorted(self):
        names = self.options.names()
        self.assertEqual(sorted(names), names)
        self.assertIn('move_files', names)
        self.assertNotIn('user_profiles', names)

    def test_describe_an_option_at_its_default(self):
        info = self.options.describe('move_files')
        self.assertEqual(
            {
                'name': 'move_files',
                'value': False,
                'default': False,
                'type': 'bool',
                'title': "Move files",
                'source': 'default',
                'settable': True,
            },
            info,
        )

    def test_describe_is_plain_serializable_data(self):
        for name in self.options.names():
            info = self.options.describe(name)
            self.assertIsInstance(info['value'], (bool, int, float, str, list, dict))

    def test_value_stored_in_the_configuration(self):
        self.config.setting['move_files'] = True
        info = self.options.describe('move_files')
        self.assertEqual((True, 'config'), (info['value'], info['source']))

    def test_value_of_a_profile(self):
        self._add_user_profile('Archive', {'move_files': True})
        info = self.options.describe('move_files')
        self.assertEqual((True, 'profile Archive'), (info['value'], info['source']))

    def test_disabled_profile_is_ignored(self):
        self._add_user_profile('Archive', {'move_files': True}, enabled=False)
        self.assertEqual('default', self.options.describe('move_files')['source'])

    def test_not_settable(self):
        self.assertFalse(self.options.describe('ui_theme')['settable'])  # not in profiles
        self.assertFalse(self.options.describe('file_renaming_scripts')['settable'])  # not a simple value

    def test_unknown_option_suggests_the_close_ones(self):
        with self.assertRaises(OptionCommandError) as ctx:
            self.options.describe('move_file')
        self.assertIn("unknown option 'move_file'", str(ctx.exception))
        self.assertIn('move_files', str(ctx.exception))


class MatchingTest(_OptionsTestBase):
    def test_without_a_pattern_only_options_not_at_their_default(self):
        self.assertEqual([], self.options.matching())
        self.config.setting['move_files'] = True
        self._add_user_profile('Archive', {'query_limit': 10})
        self.assertEqual(['move_files', 'query_limit'], [info['name'] for info in self.options.matching()])

    def test_substring_of_the_name(self):
        self.assertEqual(['move_files', 'move_files_to'], [info['name'] for info in self.options.matching('move')])

    def test_substring_of_the_title_ignores_case(self):
        self.assertEqual(['min_similarity'], [info['name'] for info in self.options.matching('SIMILARITY')])

    def test_glob(self):
        self.assertEqual(['move_files_to'], [info['name'] for info in self.options.matching('*_to')])

    def test_nothing_matches(self):
        self.assertEqual([], self.options.matching('nonsense'))


class ParseValueTest(_OptionsTestBase):
    def _parse(self, name, text):
        return parse_value(Option.get('setting', name), text)

    def test_bool(self):
        for text in ('true', 'True', 'YES', 'on', '1'):
            self.assertIs(True, self._parse('move_files', text), text)
        for text in ('false', 'No', 'off', '0'):
            self.assertIs(False, self._parse('move_files', text), text)

    def test_bad_bool(self):
        with self.assertRaises(OptionCommandError) as ctx:
            self._parse('move_files', 'maybe')
        self.assertIn('true or false', str(ctx.exception))

    def test_int_and_float(self):
        self.assertEqual(25, self._parse('query_limit', ' 25 '))
        self.assertEqual(0.75, self._parse('min_similarity', '0.75'))

    def test_bad_numbers(self):
        for name, text in (('query_limit', 'many'), ('query_limit', '2.5'), ('min_similarity', 'high')):
            with self.subTest(name=name, text=text):
                with self.assertRaises(OptionCommandError):
                    self._parse(name, text)

    def test_numbers_out_of_range_are_rejected_with_the_nearest_allowed(self):
        with self.assertRaises(OptionCommandError) as ctx:
            self._parse('query_limit', '500')
        self.assertIn('out of range', str(ctx.exception))
        self.assertIn('100', str(ctx.exception))

    def test_text_is_kept_as_it_is(self):
        self.assertEqual('/tmp/a b', self._parse('move_files_to', '/tmp/a b'))

    def test_list_from_commas_or_json(self):
        self.assertEqual(['a', 'b c'], self._parse('preserved_tags', 'a, b c'))
        self.assertEqual(['a', 'b'], self._parse('preserved_tags', '["a", "b"]'))
        self.assertEqual([], self._parse('preserved_tags', ''))

    def test_bad_json_list(self):
        for text in ('[unclosed', '["a", '):
            with self.subTest(text=text):
                with self.assertRaises(OptionCommandError):
                    self._parse('preserved_tags', text)


class SetTest(_OptionsTestBase):
    def test_nothing_is_touched_until_an_option_is_set(self):
        self.assertIsNone(self.config.setting.profiles_override)
        self.assertIsNone(self.config.setting.settings_override)
        self.options.set('move_files', 'true')
        self.assertIsNotNone(self.config.setting.profiles_override)

    def test_the_configuration_returns_the_session_value(self):
        info = self.options.set('move_files', 'yes')
        self.assertEqual((True, 'session'), (info['value'], info['source']))
        self.assertIs(True, config.setting['move_files'])

    def test_every_kind_is_returned_by_the_configuration(self):
        self.options.set('move_files_to', '/tmp/out')
        self.options.set('query_limit', '25')
        self.options.set('min_similarity', '0.9')
        self.options.set('preserved_tags', 'a,b')
        self.assertEqual('/tmp/out', config.setting['move_files_to'])
        self.assertEqual(25, config.setting['query_limit'])
        self.assertEqual(0.9, config.setting['min_similarity'])
        self.assertEqual(['a', 'b'], config.setting['preserved_tags'])

    def test_the_configuration_file_is_not_written(self):
        self.options.set('move_files', 'true')
        self.options.set('move_files_to', '/tmp/out')
        self.assertNotIn('move_files', self._file_text())
        self.assertNotIn('/tmp/out', self._file_text())
        self.assertNotIn('move_files', self.config.setting)
        with self.config.setting.no_profile():
            self.assertIs(False, self.config.setting['move_files'])

    def test_the_session_wins_over_a_profile(self):
        self._add_user_profile('Archive', {'move_files': True})
        self.options.set('move_files', 'false')
        self.assertIs(False, config.setting['move_files'])
        self.assertEqual('session', self.options.describe('move_files')['source'])

    def test_other_options_are_unchanged(self):
        self._add_user_profile('Archive', {'query_limit': 10})
        self.options.set('move_files', 'true')
        self.assertEqual(10, config.setting['query_limit'])

    def test_what_cannot_be_set_is_refused(self):
        for name in ('ui_theme', 'file_renaming_scripts'):
            with self.subTest(name=name):
                with self.assertRaises(OptionCommandError) as ctx:
                    self.options.set(name, 'x')
                self.assertIn('cannot be changed for a session', str(ctx.exception))

    def test_a_bad_value_names_the_option_and_changes_nothing(self):
        with self.assertRaises(OptionCommandError) as ctx:
            self.options.set('query_limit', 'many')
        self.assertTrue(str(ctx.exception).startswith('query_limit:'))
        self.assertEqual(50, config.setting['query_limit'])

    def test_unknown_option(self):
        with self.assertRaises(OptionCommandError):
            self.options.set('nonsense', 'x')


class UnsetTest(_OptionsTestBase):
    def test_back_to_the_value_below(self):
        self.config.setting['move_files_to'] = '/from/config'
        self.options.set('move_files_to', '/from/session')
        info = self.options.unset('move_files_to')
        self.assertEqual(('/from/config', 'config'), (info['value'], info['source']))
        self.assertEqual('/from/config', config.setting['move_files_to'])

    def test_back_to_the_profile(self):
        self._add_user_profile('Archive', {'move_files': True})
        self.options.set('move_files', 'false')
        self.assertEqual(('profile Archive', True), self._source_and_value('move_files', self.options.unset))

    def _source_and_value(self, name, action):
        info = action(name)
        return info['source'], info['value']

    def test_unset_of_what_was_never_set_is_harmless(self):
        info = self.options.unset('move_files')
        self.assertEqual('default', info['source'])

    def test_unknown_option(self):
        with self.assertRaises(OptionCommandError):
            self.options.unset('nonsense')


class SaveTest(_OptionsTestBase):
    def test_saved_values_are_written_to_the_configuration(self):
        self.options.set('move_files', 'true')
        self.options.set('query_limit', '10')
        infos = self.options.save(['move_files'])
        self.assertEqual(['move_files'], [info['name'] for info in infos])
        self.assertEqual('config', infos[0]['source'])
        self.assertIn('move_files', self.config.setting)
        self.assertIn('move_files', self._file_text())
        # Only what was asked for.
        self.assertNotIn('query_limit', self.config.setting)
        self.assertEqual('session', self.options.describe('query_limit')['source'])

    def test_save_without_names_saves_everything_set(self):
        self.options.set('move_files', 'true')
        self.options.set('query_limit', '10')
        self.assertEqual(['move_files', 'query_limit'], [info['name'] for info in self.options.save()])
        self.assertEqual(10, self.config.setting['query_limit'])
        # Nothing is left to save.
        self.assertEqual([], self.options.save())

    def test_saving_nothing_does_not_install_the_session(self):
        self.assertEqual([], self.options.save())
        self.assertFalse(self.options._installed)

    def test_the_value_survives_the_end_of_the_session(self):
        self.options.set('move_files_to', '/tmp/out')
        self.options.save()
        with self.config.setting.no_profile():
            self.assertEqual('/tmp/out', self.config.setting['move_files_to'])
        self.assertEqual('config', self.options.describe('move_files_to')['source'])

    def test_a_profile_that_sets_the_option_is_updated_like_the_gui_would(self):
        profile_id = self._add_user_profile('Archive', {'move_files': False})
        self.options.set('move_files', 'true')
        infos = self.options.save()
        self.assertEqual((True, 'profile Archive'), (infos[0]['value'], infos[0]['source']))
        saved = self.config.profiles[SettingConfigSection.SETTINGS_KEY]
        self.assertIs(True, saved[profile_id]['move_files'])
        self.assertNotIn('move_files', self.config.setting)

    def test_only_what_was_set_can_be_saved(self):
        self.options.set('move_files', 'true')
        with self.assertRaises(OptionCommandError) as ctx:
            self.options.save(['query_limit'])
        self.assertIn('has not been set', str(ctx.exception))
        with self.assertRaises(OptionCommandError):
            self.options.save(['nonsense'])
        # A refused save changes nothing.
        self.assertNotIn('move_files', self.config.setting)
        self.assertEqual('session', self.options.describe('move_files')['source'])
