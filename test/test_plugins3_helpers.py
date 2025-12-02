# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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

from io import StringIO
import json
from pathlib import Path
from unittest.mock import Mock

from test.picardtestcase import get_test_data_path

from picard.plugin3.manifest import PluginManifest


class MockPluginManager(Mock):
    """Mock PluginManager with sensible defaults."""

    def __init__(self, **kwargs):
        # Set defaults
        defaults = {
            'plugins': [],
            '_failed_plugins': [],
            '_enabled_plugins': set(),
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

        # Add get_plugin_registry_id method that returns None by default
        self.get_plugin_registry_id = Mock(return_value=None)


class MockTagger(Mock):
    """Mock Tagger with sensible defaults."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add common attributes that tests expect
        if 'webservice' not in kwargs:
            self.webservice = Mock()
        if 'register_cleanup' not in kwargs:
            self.register_cleanup = Mock()


def load_plugin_manifest(plugin_name: str) -> PluginManifest:
    """Load a plugin manifest from test data."""
    manifest_path = get_test_data_path('testplugins3', plugin_name, 'MANIFEST.toml')
    with open(manifest_path, 'rb') as manifest_file:
        return PluginManifest(plugin_name, manifest_file)


def load_test_registry():
    """Load test registry data from test/data/testplugins3/registry.json."""
    registry_path = Path(get_test_data_path('testplugins3', 'registry.json'))
    with open(registry_path, 'r') as f:
        return json.load(f)


def get_test_registry_path():
    """Get path to test registry file."""
    return Path(get_test_data_path('testplugins3', 'registry.json'))


def create_test_registry():
    """Create PluginRegistry with test data loaded."""
    from picard.plugin3.registry import PluginRegistry

    registry = PluginRegistry()
    registry._registry_data = load_test_registry()
    return registry


def create_cli_output():
    """Create PluginOutput with StringIO streams."""
    from picard.plugin3.output import PluginOutput

    return PluginOutput(stdout=StringIO(), stderr=StringIO(), color=False)


class MockCliArgs(Mock):
    """Mock CLI args with sensible defaults."""

    def __init__(self, **kwargs):
        defaults = {
            'ref': None,
            'list': False,
            'info': None,
            'list_refs': None,
            'enable': None,
            'disable': None,
            'install': None,
            'uninstall': None,
            'update': None,
            'update_all': False,
            'check_updates': False,
            'browse': False,
            'search': None,
            'check_blacklist': None,
            'refresh_registry': False,
            'switch_ref': None,
            'clean_config': None,
            'validate': None,
            'manifest': None,
            'yes': False,
            'purge': False,
            'reinstall': False,
            'force_blacklisted': False,
            'category': None,
            'trust': None,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)


def run_cli(manager, **args_kwargs):
    """Run CLI with given args and return (exit_code, stdout, stderr)."""
    from picard.plugin3.cli import PluginCLI

    output = create_cli_output()
    args = MockCliArgs(**args_kwargs)
    cli = PluginCLI(manager, args, output)
    exit_code = cli.run()
    return exit_code, output.stdout.getvalue(), output.stderr.getvalue()


class MockPlugin(Mock):
    """Mock Plugin with sensible defaults."""

    def __init__(self, name='test-plugin', uuid='test-uuid-1234', **kwargs):
        from pathlib import Path

        from picard.plugin3.plugin import Plugin, PluginState

        # Extract our custom params before passing to Mock
        local_path = kwargs.pop('local_path', Path(f'/tmp/{name}'))
        version = kwargs.pop('version', '1.0.0')
        display_name = kwargs.pop('display_name', name)
        manifest = kwargs.pop('manifest', None)
        state = kwargs.pop('state', PluginState.LOADED)

        super().__init__(spec=Plugin, **kwargs)
        self.plugin_id = name
        self.local_path = local_path
        self.state = state

        # Use provided manifest or create default
        if manifest:
            self.manifest = manifest
        else:
            self.manifest = Mock()
            self.manifest.uuid = uuid
            self.manifest.version = version
            self.manifest.name = Mock(return_value=display_name)


def create_mock_manager_with_manifest_validation():
    """Create a mock PluginManager with real manifest validation methods.

    This is useful for tests that need to validate manifests but don't need
    a full PluginManager instance.
    """
    from picard.plugin3.manager import PluginManager

    manager = Mock(spec=PluginManager)
    manager._read_and_validate_manifest = PluginManager._read_and_validate_manifest.__get__(manager, PluginManager)
    manager._validate_manifest = PluginManager._validate_manifest.__get__(manager, PluginManager)
    return manager


def create_test_manifest_content(
    name='Test Plugin',
    version='1.0.0',
    description='Test description',
    authors=None,
    maintainers=None,
    uuid='550e8400-e29b-41d4-a716-446655440000',
    api_versions=None,
    license=None,
    license_url=None,
    **extra_fields,
):
    """Create a valid MANIFEST.toml content string.

    Args:
        name: Plugin name
        version: Plugin version
        description: Plugin description
        authors: List of authors (optional)
        maintainers: List of maintainers (optional)
        uuid: Plugin UUID
        api_versions: List of API versions (default: ['3.0'])
        license: License identifier (optional)
        license_url: License URL (optional)
        **extra_fields: Additional fields to include (e.g., homepage, categories)

    Returns:
        str: MANIFEST.toml content
    """
    if api_versions is None:
        api_versions = ['3.0']

    api_str = ', '.join(f'"{v}"' for v in api_versions)

    content = f'''uuid = "{uuid}"
name = "{name}"
version = "{version}"
description = "{description}"
api = [{api_str}]
'''

    # Add optional fields
    if authors:
        authors_str = ', '.join(f'"{a}"' for a in authors)
        content += f'authors = [{authors_str}]\n'

    if maintainers:
        maintainers_str = ', '.join(f'"{m}"' for m in maintainers)
        content += f'maintainers = [{maintainers_str}]\n'

    if license:
        content += f'license = "{license}"\n'

    if license_url:
        content += f'license_url = "{license_url}"\n'

    # Add extra fields
    for key, value in extra_fields.items():
        if isinstance(value, list):
            value_str = ', '.join(f'"{v}"' for v in value)
            content += f'{key} = [{value_str}]\n'
        elif isinstance(value, dict):
            content += f'\n[{key}]\n'
            for k, v in value.items():
                content += f'{k} = "{v}"\n'
        else:
            content += f'{key} = "{value}"\n'

    return content


def create_test_plugin_dir(base_dir, plugin_name='test-plugin', manifest_content=None, add_git=False):
    """Create a test plugin directory with MANIFEST.toml.

    Args:
        base_dir: Base directory (Path or str)
        plugin_name: Plugin directory name
        manifest_content: MANIFEST.toml content (default: valid manifest)
        add_git: If True, initialize as git repository

    Returns:
        Path: Path to the created plugin directory
    """
    from pathlib import Path

    plugin_dir = Path(base_dir) / plugin_name
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Create MANIFEST.toml
    if manifest_content is None:
        manifest_content = create_test_manifest_content(name=plugin_name.replace('-', ' ').title())

    (plugin_dir / 'MANIFEST.toml').write_text(manifest_content)

    # Create __init__.py
    (plugin_dir / '__init__.py').write_text('# Test plugin\n')

    # Initialize git if requested
    if add_git:
        try:
            import pygit2

            repo = pygit2.init_repository(str(plugin_dir))
            index = repo.index
            index.add_all()
            index.write()
            tree = index.write_tree()
            author = pygit2.Signature('Test', 'test@example.com')
            repo.create_commit('refs/heads/main', author, author, 'Initial commit', tree, [])
            repo.set_head('refs/heads/main')
        except ImportError:
            # pygit2 not available, skip git init
            pass

    return plugin_dir


def create_git_commit(repo_path, message='Initial commit', author_name='Test', author_email='test@example.com'):
    """Create a git commit with all current files.

    Args:
        repo_path: Path to git repository
        message: Commit message
        author_name: Author name
        author_email: Author email

    Returns:
        str: Commit ID (SHA)
    """
    try:
        import pygit2

        repo = pygit2.Repository(str(repo_path))
        index = repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        author = pygit2.Signature(author_name, author_email)
        commit_id = repo.create_commit('refs/heads/main', author, author, message, tree, [])
        repo.set_head('refs/heads/main')
        return str(commit_id)
    except ImportError:
        return None
