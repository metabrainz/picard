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

from test.test_config import TestPicardConfigCommon

from picard.config import (
    BoolOption,
    ListOption,
    Option,
    TextOption,
)
from picard.profiles.importer import (
    ProfileImportError,
    import_profile,
)


MINIMAL_PROFILE = """\
[profile]
title = "Test Profile"
picard_version = "3.0.0"
"""

PROFILE_WITH_SETTINGS = """\
[profile]
title = "Test Profile"
picard_version = "3.0.0"

[settings]
standardize_artists = true
write_id3v23 = false
"""

PROFILE_WITH_SCRIPTS = """\
[profile]
title = "Scripted Profile"
picard_version = "3.0.0"

[scripts.naming]
id = "test-uuid-123"
title = "My Naming Script"
author = "Test Author"
description = "A script for testing"
license = "GPL-2.0"
version = "2.0"
last_updated = "2026-06-21 12:00:00 UTC"
script_language_version = "1.1"
script = '''
$if2(%albumartist%,%artist%)/%album%/
$num(%tracknumber%,2) %title%
'''

[[scripts.tagging]]
title = "Multi-valued artists"
script = "$setmulti(albumartists,%_albumartists%)"

[[scripts.tagging]]
title = "Date handling"
script = "$set(releasedate,%date%)"
"""

PROFILE_WITH_PRESET = """\
[profile]
title = "Preset Profile"
picard_version = "3.0.0"

[scripts.naming]
id = "Preset 1"
title = "Default file naming script"
preset = true
script = "some content"
"""


