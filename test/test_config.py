# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022, 2024 Laurent Monin
# Copyright (C) 2019-2022, 2024 Philipp Wolfer
# Copyright (C) 2024-2025 Bob Swift
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


from enum import (
    Enum,
    IntEnum,
)
import logging
import os
import shutil

from test.picardtestcase import PicardTestCase

from picard import config
from picard.config import (
    BoolOption,
    Config,
    FloatOption,
    IntOption,
    ListOption,
    Option,
    OptionError,
    TextOption,
    get_quick_menu_items,
    register_quick_menu_item,
)


class TestPicardConfigCommon(PicardTestCase):
    def setUp(self):
        super().setUp()

        self.tmp_directory = self.mktmpdir()

        self.configpath = os.path.join(self.tmp_directory, 'test.ini')
        shutil.copy(os.path.join('test', 'data', 'test.ini'), self.configpath)
        self.addCleanup(os.remove, self.configpath)

        self.config = Config.from_file(None, self.configpath)
        self.addCleanup(self.cleanup_config_obj)

        self.config.application["version"] = "testing"
        self.original_logging_disable = logging.root.manager.disable
        logging.disable(logging.ERROR)
        self.old_registry = dict(Option.registry)
        Option.registry = {}

    def tearDown(self):
        Option.registry = self.old_registry
        logging.disable(self.original_logging_disable)

    def cleanup_config_obj(self):
        # Ensure QSettings do not recreate the file on exit
        self.config.sync()
        del self.config
        self.config = None


class TestPicardConfig(TestPicardConfigCommon):
    def test_remove(self):
        TextOption("setting", "text_option", "abc")

        self.config.setting["text_option"] = "def"
        self.assertEqual(self.config.setting["text_option"], "def")

        self.config.setting.remove("text_option")
        self.assertEqual(self.config.setting["text_option"], "abc")


class TestPicardConfigOption(TestPicardConfigCommon):
    def test_basic_option(self):
        Option("setting", "option", "abc")
        self.assertEqual(self.config.setting["option"], "abc")
        self.config.setting["option"] = "def"
        self.assertEqual(self.config.setting["option"], "def")

    def test_option_get(self):
        Option("setting", "option", "abc")
        opt = Option.get("setting", "option")
        self.assertIsInstance(opt, Option)
        self.assertEqual(opt.default, "abc")
        self.assertIsNone(Option.get("setting", "not_existing_option"))

    def test_option_without_title(self):
        Option("setting", "option", "abc")
        opt = Option.get("setting", "option")
        self.assertIsNone(opt.title)

    def test_option_with_title(self):
        Option("setting", "option", "abc", title="Title")
        opt = Option.get("setting", "option")
        self.assertEqual(opt.title, "Title")

    def test_option_exists(self):
        Option("setting", "option", "abc")
        self.assertTrue(Option.exists("setting", "option"))
        self.assertFalse(Option.exists("setting", "not_option"))

    def test_option_add_if_missing(self):
        Option("setting", "option", "abc")
        Option.add_if_missing("setting", "option", "def")
        self.assertEqual(self.config.setting["option"], "abc")

        Option.add_if_missing("setting", "missing_option", "def", title="TITLE")
        self.assertEqual(self.config.setting["missing_option"], "def")
        self.assertEqual(Option.get_title('setting', 'missing_option'), 'TITLE')

    def test_get_default(self):
        Option("setting", "option", "abc")
        self.assertEqual(Option.get_default("setting", "option"), "abc")
        with self.assertRaisesRegex(OptionError, "^Option setting/unknown_option: No such option"):
            Option.get_default("setting", "unknown_option")

    def test_get_title(self):
        Option("setting", "option", "abc", title="Title")
        self.assertEqual(Option.get_title("setting", "option"), "Title")
        with self.assertRaisesRegex(OptionError, "^Option setting/unknown_option: No such option"):
            Option.get_title("setting", "unknown_option")


