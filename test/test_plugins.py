# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2021 Laurent Monin
# Copyright (C) 2019-2021 Philipp Wolfer
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


import logging
import os
import sys
import unittest

from test.picardtestcase import PicardTestCase

import picard
from picard.const import USER_PLUGIN_DIR
from picard.plugin import (
    _PLUGIN_MODULE_PREFIX,
    PluginWrapper,
    _unregister_module_extensions,
)
from picard.pluginmanager import (
    PluginManager,
    _compatible_api_versions,
    _plugin_name_from_path,
)
from picard.version import (
    Version,
    VersionError,
)


# testplugins structure along plugins (zipped or not) structures
#
# ├── module/
# │   └── dummyplugin/
# │       └── __init__.py
# ├── packaged_module/
# │   └── dummyplugin.picard.zip
# │       └── dummyplugin/         # FIXME: correct structure??
# │           └── __init__.py
# │           └── MANIFEST.json    # FIXME: format??
# ├── singlefile/
# │   └── dummyplugin.py
# ├── zipped_module/
# │   └── dummyplugin.zip
# │       └── dummyplugin/
# │           └── __init__.py
# └── zipped_singlefile/
#     └── dummyplugin.zip
#         └── dummyplugin.py

# module
# packaged_module
# singlefile
# zipped_module
# zipped_singlefile


def _get_test_plugins():
    testplugins = {}
    testplugins_path = os.path.join('test', 'data', 'testplugins')
    for f in os.listdir(testplugins_path):
        testplugin = os.path.join(testplugins_path, f)
        for e in os.listdir(testplugin):
            if e == '__pycache__':
                continue
            testplugins[f] = os.path.join(testplugin, e)
    return testplugins


_testplugins = _get_test_plugins()


def unload_plugin(plugin_name):
    """for testing purposes"""
    _unregister_module_extensions(plugin_name)
    if hasattr(picard.plugins, plugin_name):
        delattr(picard.plugins, plugin_name)
    key = _PLUGIN_MODULE_PREFIX + plugin_name
    if key in sys.modules:
        del sys.modules[key]


class TestPicardPluginsCommon(PicardTestCase):

    def setUp(self):
        super().setUp()
        logging.disable(logging.ERROR)

    def tearDown(self):
        pass


class TestPicardPluginsCommonTmpDir(TestPicardPluginsCommon):

    def setUp(self):
        super().setUp()
        self.tmp_directory = self.mktmpdir()


class TestPicardPluginManager(TestPicardPluginsCommon):

    def test_compatible_api_version(self):

        # use first element from picard.api_versions, it should be compatible
        api_versions = picard.api_versions[:1]
        expected = {Version.from_string(v) for v in api_versions}
        result = _compatible_api_versions(api_versions)
        self.assertEqual(result, expected)

        # pretty sure 0.0 isn't compatible
        api_versions = ["0.0"]
        expected = set()
        result = _compatible_api_versions(api_versions)
        self.assertEqual(result, expected)

        # buggy version
        api_versions = ["0.a"]
        with self.assertRaises(VersionError):
            result = _compatible_api_versions(api_versions)

    def test_plugin_name_from_path(self):
        for name, path in _testplugins.items():
            self.assertEqual(
                _plugin_name_from_path(path), 'dummyplugin',
                "failed to get plugin name from %s: %r" % (name, path)
            )


