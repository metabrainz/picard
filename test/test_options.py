# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
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

from picard.config import Option
from picard.i18n import N_
from picard.options import get_option_title


class OptionsUtilitiesTest(PicardTestCase):
    def test_option_titles(self):
        # Add test option settings
        if ('setting', 'test_option_with_title') not in Option.registry:
            Option('setting', 'test_option_with_title', None, title=N_('Test option with title'))
        if ('setting', 'test_option_without_title') not in Option.registry:
            Option('setting', 'test_option_without_title', None)

        # Invalid option name
        self.assertEqual(get_option_title('invalid_option'), None)

        # No title assigned to the option
        self.assertEqual(get_option_title('test_option_without_title'), 'test_option_without_title')

        # Title assigned to the option
        self.assertEqual(get_option_title('test_option_with_title'), 'Test option with title')

    def test_register_options_page_warns_widgets_without_in_profile(self):
        from unittest.mock import patch

        from picard.config import BoolOption
        from picard.extension_points.options_pages import register_options_page

        from picard.ui.options import OptionsPage

        BoolOption('setting', 'test_no_profile_opt', False)

        class TestPage(OptionsPage):
            NAME = 'test_warn_page'
            TITLE = 'Test'
            PARENT = None
            SORT_ORDER = 9999
            OPTIONS: dict[str, dict] = {
                'test_no_profile_opt': {'widgets': ['some_widget']},
            }

        with patch('picard.extension_points.options_pages.log') as mock_log:
            register_options_page(TestPage)
        mock_log.warning.assert_called_once()
        self.assertIn('in_profile=False', mock_log.warning.call_args[0][0])

    def test_restore_defaults_uses_correct_section(self):
        """restore_defaults should use OPTION_SECTION, not hardcode 'setting'."""
        from picard.config import (
            TextOption,
        )

        from picard.ui.options import OptionsPage

        # A plugin option in a non-setting section
        TextOption('plugin.test-restore', 'plugin_opt', 'plugin_default')

        class PluginPage(OptionsPage):
            NAME = 'test_plugin_page'
            TITLE = 'Plugin'
            PARENT = None
            SORT_ORDER = 9999
            OPTION_SECTION = 'plugin.test-restore'
            OPTIONS: dict[str, dict] = {'plugin_opt': {}}

        from picard.extension_points.options_pages import register_options_page

        register_options_page(PluginPage)

        # Verify the option was registered for this page
        registered = OptionsPage._registered_settings['test_plugin_page']
        self.assertEqual(len(registered), 1)
        self.assertEqual(registered[0].name, 'plugin_opt')
        self.assertEqual(registered[0].section, 'plugin.test-restore')

    def test_known_settings_no_collision_between_plugins(self):
        """Two plugins with same option name should not collide in profile groups."""
        from picard.config import (
            ConfigSection,
            get_config,
        )
        from picard.profile import (
            profile_groups_all_settings,
            profile_groups_reset,
        )

        profile_groups_reset()
        config = get_config()

        section1 = ConfigSection(config, 'plugin.uuid1')
        section1.display_name = 'Plugin 1'
        section1.register_option('greeting', 'hello', title='Greeting', in_profile=True)

        section2 = ConfigSection(config, 'plugin.uuid2')
        section2.display_name = 'Plugin 2'
        section2.register_option('greeting', 'hi', title='Greeting', in_profile=True)

        # Both should be in _known_settings with distinct keys
        known = profile_groups_all_settings()
        self.assertIn('plugin.uuid1/greeting', known)
        self.assertIn('plugin.uuid2/greeting', known)
