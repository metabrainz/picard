# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Laurent Monin
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
import shutil
from tempfile import mkdtemp
import unittest

from test.picardtestcase import PicardTestCase

import picard
from picard import (
    VersionError,
    version_from_string,
)
from picard.plugin import (
    PluginManager,
    _plugin_name_from_path,
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
            testplugins[f] = os.path.join(testplugin, e)
    return testplugins


_testplugins = _get_test_plugins()


class TestPicardPluginsCommon(PicardTestCase):

    def setUp(self):
        super().setUp()
        logging.disable(logging.ERROR)

    def tearDown(self):
        pass


class TestPicardPluginsCommonTmpDir(TestPicardPluginsCommon):

    def setUp(self):
        super().setUp()
        self.tmp_directory = mkdtemp()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.tmp_directory)


class TestPicardPluginManager(TestPicardPluginsCommon):

    def test_compatible_api_version(self):

        pm = PluginManager()

        # use first element from picard.api_versions, it should be compatible
        api_versions = picard.api_versions[:1]
        expected = set([version_from_string(v) for v in api_versions])
        result = pm._compatible_api_versions(api_versions)
        self.assertEqual(result, expected)

        # pretty sure 0.0 isn't compatible
        api_versions = ["0.0"]
        expected = set()
        result = pm._compatible_api_versions(api_versions)
        self.assertEqual(result, expected)

        # buggy version
        api_versions = ["0.a"]
        with self.assertRaises(VersionError):
            result = pm._compatible_api_versions(api_versions)

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

    # module
    def test_plugin_install_module(self):
        self._test_plugin_install('module')

    # packaged_module
    # FIXME
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