class TestPicardPluginsInstall(TestPicardPluginsCommonTmpDir):

    def _test_plugin_install(self, name):
        unload_plugin('dummyplugin')
        with self.assertRaises(ImportError):
            from picard.plugins.dummyplugin import DummyPlugin

        plugin_path = _testplugins[name]
        pm = PluginManager(plugins_directory=self.tmp_directory)

        msg = "install_plugin: %s %r" % (name, plugin_path)
        pm.install_plugin(plugin_path)
        self.assertEqual(len(pm.plugins), 1, msg)
        self.assertEqual(pm.plugins[0].name, 'Dummy plugin', msg)

        # if module is properly loaded, this should work
        from picard.plugins.dummyplugin import DummyPlugin  # noqa: F811
        DummyPlugin()

    def _test_plugin_install_data(self, name):
        unload_plugin('dummyplugin')
        with self.assertRaises(ImportError):
            from picard.plugins.dummyplugin import DummyPlugin

        # simulate installation from UI using data from picard plugins api web service
        with open(_testplugins[name], 'rb') as f:
            data = f.read()

        pm = PluginManager(plugins_directory=self.tmp_directory)

        msg = "install_plugin_data: %s data: %d bytes" % (name, len(data))
        pm.install_plugin(None, plugin_name='dummyplugin', plugin_data=data)
        self.assertEqual(len(pm.plugins), 1, msg)
        self.assertEqual(pm.plugins[0].name, 'Dummy plugin', msg)

        # if module is properly loaded, this should work
        from picard.plugins.dummyplugin import DummyPlugin  # noqa: F811
        DummyPlugin()

    # module
    def test_plugin_install_module(self):
        self._test_plugin_install('module')

    # packaged_module
    # FIXME : not really implemented
    @unittest.skipIf(True, "FIXME")
    def test_plugin_install_packaged_module(self):
        self._test_plugin_install('packaged_module')

    # singlefile
    def test_plugin_install_packaged_singlefile(self):
        self._test_plugin_install('singlefile')

    # zipped_module
    def test_plugin_install_packaged_zipped_module(self):
        self._test_plugin_install('zipped_module')

    # zipped_singlefile
    def test_plugin_install_packaged_zipped_singlefile(self):
        self._test_plugin_install('zipped_singlefile')

    # zipped_module from picard plugins ws
    def test_plugin_install_zipped_module_data(self):
        self._test_plugin_install_data('zipped_module')

    # zipped_singlefile from picard plugins ws
    def test_plugin_install_zipped_singlefile_data(self):
        self._test_plugin_install_data('zipped_singlefile')

    def test_plugin_install_no_path_no_plugin_name(self):
        pm = PluginManager(plugins_directory=self.tmp_directory)
        with self.assertRaises(AssertionError):
            pm.install_plugin(None)


class TestPicardPluginsLoad(TestPicardPluginsCommonTmpDir):

    def _test_plugin_load_from_directory(self, name):
        unload_plugin('dummyplugin')
        with self.assertRaises(ImportError):
            from picard.plugins.dummyplugin import DummyPlugin

        pm = PluginManager(plugins_directory=self.tmp_directory)

        src_dir = os.path.dirname(_testplugins[name])

        msg = "plugins_load_from_directory: %s %r" % (name, src_dir)
        pm.load_plugins_from_directory(src_dir)
        self.assertEqual(len(pm.plugins), 1, msg)
        self.assertEqual(pm.plugins[0].name, 'Dummy plugin', msg)

        # if module is properly loaded, this should work
        from picard.plugins.dummyplugin import DummyPlugin  # noqa: F811
        DummyPlugin()

    # singlefile
    def test_plugin_load_from_directory_singlefile(self):
        self._test_plugin_load_from_directory('singlefile')

    # zipped_module
    def test_plugin_load_from_directory_zipped_module(self):
        self._test_plugin_load_from_directory('zipped_module')

    # zipped_singlefile
    def test_plugin_load_from_directory_zipped_singlefile(self):
        self._test_plugin_load_from_directory('zipped_singlefile')

    # module
    def test_plugin_load_from_directory_module(self):
        self._test_plugin_load_from_directory('module')


class TestPluginWrapper(PicardTestCase):

    def test_is_user_installed(self):
        manifest = {
            'PLUGIN_NAME': 'foo'
        }
        user_plugin = PluginWrapper({}, USER_PLUGIN_DIR, manifest_data=manifest)
        self.assertTrue(user_plugin.is_user_installed)
        system_plugin = PluginWrapper({}, '/other/path/plugins', manifest_data=manifest)
        self.assertFalse(system_plugin.is_user_installed)