class TestPicardConfigSection(TestPicardConfigCommon):
    def test_as_dict(self):
        TextOption("setting", "text_option", "abc")
        BoolOption("setting", "bool_option", True)
        IntOption("setting", "int_option", 42)

        self.config.setting["int_option"] = 123

        expected = {
            "text_option": "abc",
            "bool_option": True,
            "int_option": 123,
        }

        self.assertEqual(expected, self.config.setting.as_dict())

    def test_register_option(self):
        class TestEnum(Enum):
            A = "a"
            B = "b"

        class TestIntEnum(IntEnum):
            A = 1
            B = 2

        test_cases = [
            ("text_option", "the default", TextOption, "s"),
            ("bool_option", True, BoolOption, False),
            ("int_option", 42, IntOption, 1),
            ("float_option", 4.2, FloatOption, 1.0),
            ("list_option", [1, 2], ListOption, ["a"]),
            ("list_option_from_tuple", (1, 2), ListOption, ["a"]),
            ("enum_option", TestEnum.A, Option, TestEnum.B),
            ("int_enum_option", TestIntEnum.A, Option, TestIntEnum.B),
            ("other_option", b"foo", Option, b"bar"),
        ]
        for name, default, expected_type, test_value in test_cases:
            opt = self.config.setting.register_option(name, default)
            self.assertEqual(Option.registry[('setting', name)], opt)
            self.assertIsInstance(opt, expected_type)
            self.assertEqual(opt.default, default)
            self.assertEqual(self.config.setting[name], default)
            self.config.setting[name] = test_value
            self.assertEqual(self.config.setting[name], test_value)

    def test_register_option_default_none(self):
        with self.assertRaises(TypeError, msg='Option default value must not be None'):
            self.config.setting.register_option("invalid_option", None)


class TestPicardConfigTextOption(TestPicardConfigCommon):
    # TextOption
    def test_text_opt_convert(self):
        opt = TextOption("setting", "text_option", "abc")
        self.assertEqual(opt.convert(123), "123")

    def test_text_opt_no_config(self):
        TextOption("setting", "text_option", "abc")

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["text_option"], "abc")
        self.assertIs(type(self.config.setting["text_option"]), str)

    def test_text_opt_set_read_back(self):
        TextOption("setting", "text_option", "abc")

        # set option to "def", and read back
        self.config.setting["text_option"] = "def"
        self.assertEqual(self.config.setting["text_option"], "def")
        self.assertIs(type(self.config.setting["text_option"]), str)

    def test_text_opt_set_none(self):
        TextOption("setting", "text_option", "abc")

        # set option to None
        self.config.setting["text_option"] = None
        self.assertEqual(self.config.setting["text_option"], "")

    def test_text_opt_set_empty(self):
        TextOption("setting", "text_option", "abc")

        # set option to ""
        self.config.setting["text_option"] = ""
        self.assertEqual(self.config.setting["text_option"], "")

    def test_text_opt_invalid_value(self):
        TextOption("setting", "text_option", "abc")

        # store invalid value in config file directly
        self.config.setValue('setting/text_option', object)
        self.assertEqual(self.config.setting["text_option"], 'abc')


class TestPicardConfigBoolOption(TestPicardConfigCommon):
    # BoolOption
    def test_bool_opt_convert(self):
        opt = BoolOption("setting", "bool_option", False)
        self.assertEqual(opt.convert(1), True)

    def test_bool_opt_no_config(self):
        BoolOption("setting", "bool_option", True)

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["bool_option"], True)
        self.assertIs(type(self.config.setting["bool_option"]), bool)

    def test_bool_opt_set_read_back(self):
        BoolOption("setting", "bool_option", True)

        # set option and read back
        self.config.setting["bool_option"] = False
        self.assertEqual(self.config.setting["bool_option"], False)
        self.assertIs(type(self.config.setting["bool_option"]), bool)

    def test_bool_opt_set_str(self):
        BoolOption("setting", "bool_option", False)

        # set option to invalid value
        self.config.setting["bool_option"] = 'yes'
        self.assertEqual(self.config.setting["bool_option"], True)

    def test_bool_opt_set_empty_str(self):
        BoolOption("setting", "bool_option", True)

        # set option to empty string
        self.config.setting["bool_option"] = ''
        self.assertEqual(self.config.setting["bool_option"], False)

    def test_bool_opt_set_none(self):
        BoolOption("setting", "bool_option", True)

        # set option to None value
        self.config.setting["bool_option"] = None
        self.assertEqual(self.config.setting["bool_option"], False)

    def test_bool_opt_set_direct_str(self):
        BoolOption("setting", "bool_option", False)

        # store invalid bool value in config file directly
        self.config.setValue('setting/bool_option', 'yes')
        self.assertEqual(self.config.setting["bool_option"], True)

    def test_bool_opt_set_direct_str_true(self):
        BoolOption("setting", "bool_option", False)

        # store 'true' directly, it should be ok, due to conversion
        self.config.setValue('setting/bool_option', 'true')
        self.assertEqual(self.config.setting["bool_option"], True)


