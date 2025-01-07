# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2021, 2023 Philipp Wolfer
# Copyright (C) 2019-2022, 2024 Laurent Monin
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
from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

import picard
from picard.const import USER_PLUGIN_DIR
from picard.plugin import (
    PluginFunctions,
    PluginWrapper,
    _unregister_module_extensions,
)
from picard.pluginmanager import (
    PluginManager,
    _compatible_api_versions,
    _plugin_dirs,
    _plugin_name_from_path,
    register_plugin_dir,
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
    if plugin_name in sys.modules:
        del sys.modules[plugin_name]


class TestPicardPluginsCommon(PicardTestCase):

    def setUp(self):
        super().setUp()
        logging.disable(logging.ERROR)


class TestPicardPluginsCommonTmpDir(TestPicardPluginsCommon):

    def setUp(self):
        super().setUp()
        self.tmp_directory = self.mktmpdir()
        register_plugin_dir(self.tmp_directory)


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
        plugin_path = _testplugins[name]
        pm = PluginManager(plugins_directory=self.tmp_directory)

        msg = "install_plugin: %s %r" % (name, plugin_path)
        pm.install_plugin(plugin_path)
        self.assertEqual(len(pm.plugins), 1, msg)
        self.assertEqual(pm.plugins[0].name, 'Dummy plugin', msg)

        # if module is properly loaded, this should work
        from picard.plugins.dummyplugin import DummyPlugin
        DummyPlugin()

        # Remove plugin again
        pm.remove_plugin('dummyplugin')
        unload_plugin('picard.plugins.dummyplugin')
        with self.assertRaises(ImportError):
            from picard.plugins.dummyplugin import (  # noqa: F811 # pylint: disable=reimported
                DummyPlugin,
            )

    def _test_plugin_install_data(self, name):
        # simulate installation from UI using data from picard plugins api web service
        with open(_testplugins[name], 'rb') as f:
            data = f.read()

        pm = PluginManager(plugins_directory=self.tmp_directory)

        msg = "install_plugin_data: %s data: %d bytes" % (name, len(data))
        pm.install_plugin(None, plugin_name='dummyplugin', plugin_data=data)
        self.assertEqual(len(pm.plugins), 1, msg)
        self.assertEqual(pm.plugins[0].name, 'Dummy plugin', msg)

        # if module is properly loaded, this should work
        from picard.plugins.dummyplugin import DummyPlugin
        DummyPlugin()

        # Remove plugin again
        pm.remove_plugin('dummyplugin')
        unload_plugin('picard.plugins.dummyplugin')
        with self.assertRaises(ImportError):
            from picard.plugins.dummyplugin import (  # noqa: F811 # pylint: disable=reimported
                DummyPlugin,
            )

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

    def setUp(self):
        super().setUp()
        self.pm = PluginManager(plugins_directory=self.tmp_directory)
        self.src_dir = None

    def tearDown(self):
        super().tearDown()
        unload_plugin('picard.plugins.dummyplugin')
        if self.src_dir:
            _plugin_dirs.remove(self.src_dir)

    def _register_plugin_dir(self, name):
        self.src_dir = os.path.dirname(_testplugins[name])
        register_plugin_dir(self.src_dir)

    def _test_plugin_load_from_directory(self, name):
        self._register_plugin_dir(name)
        msg = "plugins_load_from_directory: %s %r" % (name, self.src_dir)
        self.pm.load_plugins_from_directory(self.src_dir)
        self.assertEqual(len(self.pm.plugins), 1, msg)
        self.assertEqual(self.pm.plugins[0].name, 'Dummy plugin', msg)

        # if module is properly loaded, this should work
        from picard.plugins.dummyplugin import DummyPlugin
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

    def test_plugin_import_error(self):
        module_name = 'picard.plugins.dummyplugin'
        self.assertIsNone(sys.modules.get(module_name))
        self._register_plugin_dir('importerror')
        self.pm.load_plugins_from_directory(self.src_dir)
        self.assertIsNone(sys.modules.get(module_name))


class TestPluginWrapper(PicardTestCase):

    def test_is_user_installed(self):
        manifest = {
            'PLUGIN_NAME': 'foo'
        }
        user_plugin = PluginWrapper({}, USER_PLUGIN_DIR, manifest_data=manifest)
        self.assertTrue(user_plugin.is_user_installed)
        system_plugin = PluginWrapper({}, '/other/path/plugins', manifest_data=manifest)
        self.assertFalse(system_plugin.is_user_installed)


class TestPluginFunctions(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values({
            'enabled_plugins': [],
        })

    def test_register_order(self):
        pfs = PluginFunctions(label="test")
        self.assertEqual(pfs.functions, {})
        pfs.register('m', 'f1', priority=0)
        pfs.register('m', 'f2', priority=0)
        self.assertEqual(list(pfs._get_functions()), ['f1', 'f2'])
        pfs.register('m', 'f3', priority=1)
        pfs.register('m', 'f4', priority=-1)
        self.assertEqual(list(pfs._get_functions()), ['f3', 'f1', 'f2', 'f4'])

    def test_run_args(self):
        testfunc1 = Mock()
        testfunc2 = Mock()

        pfs = PluginFunctions(label="test")
        pfs.register('m', testfunc1)
        pfs.register('m', testfunc2)
        pfs.run(1, k=2)
        testfunc1.assert_called_with(1, k=2)
        testfunc2.assert_called_with(1, k=2)
