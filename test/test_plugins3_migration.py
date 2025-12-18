# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import tempfile
import unittest


try:
    import tomllib
except ImportError:
    import tomli as tomllib


class TestPluginMigration(unittest.TestCase):
    """Test V2 to V3 plugin migration tool."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.scripts_path = Path(__file__).parent.parent / 'scripts'
        self.original_path_len = len(sys.path)

        # Skip if migrate_plugin.py doesn't exist (e.g., when running from installed package)
        if not (self.scripts_path / 'migrate_plugin.py').exists():
            self.skipTest('migrate_plugin.py not found (running from installed package)')

    def tearDown(self):
        import shutil

        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Clean up sys.path
        while len(sys.path) > self.original_path_len:
            sys.path.pop(0)
        # Clean up imported module
        if 'migrate_plugin' in sys.modules:
            del sys.modules['migrate_plugin']

    def test_migrate_simple_plugin(self):
        """Test migrating a simple V2 plugin."""
        v2_plugin = '''# -*- coding: utf-8 -*-
PLUGIN_NAME = "Test Plugin"
PLUGIN_AUTHOR = "Test Author"
PLUGIN_DESCRIPTION = "A test plugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.metadata import register_track_metadata_processor

def process_metadata(album, metadata, track, release):
    metadata['test'] = 'value'

register_track_metadata_processor(process_metadata)
'''

        input_file = self.temp_path / 'test_plugin.py'
        input_file.write_text(v2_plugin)

        # Import migration tool
        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        output_dir = self.temp_path / 'test_plugin_v3'
        result = migrate_plugin.migrate_plugin(str(input_file), str(output_dir))

        self.assertEqual(result, 0)
        self.assertTrue((output_dir / 'MANIFEST.toml').exists())
        self.assertTrue((output_dir / '__init__.py').exists())

        # Validate MANIFEST using tomllib

        with open(output_dir / 'MANIFEST.toml', 'rb') as f:
            data = tomllib.load(f)
            self.assertEqual(data['name'], 'Test Plugin')
            self.assertEqual(data['authors'], ['Test Author'])

        # Check code conversion
        code = (output_dir / '__init__.py').read_text()
        self.assertNotIn('PLUGIN_NAME', code)
        self.assertNotIn('PLUGIN_AUTHOR', code)
        # Module-level register call should be removed
        self.assertNotIn('\nregister_track_metadata_processor(process_metadata)', code)
        self.assertIn('def enable(api: PluginApi):', code)
        self.assertIn('api.register_track_metadata_processor(process_metadata)', code)

    def test_migrate_plugin_with_long_description(self):
        """Test migrating plugin with description > 200 chars."""
        long_desc = "A" * 250
        v2_plugin = f'''PLUGIN_NAME = "Long Desc"
PLUGIN_AUTHOR = "Author"
PLUGIN_DESCRIPTION = "{long_desc}"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
'''

        input_file = self.temp_path / 'long_desc.py'
        input_file.write_text(v2_plugin)

        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        output_dir = self.temp_path / 'long_desc_v3'
        migrate_plugin.migrate_plugin(str(input_file), str(output_dir))

        with open(output_dir / 'MANIFEST.toml', 'rb') as f:
            data = tomllib.load(f)
            # Description should be truncated
            self.assertLessEqual(len(data['description']), 200)
            # Long description should have full text
            self.assertEqual(len(data['long_description']), 250)

    def test_migrate_plugin_with_quotes_in_description(self):
        """Test migrating plugin with quotes in description."""
        v2_plugin = '''PLUGIN_NAME = "Quote Test"
PLUGIN_AUTHOR = "Author"
PLUGIN_DESCRIPTION = 'Test "quoted" text'
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
'''

        input_file = self.temp_path / 'quote_test.py'
        input_file.write_text(v2_plugin)

        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        output_dir = self.temp_path / 'quote_test_v3'
        migrate_plugin.migrate_plugin(str(input_file), str(output_dir))

        with open(output_dir / 'MANIFEST.toml', 'rb') as f:
            data = tomllib.load(f)
            self.assertIn('quoted', data['description'])

    def test_plugin_name_replacement(self):
        """Test that PLUGIN_NAME references are replaced in code."""
        v2_plugin = '''PLUGIN_NAME = "Name Test"
PLUGIN_AUTHOR = "Author"
PLUGIN_DESCRIPTION = "Test"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import log

def my_function():
    log.debug("%s: Starting" % PLUGIN_NAME)
    log.info(
        "%s: Multi-line",
        PLUGIN_NAME,
    )
'''

        input_file = self.temp_path / 'name_test.py'
        input_file.write_text(v2_plugin)

        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        output_dir = self.temp_path / 'name_test_v3'
        migrate_plugin.migrate_plugin(str(input_file), str(output_dir))

        code = (output_dir / '__init__.py').read_text()
        self.assertNotIn('PLUGIN_NAME', code)
        self.assertEqual(code.count('"Name Test"'), 2)

    def test_migrate_plugin_action(self):
        """Test migrating a simple V2 plugin."""
        v2_plugin = '''# -*- coding: utf-8 -*-
PLUGIN_NAME = "Test Plugin"
PLUGIN_AUTHOR = "Test Author"
PLUGIN_DESCRIPTION = "A test plugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.ui.itemviews import BaseAction, register_album_action

class MyAlbumAction(BaseAction):
    NAME = 'My Action'

    def callback(self, objs):
        pass

register_album_action(MyAlbumAction())
'''

        input_file = self.temp_path / 'test_plugin.py'
        input_file.write_text(v2_plugin)

        # Import migration tool
        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        output_dir = self.temp_path / 'test_plugin_v3'
        result = migrate_plugin.migrate_plugin(str(input_file), str(output_dir))

        self.assertEqual(result, 0)
        self.assertTrue((output_dir / 'MANIFEST.toml').exists())
        self.assertTrue((output_dir / '__init__.py').exists())

        # Validate MANIFEST using tomllib

        with open(output_dir / 'MANIFEST.toml', 'rb') as f:
            data = tomllib.load(f)
            self.assertEqual(data['name'], 'Test Plugin')
            self.assertEqual(data['authors'], ['Test Author'])

        # Check code conversion
        code = (output_dir / '__init__.py').read_text()
        print(code)

        # Action class should have TITLE instead of NAME
        self.assertNotIn("    NAME = 'My Action'", code)
        self.assertIn('    TITLE = "My Action"', code)

        # Action class register should be called
        self.assertNotIn('\nregister_track_metadata_processor(MyAlbumAction())', code)
        self.assertIn('def enable(api: PluginApi):', code)
        self.assertIn('  api.register_album_action(MyAlbumAction)', code)
