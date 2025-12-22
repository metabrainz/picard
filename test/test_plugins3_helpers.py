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
from pathlib import Path
from unittest.mock import Mock
import uuid

from test.picardtestcase import get_test_data_path

from picard.plugin3.manifest import PluginManifest
from picard.plugin3.plugin import Plugin


def generate_unique_uuid():
    """Generate a unique UUID for test isolation."""
    return str(uuid.uuid4())


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

        # Add mock for _fetch_version_tags that returns empty list by default
        self._fetch_version_tags = Mock(return_value=[])

        # Add get_plugin_registry_id method that returns None by default
        self.get_plugin_registry_id = Mock(return_value=None)

        # Add select_ref_for_plugin method that delegates to the real implementation
        def select_ref_for_plugin_impl(plugin):
            from unittest.mock import Mock

            from picard.plugin3.manager import PluginManager

            temp_manager = PluginManager(Mock())
            temp_manager._registry_manager._fetch_version_tags = self._fetch_version_tags
            return temp_manager.select_ref_for_plugin(plugin)

        self.select_ref_for_plugin = select_ref_for_plugin_impl

        # Add get_registry_plugin_latest_version method that delegates to the real implementation
        def get_registry_plugin_latest_version_impl(plugin_data):
            from unittest.mock import Mock

            from picard.plugin3.manager import PluginManager

            temp_manager = PluginManager(Mock())
            temp_manager._fetch_version_tags = self._fetch_version_tags
            return PluginManager.get_registry_plugin_latest_version(temp_manager, plugin_data)

        self.get_registry_plugin_latest_version = get_registry_plugin_latest_version_impl

        # Add get_preferred_version method that delegates to the real implementation
        def get_preferred_version_impl(plugin_uuid, manifest_version=''):
            from picard.plugin3.manager import PluginManager

            temp_manager = PluginManager.__new__(PluginManager)
            temp_manager._get_plugin_metadata = self._get_plugin_metadata
            return PluginManager.get_preferred_version(temp_manager, plugin_uuid, manifest_version)

        self.get_preferred_version = get_preferred_version_impl

        # Add search_registry_plugins method that delegates to the real implementation
        def search_registry_plugins_impl(query=None, category=None, trust_level=None):
            from unittest.mock import Mock

            from picard.plugin3.manager import PluginManager

            temp_manager = PluginManager(Mock())
            temp_manager._registry = self._registry
            return temp_manager.search_registry_plugins(query, category, trust_level)

        self.search_registry_plugins = search_registry_plugins_impl

        # Add find_similar_plugin_ids method that delegates to the real implementation
        def find_similar_plugin_ids_impl(query, max_results=10):
            from unittest.mock import Mock

            from picard.plugin3.manager import PluginManager

            temp_manager = PluginManager(Mock())
            temp_manager._registry = self._registry
            return temp_manager.find_similar_plugin_ids(query, max_results)

        self.find_similar_plugin_ids = find_similar_plugin_ids_impl


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
    """Load test registry data from test/data/testplugins3/registry.toml."""
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    registry_path = Path(get_test_data_path('testplugins3', 'registry.toml'))
    with open(registry_path, 'rb') as f:
        return tomllib.load(f)


def get_test_registry_path():
    """Get path to test registry file."""
    return Path(get_test_data_path('testplugins3', 'registry.toml'))


def create_test_registry():
    """Create PluginRegistry with test data loaded."""
    from picard.plugin3.registry import PluginRegistry

    registry = PluginRegistry()
    registry.set_raw_registry_data(load_test_registry())
    registry._process_plugins()  # Process plugins into RegistryPlugin objects
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
            'remove': None,
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
            'locale': 'en',
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


class MockPlugin(Plugin):
    """Mock Plugin with sensible defaults."""

    def __init__(self, name='test-plugin', uuid=None, **kwargs):
        from pathlib import Path

        from picard.plugin3.plugin import PluginState

        # Extract our custom params before passing to Mock
        local_path = kwargs.pop('local_path', Path(f'/tmp/{name}'))
        version = kwargs.pop('version', '1.0.0')
        display_name = kwargs.pop('display_name', name)
        manifest = kwargs.pop('manifest', None)
        state = kwargs.pop('state', PluginState.LOADED)

        # Generate unique UUID if not provided
        if uuid is None:
            uuid = generate_unique_uuid()

        super().__init__(local_path, name)
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

        # Set uuid shortcut property
        self.uuid = uuid

        # Mock all methods
        self.load_module = Mock()
        self.enable = Mock()
        self.disable = Mock()


