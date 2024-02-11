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

from unittest.mock import Mock

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard.config import (
    ConfigSection,
    get_config,
)
from picard.plugin3.api import PluginApi
from picard.plugin3.manifest import PluginManifest
from picard.version import Version


def load_plugin_manifest(plugin_name: str) -> PluginManifest:
    manifest_path = get_test_data_path('testplugins3', plugin_name, 'MANIFEST.toml')
    with open(manifest_path, 'rb') as manifest_file:
        return PluginManifest(plugin_name, manifest_file)


class TestPluginManifest(PicardTestCase):

    def test_load_from_toml(self):
        manifest = load_plugin_manifest('example')
        self.assertEqual(manifest.module_name, 'example')
        self.assertEqual(manifest.name, 'Example plugin')
        self.assertEqual(manifest.author, 'Philipp Wolfer')
        self.assertEqual(
            manifest.description.replace('\r\n', '\n'),
            "This is an example plugin showcasing the new **Picard 3 plugin** API.\n\nYou can use [Markdown](https://daringfireball.net/projects/markdown/) for formatting.")
        self.assertEqual(manifest.version, Version(1, 0, 0))
        self.assertEqual(manifest.api_versions, (Version(3, 0, 0), Version(3, 1, 0)))
        self.assertEqual(manifest.license, 'CC0-1.0')
        self.assertEqual(manifest.license_url, 'https://creativecommons.org/publicdomain/zero/1.0/')
        self.assertEqual(manifest.user_guide_url, 'https://example.com/')


class TestPluginApi(PicardTestCase):

    def test_init(self):
        manifest = load_plugin_manifest('example')

        mock_tagger = Mock()
        mock_ws = mock_tagger.webservice = Mock()

        api = PluginApi(manifest, mock_tagger)
        self.assertEqual(api.web_service, mock_ws)
        self.assertEqual(api.logger.name, 'plugin.example')
        self.assertEqual(api.global_config, get_config())
        self.assertIsInstance(api.plugin_config, ConfigSection)
