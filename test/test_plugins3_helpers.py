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


def create_cli_args(**kwargs):
    """Create mock CLI args with defaults."""
    defaults = {
        'ref': None,
        'list': False,
        'info': None,
        'status': None,
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
        'switch_ref': None,
        'clean_config': None,
        'validate': None,
        'yes': False,
        'purge': False,
        'reinstall': False,
        'force_blacklisted': False,
        'category': None,
        'trust': None,
    }
    defaults.update(kwargs)
    return Mock(**defaults)


def run_cli(manager, **args_kwargs):
    """Run CLI with given args and return (exit_code, stdout, stderr)."""
    from picard.plugin3.cli import PluginCLI

    output = create_cli_output()
    args = create_cli_args(**args_kwargs)
    cli = PluginCLI(manager, args, output)
    exit_code = cli.run()
    return exit_code, output.stdout.getvalue(), output.stderr.getvalue()


def create_mock_plugin(name='test-plugin', uuid='test-uuid-1234', **kwargs):
    """Create a mock plugin with common attributes."""
    from pathlib import Path

    from picard.plugin3.plugin import Plugin

    mock_plugin = Mock(spec=Plugin)
    mock_plugin.plugin_id = name
    mock_plugin.local_path = kwargs.get('local_path', Path(f'/tmp/{name}'))
    mock_plugin.manifest = Mock()
    mock_plugin.manifest.uuid = uuid
    mock_plugin.manifest.version = kwargs.get('version', '1.0.0')
    mock_plugin.manifest.name = Mock(return_value=kwargs.get('display_name', name))

    for key, value in kwargs.items():
        if key not in ('local_path', 'version', 'display_name'):
            setattr(mock_plugin, key, value)

    return mock_plugin