def create_mock_manager_with_manifest_validation():
    """Create a mock PluginManager with real manifest validation methods.

    This is useful for tests that need to validate manifests but don't need
    a full PluginManager instance.
    """
    from picard.plugin3.manager import PluginManager
    from picard.plugin3.validation import PluginValidation

    manager = Mock(spec=PluginManager)
    manager._read_and_validate_manifest = PluginValidation.read_and_validate_manifest
    manager._validate_manifest = PluginValidation.validate_manifest
    return manager


def skip_if_no_git_backend():
    """Skip test if git backend is not available."""
    try:
        from picard.git.factory import has_git_backend

        if not has_git_backend():
            import pytest

            pytest.skip("git backend not available")
    except ImportError:
        import pytest

        pytest.skip("git backend not available")


def create_git_repo_with_backend(repo_path, initial_files=None):
    """Create a git repository using the git backend abstraction.

    Args:
        repo_path: Path to create repository
        initial_files: Dict of {filename: content} to create and commit

    Returns:
        str: Initial commit ID
    """
    from pathlib import Path

    from picard.git.factory import git_backend

    repo_path = Path(repo_path)
    repo_path.mkdir(parents=True, exist_ok=True)

    backend = git_backend()
    repo = backend.init_repository(repo_path)

    if initial_files:
        # Create files
        for filename, content in initial_files.items():
            (repo_path / filename).write_text(content)

        # Commit using backend
        commit_id = backend.create_commit(repo, 'Initial commit')
        repo.free()
        return commit_id

    repo.free()
    return None


def get_backend_repo(repo_path):
    """Get a backend repository instance for a path."""
    from picard.git.factory import git_backend

    return git_backend().create_repository(repo_path)


def backend_create_tag(repo_path, tag_name, commit_id=None, message=""):
    """Create a tag using the git backend."""
    from picard.git.factory import git_backend

    backend = git_backend()
    repo = backend.create_repository(repo_path)
    if commit_id is None:
        commit_id = repo.get_head_target()
    backend.create_tag(repo, tag_name, commit_id, message)
    repo.free()


def backend_create_lightweight_tag(repo_path, tag_name, commit_id=None):
    """Create a lightweight tag (reference only) using backend."""
    from picard.git.factory import git_backend

    backend = git_backend()
    repo = backend.create_repository(repo_path)
    if commit_id is None:
        commit_id = repo.get_head_target()
    backend.create_reference(repo, f'refs/tags/{tag_name}', commit_id)
    repo.free()


def backend_set_detached_head(repo_path, commit_id):
    """Set repository to detached HEAD state using backend."""
    from picard.git.factory import git_backend

    backend = git_backend()
    repo = backend.create_repository(repo_path)
    backend.set_head_detached(repo, commit_id)
    repo.free()


def backend_create_branch(repo_path, branch_name, commit_id=None):
    """Create a branch using the git backend."""
    from picard.git.factory import git_backend

    backend = git_backend()
    repo = backend.create_repository(repo_path)
    if commit_id is None:
        commit_id = repo.get_head_target()
    backend.create_branch(repo, branch_name, commit_id)
    repo.free()


def backend_add_and_commit(repo_path, message="Commit", author_name="Test", author_email="test@example.com"):
    """Add all files and commit using backend."""
    from picard.git.factory import git_backend

    backend = git_backend()
    repo = backend.create_repository(repo_path)
    commit_id = backend.add_and_commit_files(repo, message, author_name, author_email)
    repo.free()
    return commit_id


def backend_init_and_commit(repo_path, files=None, message="Initial commit"):
    """Initialize repo and create initial commit using backend."""
    from pathlib import Path

    from picard.git.factory import git_backend

    repo_path = Path(repo_path)
    repo_path.mkdir(parents=True, exist_ok=True)

    # Create files first
    if files:
        for filename, content in files.items():
            (repo_path / filename).write_text(content)

    backend = git_backend()
    repo = backend.init_repository(repo_path)
    commit_id = backend.add_and_commit_files(repo, message)
    repo.free()
    return commit_id


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
            from picard.git.factory import has_git_backend

            if has_git_backend():
                create_git_repo_with_backend(
                    plugin_dir, {'MANIFEST.toml': manifest_content, '__init__.py': '# Test plugin\n'}
                )
        except (ImportError, Exception):
            # Git backend not available, skip git init
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
        from picard.git.factory import git_backend, has_git_backend

        if not has_git_backend():
            return None

        backend = git_backend()
        repo = backend.create_repository(repo_path)
        commit_id = backend.create_commit(repo, message, author_name, author_email)
        repo.free()
        return commit_id
    except (ImportError, Exception):
        return None