class TestPicardConfigIntOption(TestPicardConfigCommon):
    # IntOption
    def test_int_opt_convert(self):
        opt = IntOption("setting", "int_option", 666)
        self.assertEqual(opt.convert("123"), 123)

    def test_int_opt_no_config(self):
        IntOption("setting", "int_option", 666)

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["int_option"], 666)
        self.assertIs(type(self.config.setting["int_option"]), int)

    def test_int_opt_set_read_back(self):
        IntOption("setting", "int_option", 666)

        # set option and read back
        self.config.setting["int_option"] = 333
        self.assertEqual(self.config.setting["int_option"], 333)
        self.assertIs(type(self.config.setting["int_option"]), int)

    def test_int_opt_not_int(self):
        IntOption("setting", "int_option", 666)

        # set option to invalid value
        self.config.setting["int_option"] = 'invalid'
        self.assertEqual(self.config.setting["int_option"], 666)

    def test_int_opt_set_none(self):
        IntOption("setting", "int_option", 666)

        # set option to None
        self.config.setting["int_option"] = None
        self.assertEqual(self.config.setting["int_option"], 666)

    def test_int_opt_direct_invalid(self):
        IntOption("setting", "int_option", 666)

        # store invalid int value in config file directly
        self.config.setValue('setting/int_option', 'x333')
        self.assertEqual(self.config.setting["int_option"], 666)

    def test_int_opt_direct_validstr(self):
        IntOption("setting", "int_option", 666)

        # store int as string directly, it should be ok, due to conversion
        self.config.setValue('setting/int_option', '333')
        self.assertEqual(self.config.setting["int_option"], 333)


class TestPicardConfigFloatOption(TestPicardConfigCommon):
    # FloatOption
    def test_float_opt_convert(self):
        opt = FloatOption("setting", "float_option", 666.6)
        self.assertEqual(opt.convert("333.3"), 333.3)

    def test_float_opt_no_config(self):
        FloatOption("setting", "float_option", 666.6)

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["float_option"], 666.6)
        self.assertIs(type(self.config.setting["float_option"]), float)

    def test_float_opt_set_read_back(self):
        FloatOption("setting", "float_option", 666.6)

        # set option and read back
        self.config.setting["float_option"] = 333.3
        self.assertEqual(self.config.setting["float_option"], 333.3)
        self.assertIs(type(self.config.setting["float_option"]), float)

    def test_float_opt_not_float(self):
        FloatOption("setting", "float_option", 666.6)

        # set option to invalid value
        self.config.setting["float_option"] = 'invalid'
        self.assertEqual(self.config.setting["float_option"], 666.6)

    def test_float_opt_set_none(self):
        FloatOption("setting", "float_option", 666.6)

        # set option to None
        self.config.setting["float_option"] = None
        self.assertEqual(self.config.setting["float_option"], 666.6)

    def test_float_opt_direct_invalid(self):
        FloatOption("setting", "float_option", 666.6)

        # store invalid float value in config file directly
        self.config.setValue('setting/float_option', '333.3x')
        self.assertEqual(self.config.setting["float_option"], 666.6)

    def test_float_opt_direct_validstr(self):
        FloatOption("setting", "float_option", 666.6)

        # store float as string directly, it should be ok, due to conversion
        self.config.setValue('setting/float_option', '333.3')
        self.assertEqual(self.config.setting["float_option"], 333.3)


class TestPicardConfigListOption(TestPicardConfigCommon):
    def test_list_opt_convert(self):
        opt = ListOption("setting", "list_option", [])
        self.assertEqual(opt.convert(('1', '2', '3')), ['1', '2', '3'])

    def test_list_opt_no_config(self):
        ListOption("setting", "list_option", ["a", "b"])

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["list_option"], ["a", "b"])
        self.assertIs(type(self.config.setting["list_option"]), list)

    def test_list_opt_set_read_back(self):
        ListOption("setting", "list_option", ["a", "b"])

        # set option and read back
        self.config.setting["list_option"] = ["c", "d"]
        self.assertEqual(self.config.setting["list_option"], ["c", "d"])
        self.assertIs(type(self.config.setting["list_option"]), list)

    def test_list_opt_not_list(self):
        ListOption("setting", "list_option", ["a", "b"])

        # set option to invalid value
        self.config.setting["list_option"] = 'invalid'
        self.assertEqual(self.config.setting["list_option"], ["a", "b"])

    def test_list_opt_set_none(self):
        ListOption("setting", "list_option", ["a", "b"])

        # set option to None
        self.config.setting["list_option"] = None
        self.assertEqual(self.config.setting["list_option"], [])

    def test_list_opt_set_empty(self):
        ListOption("setting", "list_option", ["a", "b"])

        # set option to empty list
        self.config.setting["list_option"] = []
        self.assertEqual(self.config.setting["list_option"], [])

    def test_list_opt_direct_invalid(self):
        ListOption("setting", "list_option", ["a", "b"])

        # store invalid list value in config file directly
        self.config.setValue('setting/list_option', 'efg')
        self.assertEqual(self.config.setting["list_option"], ["a", "b"])


