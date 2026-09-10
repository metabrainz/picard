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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from pathlib import Path
import shutil
import sys
import tempfile

from test.picardtestcase import PicardTestCase


try:
    import tomllib  # type: ignore[unresolved-import]
except ImportError:
    import tomli as tomllib


class TestPluginMigration(PicardTestCase):
    """Test V2 to V3 plugin migration tool."""

    def setUp(self):
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.scripts_path = Path(__file__).parent.parent.parent / 'scripts'
        self.original_path_len = len(sys.path)

        # Skip if migrate_plugin.py doesn't exist (e.g., when running from installed package)
        if not (self.scripts_path / 'migrate_plugin.py').exists():
            self.skipTest('migrate_plugin.py not found (running from installed package)')

    def tearDown(self):
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Clean up sys.path
        while len(sys.path) > self.original_path_len:
            sys.path.pop(0)
        # Clean up imported module
        if 'migrate_plugin' in sys.modules:
            del sys.modules['migrate_plugin']
        super().tearDown()

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

from picard.ui.itemviews import (BaseAction, register_album_action,)

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

    def test_track_processor_signature_rewritten_with_api(self):
        """A canonical v2 track processor signature is rewritten to the full v3 form."""
        v2_code = (
            "from picard.metadata import register_track_metadata_processor\n\n\n"
            "def process_track(album, metadata, track, release):\n"
            "    metadata['custom'] = 'value'\n\n\n"
            "register_track_metadata_processor(process_track)\n"
        )

        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        content, warnings = migrate_plugin.convert_plugin_code(v2_code, {'name': 'Test'})

        # v3 signature: api first, plus track_node/release_node
        self.assertIn('def process_track(api, track, metadata, track_node, release_node)', content)
        # No per-function "still lacks api" warning for a recognized signature
        joined = '\n'.join(warnings)
        self.assertNotIn('still lack the', joined)

    def test_album_processor_signature_rewritten_with_api(self):
        """A canonical v2 album processor signature is rewritten to the full v3 form."""
        v2_code = (
            "from picard.metadata import register_album_metadata_processor\n\n\n"
            "def process_album(album, metadata, release):\n"
            "    metadata['custom'] = 'value'\n\n\n"
            "register_album_metadata_processor(process_album)\n"
        )

        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        content, _warnings = migrate_plugin.convert_plugin_code(v2_code, {'name': 'Test'})
        self.assertIn('def process_album(api, album, metadata, release_node)', content)

    def test_non_canonical_processor_flagged_by_name(self):
        """A processor with non-canonical parameter names is NOT auto-rewritten,
        and the warning names the specific function that still needs 'api'."""
        v2_code = (
            "from picard.metadata import register_track_metadata_processor\n\n\n"
            "def my_proc(alb, meta, trk, rel):\n"
            "    meta['x'] = 'y'\n\n\n"
            "register_track_metadata_processor(my_proc)\n"
        )

        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        content, warnings = migrate_plugin.convert_plugin_code(v2_code, {'name': 'Test'})

        # Signature was not rewritten (still no 'api' first arg)
        self.assertIn('def my_proc(alb, meta, trk, rel)', content)
        # And the warning names it explicitly
        joined = '\n'.join(warnings)
        self.assertIn('still lack the', joined)
        self.assertIn('my_proc', joined)

    def test_file_to_track_processor_keeps_track_arg(self):
        """v2 file-to-track processor (track, file) -> v3 (api, track, file).

        The track argument must be retained (see docs/PLUGINSV3/API.md:
        register_file_post_addition_to_track_processor -> function(api, track, file)).
        """
        v2_code = (
            "from picard.file import register_file_post_addition_to_track_processor\n\n\n"
            "def get_lyrics(track, file):\n"
            "    pass\n\n\n"
            "register_file_post_addition_to_track_processor(get_lyrics)\n"
        )

        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        content, _warnings = migrate_plugin.convert_plugin_code(v2_code, {'name': 'Test'})
        self.assertIn('def get_lyrics(api, track, file)', content)

    def test_file_processor_gets_api_arg(self):
        """v2 file processor (file) -> v3 (api, file)."""
        v2_code = (
            "from picard.file import register_file_post_load_processor\n\n\n"
            "def on_load(file):\n"
            "    pass\n\n\n"
            "register_file_post_load_processor(on_load)\n"
        )

        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        content, _warnings = migrate_plugin.convert_plugin_code(v2_code, {'name': 'Test'})
        self.assertIn('def on_load(api, file)', content)

    def test_qualified_plugin_priority_converted(self):
        """A qualified PluginPriority reference (plugin.PluginPriority.HIGH) is
        converted to an integer without leaving the module qualifier behind.

        Regression: previously only the bare `PluginPriority.HIGH` was matched,
        producing `plugin.100`, which is a syntax error and cascaded into the
        registration call not being removed (observed migrating the real
        `instruments` v2 plugin).
        """
        v2_code = (
            "from picard import metadata\n"
            "from picard import plugin\n\n\n"
            "def add_instruments(album, metadata, track, release):\n"
            "    pass\n\n\n"
            "metadata.register_track_metadata_processor(\n"
            "    add_instruments, priority=plugin.PluginPriority.HIGH)\n"
        )

        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        content, _warnings = migrate_plugin.convert_plugin_code(v2_code, {'name': 'Test'})

        # Output must be valid Python
        import ast as _ast

        _ast.parse(content)
        # No mangled qualifier and no leftover module-level registration
        self.assertNotIn('plugin.100', content)
        self.assertNotIn('metadata.register_track_metadata_processor', content)
        # Registration moved into enable()
        self.assertIn('api.register_track_metadata_processor(add_instruments)', content)

    def test_migrated_output_is_valid_python(self):
        """migrate_plugin() writes syntactically valid Python and does not emit
        the "not valid Python" error for a normal plugin (output-validation
        safety net does not false-positive)."""
        import ast as _ast
        import contextlib
        import io

        v2_plugin = '''PLUGIN_NAME = "Valid Output"
PLUGIN_AUTHOR = "Author"
PLUGIN_DESCRIPTION = "Test"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.metadata import register_track_metadata_processor


def process_track(album, metadata, track, release):
    metadata['custom'] = 'value'


register_track_metadata_processor(process_track)
'''

        input_file = self.temp_path / 'valid_output.py'
        input_file.write_text(v2_plugin)

        sys.path.insert(0, str(self.scripts_path))
        import migrate_plugin

        output_dir = self.temp_path / 'valid_output_v3'
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            migrate_plugin.migrate_plugin(str(input_file), str(output_dir))

        code = (output_dir / '__init__.py').read_text()
        # Parses cleanly
        _ast.parse(code)
        # And the validation safety net did not flag it
        self.assertNotIn('not valid Python', buf.getvalue())
