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

from test.picardtestcase import PicardTestCase

from picard.profile_settings_upgrades import upgrade_settings_for_import


class TestProfileSettingsUpgrades(PicardTestCase):
    def test_rename_windows_compatible_filenames(self):
        settings = {'windows_compatible_filenames': True}
        upgrade_settings_for_import(settings, '1.2.0')
        self.assertNotIn('windows_compatible_filenames', settings)
        self.assertTrue(settings['windows_compatibility'])

    def test_rename_dont_write_tags_reversed(self):
        settings = {'dont_write_tags': False}
        upgrade_settings_for_import(settings, '2.9.0')
        self.assertNotIn('dont_write_tags', settings)
        self.assertTrue(settings['enable_tag_saving'])

    def test_rename_dont_write_tags_reversed_true(self):
        settings = {'dont_write_tags': True}
        upgrade_settings_for_import(settings, '2.9.0')
        self.assertFalse(settings['enable_tag_saving'])

    def test_rename_selected_file_naming_script_id(self):
        settings = {'selected_file_naming_script_id': 'my-uuid'}
        upgrade_settings_for_import(settings, '3.0.0b4')
        self.assertNotIn('selected_file_naming_script_id', settings)
        self.assertEqual(settings['active_file_naming_script_id'], 'my-uuid')

    def test_ca_providers_whitelist_rename(self):
        settings = {'ca_providers': [('Whitelist', True), ('Cover Art Archive', True)]}
        upgrade_settings_for_import(settings, '2.4.0')
        self.assertEqual(
            settings['ca_providers'],
            [('UrlRelationships', True), ('Cover Art Archive', True)],
        )

    def test_cover_format_lowercase(self):
        settings = {
            'cover_tags_convert_to_format': 'JPEG',
            'cover_file_convert_to_format': 'PNG',
        }
        upgrade_settings_for_import(settings, '3.0.0dev9')
        self.assertEqual(settings['cover_tags_convert_to_format'], 'jpeg')
        self.assertEqual(settings['cover_file_convert_to_format'], 'png')

    def test_matchedtracks_fix(self):
        settings = {
            'list_of_scripts': [
                (0, 'Script', True, '$set(foo,$matchedtracks(bar))'),
            ],
        }
        upgrade_settings_for_import(settings, '3.0.0dev10')
        self.assertEqual(
            settings['list_of_scripts'][0][3],
            '$set(foo,$matchedtracks())',
        )

    def test_genre_renames(self):
        settings = {
            'max_tags': 10,
            'min_tag_usage': 80,
            'only_my_tags': True,
            'artists_tags': False,
        }
        upgrade_settings_for_import(settings, '2.0.0')
        self.assertEqual(settings['max_genres'], 10)
        self.assertEqual(settings['min_genre_usage'], 80)
        self.assertTrue(settings['only_my_genres'])
        self.assertFalse(settings['artists_genres'])
        self.assertNotIn('max_tags', settings)

    def test_no_upgrades_for_current_version(self):
        settings = {'rename_files': True}
        # Use a very high version — no upgrades should apply
        applied = upgrade_settings_for_import(settings, '99.0.0')
        self.assertEqual(applied, [])
        self.assertEqual(settings, {'rename_files': True})

    def test_invalid_version_string(self):
        settings = {'rename_files': True}
        applied = upgrade_settings_for_import(settings, 'not-a-version')
        self.assertEqual(applied, [])

    def test_artist_locales_rename(self):
        settings = {'artist_locales': ['fr', 'de']}
        upgrade_settings_for_import(settings, '3.0.0b1')
        self.assertNotIn('artist_locales', settings)
        self.assertEqual(settings['translation_locales'], ['fr', 'de'])

    def test_multiple_upgrades_applied_in_order(self):
        """A profile from version 1.0 should get all upgrades applied."""
        settings = {
            'windows_compatible_filenames': True,
            'save_only_front_images_to_tags': False,
            'dont_write_tags': True,
        }
        applied = upgrade_settings_for_import(settings, '1.0.0')
        # All three should be renamed
        self.assertIn('windows_compatibility', settings)
        self.assertIn('embed_only_one_front_image', settings)
        self.assertIn('enable_tag_saving', settings)
        # Old names gone
        self.assertNotIn('windows_compatible_filenames', settings)
        self.assertNotIn('save_only_front_images_to_tags', settings)
        self.assertNotIn('dont_write_tags', settings)
        # Reversed boolean
        self.assertFalse(settings['enable_tag_saving'])
        self.assertTrue(len(applied) >= 3)
