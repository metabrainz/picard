# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
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
from json import JSONDecodeError

from test.picardtestcase import PicardTestCase

from picard.script import (
    FileNamingScript,
    PicardScript,
)


class _DateTime(datetime.datetime):
    @classmethod
    def utcnow(cls):
        return cls(year=2020, month=1, day=2, hour=12, minute=34, second=56, microsecond=789, tzinfo=None)


class ScriptClassesTest(PicardTestCase):

    original_datetime = datetime.datetime

    def setUp(self):
        super().setUp()
        # Save original datetime object and substitute one returning
        # a fixed utcnow() value for testing.
        datetime.datetime = _DateTime

    def tearDown(self):
        # Restore original datetime object
        datetime.datetime = self.original_datetime

    def test_script_object_1(self):
        # Check initial loaded values.
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        self.assertEqual(test_script.id, '12345')
        self.assertEqual(test_script.get_value('id'), '12345')
        self.assertEqual(test_script.last_updated, '2021-04-26')
        self.assertEqual(test_script.get_value('last_updated'), '2021-04-26')
        self.assertEqual(test_script.to_json(), '{"script": "Script text", "title": "Script 1"}')

    def test_script_object_2(self):
        # Check updating values directly so as not to modify `last_updated`.
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        test_script.id = '54321'
        self.assertEqual(test_script.id, '54321')
        self.assertEqual(test_script.get_value('id'), '54321')
        self.assertEqual(test_script.last_updated, '2021-04-26')
        self.assertEqual(test_script.get_value('last_updated'), '2021-04-26')

        test_script.title = 'Updated Script 1'
        self.assertEqual(test_script.title, 'Updated Script 1')
        self.assertEqual(test_script.title, 'Updated Script 1')
        self.assertEqual(test_script.get_value('title'), 'Updated Script 1')
        self.assertEqual(test_script.get_value('last_updated'), '2021-04-26')

    def test_script_object_3(self):
        # Check updating values that are ignored from modifying `last_updated`.
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        test_script.update_script_setting(id='54321')
        self.assertEqual(test_script.id, '54321')
        self.assertEqual(test_script.get_value('id'), '54321')
        self.assertEqual(test_script.last_updated, '2021-04-26')
        self.assertEqual(test_script.get_value('last_updated'), '2021-04-26')

    def test_script_object_4(self):
        # Check updating values that modify `last_updated`.
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        test_script.update_script_setting(title='Updated Script 1')
        self.assertEqual(test_script.title, 'Updated Script 1')
        self.assertEqual(test_script.get_value('title'), 'Updated Script 1')
        self.assertEqual(test_script.last_updated, '2020-01-02 12:34:56 UTC')
        self.assertEqual(test_script.get_value('last_updated'), '2020-01-02 12:34:56 UTC')

    def test_script_object_5(self):
        # Check updating values from JSON that modify `last_updated`.
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        test_script.update_from_json('{"script": "Updated script"}')
        self.assertEqual(test_script.script, 'Updated script')
        self.assertEqual(test_script.get_value('script'), 'Updated script')
        self.assertEqual(test_script.last_updated, '2020-01-02 12:34:56 UTC')
        self.assertEqual(test_script.get_value('last_updated'), '2020-01-02 12:34:56 UTC')

    def test_script_object_6(self):
        # Test that extra (unknown) settings are ignored during updating
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        test_script.update_script_setting(description='Updated description')
        self.assertEqual(test_script.get_value('last_updated'), '2021-04-26')
        self.assertEqual(test_script.to_json(), '{"script": "Script text", "title": "Script 1"}')
        with self.assertRaises(AttributeError):
            print(test_script.description)

    def test_script_object_7(self):
        # Test that extra (unknown) settings are ignored during updating from JSON string
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        test_script.update_from_json('{"description": "Updated description"}')
        self.assertEqual(test_script.get_value('last_updated'), '2021-04-26')
        self.assertEqual(test_script.to_json(), '{"script": "Script text", "title": "Script 1"}')
        with self.assertRaises(AttributeError):
            print(test_script.description)

    def test_script_object_8(self):
        # Test that requested unknown settings return None
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        self.assertEqual(test_script.get_value('unknown_setting'), None)

    def test_script_object_9(self):
        # Test that an exception is raised when creating or updating using an invalid JSON string
        with self.assertRaises(JSONDecodeError):
            test_script = PicardScript().create_from_json('Not a JSON string')
        test_script = PicardScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26')
        with self.assertRaises(JSONDecodeError):
            test_script.update_from_json('Not a JSON string')

    def test_naming_script_object_1(self):
        # Check initial loaded values.
        test_script = FileNamingScript(title='Script 1', script='Script text', id='12345', last_updated='2021-04-26', description='Script description', author='Script author')
        self.assertEqual(test_script.id, '12345')
        self.assertEqual(test_script.get_value('id'), '12345')
        self.assertEqual(test_script.last_updated, '2021-04-26')
        self.assertEqual(test_script.get_value('last_updated'), '2021-04-26')
        self.assertEqual(test_script.script, 'Script text')
        self.assertEqual(test_script.get_value('script'), 'Script text')
        self.assertEqual(test_script.author, 'Script author')
        self.assertEqual(test_script.get_value('author'), 'Script author')
        self.assertEqual(test_script.to_json(),
                         '{'
                         '"author": "Script author", '
                         '"description": "Script description", '
                         '"last_updated": "2021-04-26", '
                         '"license": "", '
                         '"script": "Script text", '
                         '"title": "Script 1", '
                         '"version": ""'
                         '}'
                         )
        self.assertEqual(test_script.to_json(indent=4),
                         '{\n'
                         '    "author": "Script author",\n'
                         '    "description": "Script description",\n'
                         '    "last_updated": "2021-04-26",\n'
                         '    "license": "",\n'
                         '    "script": "Script text",\n'
                         '    "title": "Script 1",\n'
                         '    "version": ""\n'
                         '}'
                         )
