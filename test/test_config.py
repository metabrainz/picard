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
import shutil

from test.picardtestcase import PicardTestCase

from picard.config import (
    BoolOption,
    Config,
    FloatOption,
    IntOption,
    ListOption,
    Option,
    OptionError,
    TextOption,
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
        logging.disable(logging.ERROR)
        Option.registry = {}

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

    def test_option_exists(self):
        Option("setting", "option", "abc")
        self.assertTrue(Option.exists("setting", "option"))
        self.assertFalse(Option.exists("setting", "not_option"))

    def test_option_add_if_missing(self):
        Option("setting", "option", "abc")
        Option.add_if_missing("setting", "option", "def")
        self.assertEqual(self.config.setting["option"], "abc")

        Option.add_if_missing("setting", "missing_option", "def")
        self.assertEqual(self.config.setting["missing_option"], "def")

    def test_double_declaration(self):
        Option("setting", "option", "abc")
        with self.assertRaisesRegex(OptionError, r"^Option setting/option: Already declared"):
            Option("setting", "option", "def")


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
