# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020, 2022 Philipp Wolfer
# Copyright (C) 2020-2022, 2025 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from PyQt6.QtGui import QColor

from test.picardtestcase import PicardTestCase

from picard import config

from picard.ui.colors import (
    InterfaceColors,
    UnknownColorException,
    interface_colors,
)


settings = {
    'interface_colors': {
        'unknowncolor': '#deadbe',
        'entity_error': '#abcdef',
    },
    'interface_colors_dark': {
        'unknowncolor': '#deadbe',
        'entity_error': '#abcdef',
    },
}


class InterfaceColorsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(settings)

    def test_interface_colors(self):
        for key in ('interface_colors', 'interface_colors_dark'):
            interface_colors = InterfaceColors(dark_theme=key == 'interface_colors_dark')
            with self.assertRaises(UnknownColorException):
                interface_colors.get_color('testcolor')
            default_colors = interface_colors.default_colors
            self.assertEqual(interface_colors.get_color('entity_error'), default_colors['entity_error'].value)
            interface_colors.load_from_config()
            self.assertEqual(interface_colors.get_color('entity_error'), '#abcdef')
            self.assertEqual(interface_colors.get_colors()['entity_error'], '#abcdef')
            interface_colors.set_color('entity_error', '#000000')
            self.assertTrue(interface_colors.save_to_config())
            self.assertEqual(config.setting[key]['entity_error'], '#000000')
            self.assertNotIn('unknowncolor', config.setting[key])
            self.assertEqual(
                interface_colors.get_color_description('entity_error'),
                default_colors['entity_error'].description,
            )
            self.assertEqual(interface_colors.get_qcolor('entity_error'), QColor('#000000'))

    def test_interface_colors_default(self):
        self.assertIsInstance(interface_colors, InterfaceColors)

    def test_reload_switches_color_set(self):
        """Test that reload() picks up colors for the current theme."""
        # Create instance for light theme
        colors = InterfaceColors(dark_theme=False)
        colors.load_from_config()
        light_log_debug = colors.get_color('log_debug')

        # Switch to dark theme and reload
        colors._dark_theme = True
        colors.reload()
        dark_log_debug = colors.get_color('log_debug')

        # Dark and light should differ for log_debug
        self.assertNotEqual(light_log_debug, dark_log_debug)

    def test_reload_loads_user_config(self):
        """Test that reload() loads user customizations from config."""
        # Set a known value in config first
        config.setting['interface_colors'] = {'entity_error': '#112233'}
        colors = InterfaceColors(dark_theme=False)
        colors.reload()
        self.assertEqual(colors.get_color('entity_error'), '#112233')

    def test_theme_changed_triggers_reload(self):
        """Test that theme.theme_changed signal triggers interface_colors reload."""
        from picard.ui.theme import theme

        # Set distinct colors in dark config
        config.setting['interface_colors_dark'] = {'entity_error': '#aabbcc'}
        # Simulate a theme switch by emitting theme_changed
        # (normally apply_theme would set is_dark_theme first, but we can
        #  just verify the signal connection works by checking reload was called)
        original_dark = interface_colors._dark_theme
        interface_colors._dark_theme = True
        theme.theme_changed.emit()
        dark_error = interface_colors.get_color('entity_error')
        self.assertEqual(dark_error, '#aabbcc')
        # Restore
        interface_colors._dark_theme = original_dark
        interface_colors.reload()