class TestPicardConfigVarOption(TestPicardConfigCommon):
    # Option
    def test_var_opt_convert(self):
        opt = Option("setting", "var_option", set())
        self.assertEqual(opt.convert(["a", "b", "a"]), {"a", "b"})

    def test_var_opt_no_config(self):
        Option("setting", "var_option", {"a", "b"})

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["var_option"], {"a", "b"})
        self.assertIs(type(self.config.setting["var_option"]), set)

    def test_var_opt_set_read_back(self):
        Option("setting", "var_option", {"a", "b"})

        # set option to "def", and read back
        self.config.setting["var_option"] = {"c", "d"}
        self.assertEqual(self.config.setting["var_option"], {"c", "d"})
        self.assertIs(type(self.config.setting["var_option"]), set)

    def test_var_opt_set_none(self):
        Option("setting", "var_option", {"a", "b"})

        # set option to None
        self.config.setting["var_option"] = None
        self.assertEqual(self.config.setting["var_option"], {"a", "b"})

    def test_var_opt_set_empty(self):
        Option("setting", "var_option", {"a", "b"})

        # set option to ""
        self.config.setting["var_option"] = set()
        self.assertEqual(self.config.setting["var_option"], set())

    def test_var_opt_invalid_value(self):
        Option("setting", "var_option", {"a", "b"})

        # store invalid value in config file directly
        self.config.setValue('setting/var_option', object)
        self.assertEqual(self.config.setting["var_option"], {"a", "b"})