class TestProfileImport(TestPicardConfigCommon):
    def setUp(self):
        super().setUp()
        ListOption.add_if_missing('profiles', 'user_profiles', [])
        Option.add_if_missing('profiles', 'user_profile_settings', {})
        Option('setting', 'file_renaming_scripts', {})
        self.config.profiles['user_profiles'] = []
        self.config.profiles['user_profile_settings'] = {}

    def test_import_minimal_profile(self):
        result = import_profile(self.config, MINIMAL_PROFILE)

        self.assertEqual(result.title, 'Test Profile')
        self.assertIsNotNone(result.profile_id)
        profiles = self.config.profiles['user_profiles']
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0]['title'], 'Test Profile')
        self.assertFalse(profiles[0]['enabled'])

    def test_import_profile_enabled(self):
        result = import_profile(self.config, MINIMAL_PROFILE, enabled=True)

        profiles = self.config.profiles['user_profiles']
        self.assertTrue(profiles[0]['enabled'])
        self.assertEqual(result.profile_id, profiles[0]['id'])

    def test_import_settings(self):
        BoolOption('setting', 'standardize_artists', False, title="Standardize", in_profile=True)
        BoolOption('setting', 'write_id3v23', True, title="Write ID3v2.3", in_profile=True)

        result = import_profile(self.config, PROFILE_WITH_SETTINGS)

        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        self.assertTrue(settings['standardize_artists'])
        self.assertFalse(settings['write_id3v23'])

    def test_import_unknown_options_skipped(self):
        BoolOption('setting', 'standardize_artists', False, title="Standardize", in_profile=True)
        # write_id3v23 not registered — simulates unknown option

        result = import_profile(self.config, PROFILE_WITH_SETTINGS)

        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        self.assertTrue(settings['standardize_artists'])
        self.assertNotIn('write_id3v23', settings)
        self.assertIn('write_id3v23', result.skipped_options)
        self.assertEqual(len(result.warnings), 1)

    def test_import_non_profile_option_skipped(self):
        # Option exists but in_profile=False — cannot be overridden by profile
        BoolOption('setting', 'standardize_artists', False, title="Standardize", in_profile=False)

        toml = """\
[profile]
title = "Test"
picard_version = "3.0.0"

[settings]
standardize_artists = true
"""
        result = import_profile(self.config, toml)

        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        self.assertNotIn('standardize_artists', settings)
        self.assertIn('standardize_artists', result.skipped_options)

    def test_import_naming_script(self):
        TextOption('setting', 'active_file_naming_script_id', '', title="Script", in_profile=True)

        result = import_profile(self.config, PROFILE_WITH_SCRIPTS)

        # Script registered in global dict
        scripts = self.config.setting['file_renaming_scripts']
        self.assertIn('test-uuid-123', scripts)
        self.assertEqual(scripts['test-uuid-123']['title'], 'My Naming Script')
        self.assertIn('%albumartist%', scripts['test-uuid-123']['script'])
        # Metadata fields preserved
        self.assertEqual(scripts['test-uuid-123']['author'], 'Test Author')
        self.assertEqual(scripts['test-uuid-123']['description'], 'A script for testing')
        self.assertEqual(scripts['test-uuid-123']['license'], 'GPL-2.0')
        self.assertEqual(scripts['test-uuid-123']['version'], '2.0')
        self.assertEqual(scripts['test-uuid-123']['last_updated'], '2026-06-21 12:00:00 UTC')
        self.assertEqual(scripts['test-uuid-123']['script_language_version'], '1.1')

        # Profile references the script
        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        self.assertEqual(settings['active_file_naming_script_id'], 'test-uuid-123')

    def test_import_naming_script_id_collision(self):
        TextOption('setting', 'active_file_naming_script_id', '', title="Script", in_profile=True)

        # Pre-existing script with same ID
        self.config.setting['file_renaming_scripts'] = {
            'test-uuid-123': {'id': 'test-uuid-123', 'title': 'Existing', 'script': 'old'},
        }

        result = import_profile(self.config, PROFILE_WITH_SCRIPTS)

        # A new ID was generated, old script untouched
        scripts = self.config.setting['file_renaming_scripts']
        self.assertIn('test-uuid-123', scripts)
        self.assertEqual(scripts['test-uuid-123']['title'], 'Existing')  # unchanged

        # New script has different ID
        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        new_id = settings['active_file_naming_script_id']
        self.assertNotEqual(new_id, 'test-uuid-123')
        self.assertIn(new_id, scripts)
        self.assertEqual(scripts[new_id]['title'], 'My Naming Script')

    def test_import_preset_naming_script(self):
        TextOption('setting', 'active_file_naming_script_id', '', title="Script", in_profile=True)

        result = import_profile(self.config, PROFILE_WITH_PRESET)

        # Preset is referenced by ID, not registered in file_renaming_scripts
        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        self.assertEqual(settings['active_file_naming_script_id'], 'Preset 1')

        scripts = self.config.setting['file_renaming_scripts']
        self.assertNotIn('Preset 1', scripts)

    def test_import_tagger_scripts(self):
        ListOption('setting', 'list_of_scripts', [], title="Scripts", in_profile=True)
        BoolOption('setting', 'enable_tagger_scripts', False, title="Enable scripts", in_profile=True)

        result = import_profile(self.config, PROFILE_WITH_SCRIPTS)

        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        scripts = settings['list_of_scripts']
        self.assertEqual(len(scripts), 2)
        self.assertEqual(scripts[0][1], 'Multi-valued artists')
        self.assertEqual(scripts[1][1], 'Date handling')
        # All imported scripts are enabled by default
        self.assertTrue(scripts[0][2])
        self.assertTrue(scripts[1][2])
        # Master toggle is enabled
        self.assertTrue(settings['enable_tagger_scripts'])

    def test_import_tagger_scripts_deduplication(self):
        ListOption('setting', 'list_of_scripts', [], title="Scripts", in_profile=True)
        BoolOption('setting', 'enable_tagger_scripts', False, title="Enable scripts", in_profile=True)

        # Import once
        import_profile(self.config, PROFILE_WITH_SCRIPTS)

        # Import the same profile again (simulating re-import)
        # Reset profiles to import fresh but keep the same TOML
        self.config.profiles['user_profiles'] = []
        self.config.profiles['user_profile_settings'] = {}
        toml_with_duplicate = """\
[profile]
title = "Test"
picard_version = "3.0.0"

[[scripts.tagging]]
title = "Multi-valued artists"
script = "$setmulti(albumartists,%_albumartists%)"

[[scripts.tagging]]
title = "Multi-valued artists"
script = "$setmulti(albumartists,%_albumartists%)"
"""
        result = import_profile(self.config, toml_with_duplicate)

        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        scripts = settings['list_of_scripts']
        # Only one copy (deduplication by title+content)
        self.assertEqual(len(scripts), 1)
        self.assertIn('1 duplicate', result.warnings[0])

    def test_import_tagger_scripts_with_enabled_field(self):
        ListOption('setting', 'list_of_scripts', [], title="Scripts", in_profile=True)
        BoolOption('setting', 'enable_tagger_scripts', False, title="Enable scripts", in_profile=True)

        toml = """\
[profile]
title = "Backup"
picard_version = "3.0.0"

[[scripts.tagging]]
title = "Enabled"
enabled = true
script = "$set(a,b)"

[[scripts.tagging]]
title = "Disabled"
enabled = false
script = "$noop()"
"""
        result = import_profile(self.config, toml)

        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        scripts = settings['list_of_scripts']
        self.assertEqual(len(scripts), 2)
        self.assertTrue(scripts[0][2])  # enabled
        self.assertFalse(scripts[1][2])  # disabled

    def test_import_duplicate_title_gets_copy_suffix(self):
        # Create an existing profile with the same title
        self.config.profiles['user_profiles'] = [
            {'id': 'existing', 'title': 'Test Profile', 'enabled': True, 'position': 0},
        ]

        result = import_profile(self.config, MINIMAL_PROFILE)

        self.assertEqual(result.title, 'Test Profile (copy)')

    def test_import_invalid_toml_raises(self):
        with self.assertRaises(ProfileImportError):
            import_profile(self.config, "not valid [[ toml content")

    def test_import_missing_profile_section_raises(self):
        with self.assertRaises(ProfileImportError):
            import_profile(self.config, "[settings]\nfoo = true\n")

    def test_import_missing_title_raises(self):
        with self.assertRaises(ProfileImportError):
            import_profile(self.config, "[profile]\npicard_version = '3.0'\n")

    def test_import_unsupported_format_version_raises(self):
        toml = """\
[profile]
title = "Future Profile"
format_version = 999
picard_version = "4.0.0"
"""
        with self.assertRaises(ProfileImportError) as ctx:
            import_profile(self.config, toml)
        self.assertIn("Unsupported profile format version", str(ctx.exception))

    def test_import_missing_format_version_defaults_to_1(self):
        """Profiles without format_version (exported before this field existed) are accepted."""
        result = import_profile(self.config, MINIMAL_PROFILE)
        self.assertEqual(result.title, 'Test Profile')

    def test_import_current_format_version_accepted(self):
        from picard.profiles import PROFILE_FORMAT_VERSION

        toml = f"""\
[profile]
title = "Current Format"
format_version = {PROFILE_FORMAT_VERSION}
picard_version = "3.0.0"
"""
        result = import_profile(self.config, toml)
        self.assertEqual(result.title, 'Current Format')

    def test_import_partial_profile_scripts_only(self):
        ListOption('setting', 'list_of_scripts', [], title="Scripts", in_profile=True)
        BoolOption('setting', 'enable_tagger_scripts', False, title="Enable scripts", in_profile=True)

        toml = """\
[profile]
title = "Scripts Only"
picard_version = "3.0.0"

[[scripts.tagging]]
title = "My Script"
script = "$set(foo,bar)"
"""
        result = import_profile(self.config, toml)

        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        self.assertIn('list_of_scripts', settings)
        self.assertNotIn('standardize_artists', settings)

    def test_import_tuple_conversion(self):
        ListOption('setting', 'ca_providers', [('a', True)], title="Providers", in_profile=True)

        toml = """\
[profile]
title = "Test"
picard_version = "3.0.0"

[settings]
ca_providers = [["Cover Art Archive", true], ["UrlRelationships", false]]
"""
        result = import_profile(self.config, toml)

        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        # Inner lists should be converted to tuples since default has tuples
        expected = [('Cover Art Archive', True), ('UrlRelationships', False)]
        self.assertEqual(settings['ca_providers'], expected)

    def test_replace_fully_overrides_scripts(self):
        """Replace import fully overrides the profile's scripts.

        When using --replace, the imported file becomes the new truth.
        Existing scripts not in the import (e.g. disabled scripts excluded
        from share-mode exports) are replaced, not preserved.
        """
        ListOption('setting', 'list_of_scripts', [], title="Scripts", in_profile=True)
        BoolOption('setting', 'enable_tagger_scripts', False, title="Enable scripts", in_profile=True)

        # Existing profile has two scripts: one enabled, one disabled
        existing_id = 'existing-profile-uuid'
        self.config.profiles['user_profiles'] = [
            {'id': existing_id, 'title': 'My profile', 'enabled': True, 'position': 0},
        ]
        self.config.profiles['user_profile_settings'] = {
            existing_id: {
                'enable_tagger_scripts': True,
                'list_of_scripts': [
                    (0, 'Enabled Script', True, '$set(foo,bar)'),
                    (1, 'Disabled Script', False, '$set(baz,qux)'),
                ],
            },
        }

        # Import with replace — only the enabled script is in the file
        toml_share_export = """\
[profile]
title = "My profile"
picard_version = "3.0.0"

[[scripts.tagging]]
title = "Enabled Script"
script = "$set(foo,bar)"
"""
        result = import_profile(self.config, toml_share_export, replace_id=existing_id)

        settings = self.config.profiles['user_profile_settings'][result.profile_id]
        scripts = settings['list_of_scripts']

        # Only the imported script should be present — replace is a full override
        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0][1], 'Enabled Script')
