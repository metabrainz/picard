# -*- coding: utf-8 -*-
#
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from pathlib import Path
from unittest.mock import Mock

from PyQt6.QtGui import QColor

from test.picardtestcase import PicardTestCase
from test.plugins3.helpers import load_plugin_manifest

from picard.plugin3.api import PluginApi

from picard.ui.colors import (
    _COLOR_DESCRIPTIONS,
    _DEFAULT_COLORS,
    UnknownColorException,
    interface_colors,
    unregister_color,
)


class TestPluginApiColors(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.api = PluginApi(load_plugin_manifest('example'), Mock(), Mock(), Path(''))
        # Clean up any colors registered by this test
        self._registered_keys = []

    def tearDown(self):
        # Ensure cleanup of any registered colors
        self.api.unregister_all_colors()
        super().tearDown()

    def test_register_color_both_values(self):
        """Test registering a color with both light and dark values."""
        self.api.register_color(
            'test_color',
            title="Test Color",
            light_value='#FF0000',
            dark_value='#AA0000',
        )
        key = self.api._color_key('test_color')
        self.assertIn(key, _DEFAULT_COLORS['light'])
        self.assertIn(key, _DEFAULT_COLORS['dark'])
        self.assertEqual(_DEFAULT_COLORS['light'][key].value, '#ff0000')
        self.assertEqual(_DEFAULT_COLORS['dark'][key].value, '#aa0000')

    def test_register_color_light_only(self):
        """Test registering with only light_value sets dark to same."""
        self.api.register_color(
            'light_only',
            title="Light Only",
            light_value='#00FF00',
        )
        key = self.api._color_key('light_only')
        self.assertIn(key, _DEFAULT_COLORS['light'])
        self.assertIn(key, _DEFAULT_COLORS['dark'])
        self.assertEqual(_DEFAULT_COLORS['light'][key].value, '#00ff00')
        self.assertEqual(_DEFAULT_COLORS['dark'][key].value, '#00ff00')

    def test_register_color_dark_only(self):
        """Test registering with only dark_value sets light to same."""
        self.api.register_color(
            'dark_only',
            title="Dark Only",
            dark_value='#0000FF',
        )
        key = self.api._color_key('dark_only')
        self.assertIn(key, _DEFAULT_COLORS['light'])
        self.assertIn(key, _DEFAULT_COLORS['dark'])
        self.assertEqual(_DEFAULT_COLORS['light'][key].value, '#0000ff')
        self.assertEqual(_DEFAULT_COLORS['dark'][key].value, '#0000ff')

    def test_register_color_no_values_raises(self):
        """Test that registering without any value raises ValueError."""
        with self.assertRaises(ValueError):
            self.api.register_color('bad_color', title="Bad")

    def test_register_color_invalid_name_raises(self):
        """Test that invalid color names are rejected."""
        with self.assertRaises(ValueError):
            self.api.register_color('invalid:name', title="Bad", light_value='red')
        with self.assertRaises(ValueError):
            self.api.register_color('invalid.name', title="Bad", light_value='red')
        with self.assertRaises(ValueError):
            self.api.register_color('', title="Bad", light_value='red')
        with self.assertRaises(ValueError):
            self.api.register_color('123start', title="Bad", light_value='red')

    def test_register_color_valid_names(self):
        """Test that valid color names are accepted."""
        self.api.register_color('simple', title="Simple", light_value='red')
        self.api.register_color('with_underscore', title="Underscored", light_value='blue')
        self.api.register_color('_leading', title="Leading", light_value='green')
        self.api.register_color('CamelCase', title="Camel", light_value='yellow')

    def test_register_color_description_group(self):
        """Test that the color description uses the plugin's manifest name as group."""
        self.api.register_color('grouped', title="My Color", light_value='#123456')
        key = self.api._color_key('grouped')
        self.assertIn(key, _COLOR_DESCRIPTIONS)
        desc = _COLOR_DESCRIPTIONS[key]
        self.assertEqual(desc.title, "My Color")
        self.assertEqual(desc.group, self.api.manifest.name_i18n())

    def test_get_plugin_color(self):
        """Test reading a plugin-registered color."""
        self.api.register_color('my_color', title="My Color", light_value='#ABCDEF')
        color = self.api.get_plugin_color('my_color')
        self.assertEqual(color, '#abcdef')

    def test_get_plugin_qcolor(self):
        """Test reading a plugin-registered color as QColor."""
        self.api.register_color('my_color', title="My Color", light_value='#FF8800')
        qcolor = self.api.get_plugin_qcolor('my_color')
        self.assertIsInstance(qcolor, QColor)
        self.assertEqual(qcolor.name(), '#ff8800')

    def test_get_plugin_color_unknown_raises(self):
        """Test that reading an unregistered plugin color raises."""
        with self.assertRaises(UnknownColorException):
            self.api.get_plugin_color('nonexistent')

    def test_get_color_core(self):
        """Test reading a core interface color."""
        color = self.api.get_color('entity_error')
        self.assertEqual(color, interface_colors.get_color('entity_error'))

    def test_get_qcolor_core(self):
        """Test reading a core interface color as QColor."""
        qcolor = self.api.get_qcolor('entity_error')
        self.assertIsInstance(qcolor, QColor)
        self.assertEqual(qcolor.name(), interface_colors.get_color('entity_error'))

    def test_get_color_unknown_raises(self):
        """Test that reading an unknown core color raises."""
        with self.assertRaises(UnknownColorException):
            self.api.get_color('totally_nonexistent_color')

    def test_is_dark_theme(self):
        """Test is_dark_theme property."""
        self.assertIsInstance(self.api.is_dark_theme, bool)

    def test_unregister_color(self):
        """Test unregistering a single color."""
        self.api.register_color('temp', title="Temp", light_value='#111111')
        key = self.api._color_key('temp')
        self.assertIn(key, _DEFAULT_COLORS['light'])
        self.api.unregister_color('temp')
        self.assertNotIn(key, _DEFAULT_COLORS['light'])
        self.assertNotIn(key, _DEFAULT_COLORS['dark'])
        self.assertNotIn(key, _COLOR_DESCRIPTIONS)

    def test_unregister_all_colors(self):
        """Test unregistering all plugin colors at once."""
        self.api.register_color('color_a', title="A", light_value='#111111')
        self.api.register_color('color_b', title="B", light_value='#222222')
        key_a = self.api._color_key('color_a')
        key_b = self.api._color_key('color_b')
        self.assertIn(key_a, _DEFAULT_COLORS['light'])
        self.assertIn(key_b, _DEFAULT_COLORS['light'])
        self.api.unregister_all_colors()
        self.assertNotIn(key_a, _DEFAULT_COLORS['light'])
        self.assertNotIn(key_b, _DEFAULT_COLORS['light'])
        self.assertEqual(self.api._registered_colors, [])

    def test_color_namespace_isolation(self):
        """Test that plugin colors cannot collide with core colors."""
        # Register a plugin color with same name as a core color
        self.api.register_color('entity_error', title="Plugin Error", light_value='#FFFFFF')
        # Plugin color is namespaced differently
        plugin_color = self.api.get_plugin_color('entity_error')
        core_color = self.api.get_color('entity_error')
        # They should be different because the plugin one is #FFFFFF
        self.assertEqual(plugin_color, '#ffffff')
        self.assertNotEqual(plugin_color, core_color)

    def test_register_color_named_css_color(self):
        """Test registering with CSS named colors."""
        self.api.register_color('named', title="Named", light_value='red', dark_value='darkred')
        color_light = _DEFAULT_COLORS['light'][self.api._color_key('named')].value
        color_dark = _DEFAULT_COLORS['dark'][self.api._color_key('named')].value
        self.assertEqual(color_light, QColor('red').name())
        self.assertEqual(color_dark, QColor('darkred').name())

    def test_register_color_invalid_light_raises(self):
        """Test that invalid light_value raises ValueError."""
        with self.assertRaises(ValueError):
            self.api.register_color('bad', title="Bad", light_value='notacolor', dark_value='#00FF00')

    def test_register_color_invalid_dark_raises(self):
        """Test that invalid dark_value raises ValueError."""
        with self.assertRaises(ValueError):
            self.api.register_color('bad', title="Bad", light_value='#FF0000', dark_value='xyz')

    def test_register_color_both_invalid_raises(self):
        """Test that both values invalid raises ValueError."""
        with self.assertRaises(ValueError):
            self.api.register_color('bad', title="Bad", light_value='nope', dark_value='alsonope')


class TestUnregisterColor(PicardTestCase):
    """Test the module-level unregister_color function."""

    def test_unregister_existing_color(self):
        """Test unregistering a dynamically added color."""
        from picard.ui.colors import (
            ColorDescription,
            register_color,
        )

        register_color(
            ('light', 'dark'),
            'test_dynamic',
            '#AABBCC',
            description=ColorDescription(title="Test", group="Test"),
        )
        self.assertIn('test_dynamic', _DEFAULT_COLORS['light'])
        unregister_color('test_dynamic')
        self.assertNotIn('test_dynamic', _DEFAULT_COLORS['light'])
        self.assertNotIn('test_dynamic', _DEFAULT_COLORS['dark'])
        self.assertNotIn('test_dynamic', _COLOR_DESCRIPTIONS)

    def test_unregister_nonexistent_is_safe(self):
        """Test that unregistering a non-existent color doesn't raise."""
        unregister_color('totally_fake_color_key')


class TestColorAlphaSupport(PicardTestCase):
    """Test that colors with alpha are properly stored and retrieved."""

    def test_opaque_color_stored_as_rrggbb(self):
        """Opaque colors are stored as #RRGGBB (6 digits)."""
        from picard.ui.colors import _color_to_string

        c = QColor('#FF0000')
        self.assertEqual(_color_to_string(c), '#ff0000')

    def test_alpha_color_stored_as_aarrggbb(self):
        """Colors with alpha < 255 are stored as #AARRGGBB (8 digits)."""
        from picard.ui.colors import _color_to_string

        c = QColor('#80FF0000')
        self.assertEqual(_color_to_string(c), '#80ff0000')

    def test_register_color_with_alpha(self):
        """Plugin can register a color with alpha."""
        from pathlib import Path
        from unittest.mock import Mock

        from test.plugins3.helpers import load_plugin_manifest

        from picard.plugin3.api import PluginApi

        api = PluginApi(load_plugin_manifest('example'), Mock(), Mock(), Path(''))
        api.register_color('semi_transparent', title="Semi", light_value='#80FF0000')
        color = api.get_plugin_color('semi_transparent')
        self.assertEqual(color, '#80ff0000')
        qcolor = api.get_plugin_qcolor('semi_transparent')
        self.assertEqual(qcolor.alpha(), 128)
        self.assertEqual(qcolor.red(), 255)
        api.unregister_all_colors()

    def test_shorthand_normalized_to_rrggbb(self):
        """Shorthand #RGB input is normalized to #RRGGBB."""
        from picard.ui.colors import _color_to_string

        c = QColor('#ABC')
        self.assertEqual(_color_to_string(c), '#aabbcc')
