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
from test.picardtestcase import PicardTestCase

import picard
from picard import (
    VersionError,
    version_from_string,
)
from picard.plugin import PluginManager


class TestPicardPluginsCommon(PicardTestCase):

    def setUp(self):
        super().setUp()
        logging.disable(logging.ERROR)

    def tearDown(self):
        pass


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
