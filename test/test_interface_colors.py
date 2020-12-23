# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Laurent Monin
# Copyright (C) 2020 Philipp Wolfer
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

from PyQt5.QtGui import QColor

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
    }
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
            self.assertEqual(interface_colors.get_color_description('entity_error'), default_colors['entity_error'].description)
            self.assertEqual(interface_colors.get_qcolor('entity_error'), QColor('#000000'))

    def test_interface_colors_default(self):
        self.assertIsInstance(interface_colors, InterfaceColors)