class TestPicardConfigSignals(TestPicardConfigCommon):
    def _set_signal_value(self, name: str, old_value: object, new_value: object):
        self.setting_name = name
        self.setting_old_value = old_value
        self.setting_new_value = new_value

    def test_file_naming_signal(self):
        TextOption('setting', 'option_text', 'abc')
        BoolOption('setting', 'option_bool', False)
        IntOption('setting', 'option_int', 1)
        FloatOption('setting', 'option_float', 1.0)
        ListOption('setting', 'option_list', [1, 2, 3])
        Option('setting', 'option_set', {1, 2, 3})
        Option('setting', 'option_dict', {'a': 1, 'b': 2, 'c': 3})

        self.config.setting.setting_changed.connect(self._set_signal_value)

        # Test text option
        self.setting_name = ''
        self.setting_old_value = ''
        self.setting_new_value = ''
        self.config.setting['option_text'] = 'def'
        self.assertEqual(self.setting_name, 'option_text')
        self.assertEqual(self.setting_old_value, 'abc')
        self.assertEqual(self.setting_new_value, 'def')

        # Test no signal if set to same value
        self.setting_name = ''
        self.setting_old_value = ''
        self.setting_new_value = ''
        self.config.setting['option_text'] = 'def'
        self.assertEqual(self.setting_name, '')
        self.assertEqual(self.setting_old_value, '')
        self.assertEqual(self.setting_new_value, '')

        # Test bool option
        self.setting_name = ''
        self.setting_old_value = ''
        self.setting_new_value = ''
        self.config.setting['option_bool'] = True
        self.assertEqual(self.setting_name, 'option_bool')
        self.assertEqual(self.setting_old_value, False)
        self.assertEqual(self.setting_new_value, True)

        # Test int option
        self.setting_name = ''
        self.setting_old_value = ''
        self.setting_new_value = ''
        self.config.setting['option_int'] = 2
        self.assertEqual(self.setting_name, 'option_int')
        self.assertEqual(self.setting_old_value, 1)
        self.assertEqual(self.setting_new_value, 2)

        # Test float option
        self.setting_name = ''
        self.setting_old_value = ''
        self.setting_new_value = ''
        self.config.setting['option_float'] = 2.5
        self.assertEqual(self.setting_name, 'option_float')
        self.assertEqual(self.setting_old_value, 1.0)
        self.assertEqual(self.setting_new_value, 2.5)

        # Test list option
        self.setting_name = ''
        self.setting_old_value = ''
        self.setting_new_value = ''
        self.config.setting['option_list'] = [3, 2, 1]
        self.assertEqual(self.setting_name, 'option_list')
        self.assertEqual(self.setting_old_value, [1, 2, 3])
        self.assertEqual(self.setting_new_value, [3, 2, 1])

        # Test option (set)
        self.setting_name = ''
        self.setting_old_value = ''
        self.setting_new_value = ''
        self.config.setting['option_set'] = {4, 5, 6}
        self.assertEqual(self.setting_name, 'option_set')
        self.assertEqual(self.setting_old_value, {1, 2, 3})
        self.assertEqual(self.setting_new_value, {4, 5, 6})

        # Test option (dict)
        self.setting_name = ''
        self.setting_old_value = ''
        self.setting_new_value = ''
        self.config.setting['option_dict'] = {'a': 3, 'b': 2, 'c': 1}
        self.assertEqual(self.setting_name, 'option_dict')
        self.assertEqual(self.setting_old_value, {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(self.setting_new_value, {'a': 3, 'b': 2, 'c': 1})


class TestPicardConfigQuickMenuItems(TestPicardConfigCommon):
    def _get_menu_items(self):
        return [x for x in get_quick_menu_items()]

    def test_register_quick_menu_items(self):
        # Save original dictionary and set new empty dictionary for testing
        old = config._quick_menu_items
        config._quick_menu_items = {}
        self.assertEqual(self._get_menu_items(), [])

        # Set up options for testing
        BoolOption('setting', 'option_bool_no_title', True)
        TextOption('setting', 'option_text', 'abc', title="Text")
        BoolOption('setting', 'option_bool', False, title="Bool")
        IntOption('setting', 'option_int', 1, title="Int")
        FloatOption('setting', 'option_float', 1.0, title="Float")
        ListOption('setting', 'option_list', [1, 2, 3], title="List")
        Option('setting', 'option_set', {1, 2, 3}, title="Set")
        Option('setting', 'option_dict', {'a': 1, 'b': 2, 'c': 3}, title="Dict")

        # Test that options without titles are not registered
        option = Option.get('setting', 'option_bool_no_title')
        register_quick_menu_item(0, "test group", option)
        menu_items = self._get_menu_items()
        self.assertEqual(len(menu_items), 0)

        # Test that only boolean options are registered
        for opt_type in ['bool', 'text', 'int', 'float', 'list', 'set', 'dict']:
            option = Option.get('setting', f"option_{opt_type}")
            register_quick_menu_item(0, "test group", option)
            menu_items = self._get_menu_items()
            self.assertEqual(len(menu_items), 1, f"Error processing '{opt_type}' option.")

        # Restore original dictionary
        config._quick_menu_items = old

    def test_return_order(self):
        # Save original dictionary and set new empty dictionary for testing
        old = config._quick_menu_items
        config._quick_menu_items = {}
        self.assertEqual(self._get_menu_items(), [])

        # Set up options for testing
        BoolOption('setting', 'option1', True, title="Option 1")
        BoolOption('setting', 'option2', True, title="Option 2")
        BoolOption('setting', 'option3', True, title="Option 3")
        BoolOption('setting', 'option4', True, title="Option 4")

        # Register options
        register_quick_menu_item(2, "Group 2", Option.get('setting', 'option4'))
        register_quick_menu_item(2, "Group 2", Option.get('setting', 'option1'))
        register_quick_menu_item(2, "Group 2", Option.get('setting', 'option2'))
        register_quick_menu_item(1, "Group 1", Option.get('setting', 'option3'))
        register_quick_menu_item(3, "Group 1", Option.get('setting', 'option4'))

        # Get menu items
        items = self._get_menu_items()
        self.assertEqual(len(items), 2)

        # Confirm order returned is:
        #   Group 1: 'option3', 'option4'
        #   Group 2: 'option4', 'option1', 'option2'

        group = items[0]
        options = group['options']
        self.assertEqual(group['group_title'], "Group 1")
        self.assertEqual(len(options), 2)
        self.assertEqual(options[0].name, 'option3')
        self.assertEqual(options[1].name, 'option4')

        group = items[1]
        options = group['options']
        self.assertEqual(group['group_title'], "Group 2")
        self.assertEqual(len(options), 3)
        self.assertEqual(options[0].name, 'option4')
        self.assertEqual(options[1].name, 'option1')
        self.assertEqual(options[2].name, 'option2')

        # Restore original dictionary
        config._quick_menu_items = old
