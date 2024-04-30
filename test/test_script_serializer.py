# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021, 2024 Philipp Wolfer
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


import datetime
from unittest.mock import patch

import yaml

from test.picardtestcase import PicardTestCase

from picard.script.serializer import (
    FileNamingScript,
    PicardScript,
    ScriptImportError,
)


class MockDateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        if tz == datetime.timezone.utc:
            return cls(year=2020, month=1, day=2, hour=12, minute=34, second=56, microsecond=789, tzinfo=None)
        else:
            raise Exception("Unexpected parameter tz=%r" % tz)


class PicardScriptTest(PicardTestCase):

    def assertYamlEquals(self, yaml_str, obj, msg=None):
        self.assertEqual(obj, yaml.safe_load(yaml_str), msg)

    def test_script_object_1(self):
        # Check initial loaded values.
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26', script_language_version='1.0')
        self.assertEqual(test_script.id, '12345')
        self.assertEqual(test_script['id'], '12345')
        self.assertEqual(test_script.last_updated, '2021-04-26')
        self.assertEqual(test_script['last_updated'], '2021-04-26')
        self.assertYamlEquals(test_script.to_yaml(), {"id": "12345", "script": "Script text\n", "script_language_version": "1.0", "title": "Script 1"})

    def test_script_object_2(self):
        # Check updating values directly so as not to modify `last_updated`.
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        test_script.id = '54321'
        self.assertEqual(test_script.id, '54321')
        self.assertEqual(test_script['id'], '54321')
        self.assertEqual(test_script.last_updated, '2021-04-26')
        self.assertEqual(test_script['last_updated'], '2021-04-26')

        test_script.title = 'Updated Script 1'
        self.assertEqual(test_script.title, 'Updated Script 1')
        self.assertEqual(test_script['title'], 'Updated Script 1')
        self.assertEqual(test_script['last_updated'], '2021-04-26')

    def test_script_object_3(self):
        # Check updating values that are ignored from modifying `last_updated`.
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        test_script.update_script_setting(id='54321')
        self.assertEqual(test_script.id, '54321')
        self.assertEqual(test_script['id'], '54321')
        self.assertEqual(test_script.last_updated, '2021-04-26')
        self.assertEqual(test_script['last_updated'], '2021-04-26')

    @patch('datetime.datetime', MockDateTime)
    def test_script_object_4(self):
        # Check updating values that modify `last_updated`.
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        test_script.update_script_setting(title='Updated Script 1')
        self.assertEqual(test_script.title, 'Updated Script 1')
        self.assertEqual(test_script['title'], 'Updated Script 1')
        self.assertEqual(test_script.last_updated, '2020-01-02 12:34:56 UTC')
        self.assertEqual(test_script['last_updated'], '2020-01-02 12:34:56 UTC')

    @patch('datetime.datetime', MockDateTime)
    def test_script_object_5(self):
        # Check updating values from dict that modify `last_updated`.
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        test_script.update_from_dict({"script": "Updated script"})
        self.assertEqual(test_script.script, 'Updated script')
        self.assertEqual(test_script['script'], 'Updated script')
        self.assertEqual(test_script.last_updated, '2020-01-02 12:34:56 UTC')
        self.assertEqual(test_script['last_updated'], '2020-01-02 12:34:56 UTC')

    def test_script_object_6(self):
        # Test that extra (unknown) settings are ignored during updating
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26', script_language_version='1.0')
        test_script.update_script_setting(description='Updated description')
        self.assertEqual(test_script['last_updated'], '2021-04-26')
        self.assertYamlEquals(test_script.to_yaml(), {"id": "12345", "script": "Script text\n", "script_language_version": "1.0", "title": "Script 1"})
        with self.assertRaises(AttributeError):
            print(test_script.description)

    def test_script_object_7(self):
        # Test that extra (unknown) settings are ignored during updating from dict
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26', script_language_version='1.0')
        test_script.update_from_dict({"description": "Updated description"})
        self.assertEqual(test_script['last_updated'], '2021-04-26')
        self.assertYamlEquals(test_script.to_yaml(), {"id": "12345", "script": "Script text\n", "script_language_version": "1.0", "title": "Script 1"})
        with self.assertRaises(AttributeError):
            print(test_script.description)

    def test_script_object_8(self):
        # Test that requested unknown settings return None
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        self.assertEqual(test_script['unknown_setting'], None)

    def test_script_object_9(self):
        # Test that an exception is raised when creating or updating using an invalid YAML string
        with self.assertRaises(ScriptImportError):
            PicardScript().create_from_yaml('Not a YAML string')
        PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26', script_language_version='1.0')

    def test_naming_script_object_1(self):
        # Check initial loaded values.
        test_script = FileNamingScript(
            title='Script 1', script='Script text', id='12345', last_updated='2021-04-26',
            description='Script description', author='Script author', script_language_version='1.0'
        )
        self.assertEqual(test_script.id, '12345')
        self.assertEqual(test_script['id'], '12345')
        self.assertEqual(test_script.last_updated, '2021-04-26')
        self.assertEqual(test_script['last_updated'], '2021-04-26')
        self.assertEqual(test_script.script, 'Script text')
        self.assertEqual(test_script['script'], 'Script text')
        self.assertEqual(test_script.author, 'Script author')
        self.assertEqual(test_script['author'], 'Script author')
        self.assertEqual(
            test_script.to_yaml(),
            "title: Script 1\n"
            "description: |\n"
            "  Script description\n"
            "author: Script author\n"
            "license: ''\n"
            "version: ''\n"
            "last_updated: '2021-04-26'\n"
            "script_language_version: '1.0'\n"
            "script: |\n"
            "  Script text\n"
            "id: '12345'\n"
        )
