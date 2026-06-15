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

        from picard.ui.options import OptionsPage, PageOptionConfigs

        BoolOption('setting', 'test_no_profile_opt', False)

        class TestPage(OptionsPage):
            NAME = 'test_warn_page'
            TITLE = 'Test'
            PARENT = None
            SORT_ORDER = 9999
            OPTIONS: PageOptionConfigs = {
                'test_no_profile_opt': {'widgets': ['some_widget']},
            }

        with patch('picard.extension_points.options_pages.log') as mock_log:
            register_options_page(TestPage)
        mock_log.warning.assert_called_once()
        self.assertIn('in_profile=False', mock_log.warning.call_args[0][0])

    def test_restore_defaults_no_profile_core(self):
        """Without profiles, restore_defaults resets to default and doesn't persist."""
        from picard.config import (
            TextOption,
            get_config,
        )

        from picard.ui.options import OptionsPage, PageOptionConfigs

        config = get_config()
        TextOption('setting', 'test_rd_core', 'default_value', in_profile=True)
        config.setting['test_rd_core'] = 'user_value'

        class CorePage(OptionsPage):
            NAME = 'test_rd_core_page'
            TITLE = 'Test'
            PARENT = None
            SORT_ORDER = 9999
            OPTION_SECTION = 'setting'
            OPTIONS: PageOptionConfigs = {'test_rd_core': {}}

        from picard.extension_points.options_pages import register_options_page

        register_options_page(CorePage)

        page = CorePage.__new__(CorePage)
        page.load = lambda: None

        page.restore_defaults()

        # After restore_defaults (without save), value should be back to user_value
        self.assertEqual(config.setting['test_rd_core'], 'user_value')

    def test_known_settings_no_collision_between_plugins(self):
        """Two plugins with same option name should not collide in profile groups."""
        from picard.config import (
            ProfileConfigSection,
            get_config,
        )
        from picard.profile import (
            profile_groups_all_settings,
            profile_groups_reset,
        )

        profile_groups_reset()
        config = get_config()

        section1 = ProfileConfigSection(config, 'plugin.uuid1')
        section1.display_name = 'Plugin 1'
        section1.register_option('greeting', 'hello', title='Greeting', in_profile=True)

        section2 = ProfileConfigSection(config, 'plugin.uuid2')
        section2.display_name = 'Plugin 2'
        section2.register_option('greeting', 'hi', title='Greeting', in_profile=True)

        # Both should be in _known_settings with distinct keys
        known = profile_groups_all_settings()
        self.assertIn('plugin.uuid1/greeting', known)
        self.assertIn('plugin.uuid2/greeting', known)
