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

import os
import shutil
from tempfile import mkdtemp

from test.picardtestcase import PicardTestCase

from picard.config import *
from picard.config_upgrade import *


class TestPicardConfig(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.tmp_directory = mkdtemp()
        self.configpath = os.path.join(self.tmp_directory, 'test.ini')
        self.config = Config.from_file(None, self.configpath)
        self.config.application["version"] = "testing"

    def tearDown(self):
        shutil.rmtree(self.tmp_directory)

    def _print_config(self):
        self.config.sync()
        with open(self.configpath) as f:
            print(f.read())

    def test_remove(self):
        TextOption("setting", "text_option", "abc")

        self.config.setting["text_option"] = "def"
        self.assertEqual(self.config.setting["text_option"], "def")

        self.config.setting.remove("text_option")
        self.assertEqual(self.config.setting["text_option"], "abc")


    ### TextOption
    def test_text_opt_convert(self):
        opt = TextOption("setting", "text_option", "abc")
        self.assertEqual(opt.convert(123), "123")

    def test_text_opt_no_config(self):
        TextOption("setting", "text_option", "abc")

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["text_option"], "abc")
        self.assertEqual(type(self.config.setting["text_option"]), str)

    def test_text_opt_set_read_back(self):
        TextOption("setting", "text_option", "abc")

        # set option to "def", and read back
        self.config.setting["text_option"] = "def"
        self.assertEqual(self.config.setting["text_option"], "def")
        self.assertEqual(type(self.config.setting["text_option"]), str)

    def test_text_opt_set_None(self):
        TextOption("setting", "text_option", "abc")

        # set option to None
        self.config.setting["text_option"] = None
        self.assertEqual(self.config.setting["text_option"], "")

    def test_text_opt_set_empty(self):
        TextOption("setting", "text_option", "abc")

        # set option to ""
        self.config.setting["text_option"] = ""
        self.assertEqual(self.config.setting["text_option"], "")

    def test_text_opt_xxx(self):
        TextOption("setting", "text_option", "abc")

        # store invalid value in config file directly
        self.config.setValue('setting/text_option', object)
        self.assertEqual(self.config.setting["text_option"], 'abc')

    ### BoolOption
    def test_bool_opt_convert(self):
        opt = BoolOption("setting", "bool_option", False)
        self.assertEqual(opt.convert(1), True)

    def test_bool_opt_no_config(self):
        BoolOption("setting", "bool_option", True)

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["bool_option"], True)
        self.assertEqual(type(self.config.setting["bool_option"]), bool)

    def test_bool_opt_set_read_back(self):
        BoolOption("setting", "bool_option", True)

        # set option and read back
        self.config.setting["bool_option"] = False
        self.assertEqual(self.config.setting["bool_option"], False)
        self.assertEqual(type(self.config.setting["bool_option"]), bool)

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

    def test_bool_opt_set_None(self):
        BoolOption("setting", "bool_option", True)

        # set option to None value
        self.config.setting["bool_option"] = None
        self.assertEqual(self.config.setting["bool_option"], False)

    def test_bool_opt_set_direct_str(self):
        BoolOption("setting", "bool_option", False)

        # store invalid bool value in config file directly
        self.config.setValue('setting/bool_option', 'yes')
        self.assertEqual(self.config.setting["bool_option"], True)

    def test_bool_opt_set_direct_str_true(self):
        BoolOption("setting", "bool_option", False)

        # store 'true' directly, it should be ok, due to conversion
        self.config.setValue('setting/bool_option', 'true')
        self.assertEqual(self.config.setting["bool_option"], True)

    ### IntOption
    def test_int_opt_convert(self):
        opt = IntOption("setting", "int_option", 666)
        self.assertEqual(opt.convert("123"), 123)

    def test_int_opt_no_config(self):
        IntOption("setting", "int_option", 666)

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["int_option"], 666)
        self.assertEqual(type(self.config.setting["int_option"]), int)

    def test_int_opt_set_read_back(self):
        IntOption("setting", "int_option", 666)

        # set option and read back
        self.config.setting["int_option"] = 333
        self.assertEqual(self.config.setting["int_option"], 333)
        self.assertEqual(type(self.config.setting["int_option"]), int)

    def test_int_opt_not_int(self):
        IntOption("setting", "int_option", 666)

        # set option to invalid value
        self.config.setting["int_option"] = 'invalid'
        self.assertEqual(self.config.setting["int_option"], 666)

    def test_int_opt_set_None(self):
        IntOption("setting", "int_option", 666)

        # set option to None
        self.config.setting["int_option"] = None
        self.assertEqual(self.config.setting["int_option"], 666)

    def test_int_opt_direct_invalid(self):
        IntOption("setting", "int_option", 666)

        # store invalid int value in config file directly
        self.config.setValue('setting/int_option', 'x333')
        self.assertEqual(self.config.setting["int_option"], 666)

    def test_int_opt_direct_validstr(self):
        IntOption("setting", "int_option", 666)

        # store int as string directly, it should be ok, due to conversion
        self.config.setValue('setting/int_option', '333')
        self.assertEqual(self.config.setting["int_option"], 333)

    # FloatOption
    def test_float_opt_convert(self):
        opt = FloatOption("setting", "float_option", 666.6)
        self.assertEqual(opt.convert("333.3"), 333.3)

    def test_float_opt_no_config(self):
        FloatOption("setting", "float_option", 666.6)

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["float_option"], 666.6)
        self.assertEqual(type(self.config.setting["float_option"]), float)

    def test_float_opt_set_read_back(self):
        FloatOption("setting", "float_option", 666.6)

        # set option and read back
        self.config.setting["float_option"] = 333.3
        self.assertEqual(self.config.setting["float_option"], 333.3)
        self.assertEqual(type(self.config.setting["float_option"]), float)

    def test_float_opt_not_float(self):
        FloatOption("setting", "float_option", 666.6)

        # set option to invalid value
        self.config.setting["float_option"] = 'invalid'
        self.assertEqual(self.config.setting["float_option"], 666.6)

    def test_float_opt_set_None(self):
        FloatOption("setting", "float_option", 666.6)

        # set option to None
        self.config.setting["float_option"] = None
        self.assertEqual(self.config.setting["float_option"], 666.6)

    def test_float_opt_direct_invalid(self):
        FloatOption("setting", "float_option", 666.6)

        # store invalid float value in config file directly
        self.config.setValue('setting/float_option', '333.3x')
        self.assertEqual(self.config.setting["float_option"], 666.6)

    def test_float_opt_direct_validstr(self):
        FloatOption("setting", "float_option", 666.6)

        # store float as string directly, it should be ok, due to conversion
        self.config.setValue('setting/float_option', '333.3')
        self.assertEqual(self.config.setting["float_option"], 333.3)

    ### ListOption
    def test_list_opt_convert(self):
        opt = ListOption("setting", "list_option", [])
        self.assertEqual(opt.convert("123"), ['1', '2', '3'])

    def test_list_opt_no_config(self):
        ListOption("setting", "list_option", ["a", "b"])

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["list_option"], ["a", "b"])
        self.assertEqual(type(self.config.setting["list_option"]), list)

    def test_list_opt_set_read_back(self):
        ListOption("setting", "list_option", ["a", "b"])

        # set option and read back
        self.config.setting["list_option"] = ["c", "d"]
        self.assertEqual(self.config.setting["list_option"], ["c", "d"])
        self.assertEqual(type(self.config.setting["list_option"]), list)

    def test_list_opt_not_list(self):
        ListOption("setting", "list_option", ["a", "b"])

        # set option to invalid value
        self.config.setting["list_option"] = 'invalid'
        self.assertEqual(self.config.setting["list_option"], ["a", "b"])

    def test_list_opt_set_None(self):
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

        # store invalid list value in config file directly
        self.config.setValue('setting/list_option', 'efg')
        self.assertEqual(self.config.setting["list_option"], ["a", "b"])

    ### IntListOption
    def test_intlist_opt_convert(self):
        opt = IntListOption("setting", "intlist_option", [])
        self.assertEqual(opt.convert(["1", "2", "3"]), [1 ,2 ,3])

    def test_intlist_opt_no_config(self):
        IntListOption("setting", "intlist_option", [1, 2])

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["intlist_option"], [1, 2])
        self.assertEqual(type(self.config.setting["intlist_option"]), list)

    def test_intlist_opt_set_read_back(self):
        IntListOption("setting", "intlist_option", [1, 2])

        # set option and read back
        self.config.setting["intlist_option"] = [3, 4]
        self.assertEqual(self.config.setting["intlist_option"], [3, 4])
        self.assertEqual(type(self.config.setting["intlist_option"]), list)

    def test_intlist_opt_not_intlist(self):
        IntListOption("setting", "intlist_option", [1, 2])

        # set option to invalid value
        self.config.setting["intlist_option"] = [5, "a"]
        self.assertEqual(self.config.setting["intlist_option"], [1, 2])

    def test_intlist_opt_set_None(self):
        IntListOption("setting", "intlist_option", [1, 2])

        # set option to None
        self.config.setting["intlist_option"] = None
        self.assertEqual(self.config.setting["intlist_option"], [])

    def test_intlist_opt_set_empty(self):
        IntListOption("setting", "intlist_option", [1, 2])

        # set option to empty intlist
        self.config.setting["intlist_option"] = []
        self.assertEqual(self.config.setting["intlist_option"], [])

    def test_intlist_opt_direct_invalid(self):
        IntListOption("setting", "intlist_option", [1, 2])

        # store invalid intlist value in config file directly
        self.config.setValue('setting/intlist_option', 'efg')
        self.assertEqual(self.config.setting["intlist_option"], [1, 2])

    ### Option
    def test_var_opt_convert(self):
        opt = Option("setting", "var_option", set())
        self.assertEqual(opt.convert(["a", "b", "a"]), {"a", "b"})

    def test_var_opt_no_config(self):
        Option("setting", "var_option", set(["a", "b"]))

        # test default, nothing in config yet
        self.assertEqual(self.config.setting["var_option"], set(["a", "b"]))
        self.assertEqual(type(self.config.setting["var_option"]), set)

    def test_var_opt_set_read_back(self):
        Option("setting", "var_option", set(["a", "b"]))

        # set option to "def", and read back
        self.config.setting["var_option"] = set(["c", "d"])
        self.assertEqual(self.config.setting["var_option"], set(["c", "d"]))
        self.assertEqual(type(self.config.setting["var_option"]), set)

    def test_var_opt_set_None(self):
        Option("setting", "var_option", set(["a", "b"]))

        # set option to None
        self.config.setting["var_option"] = None
        self.assertEqual(self.config.setting["var_option"], set(["a", "b"]))

    def test_var_opt_set_empty(self):
        Option("setting", "var_option", set(["a", "b"]))

        # set option to ""
        self.config.setting["var_option"] = set()
        self.assertEqual(self.config.setting["var_option"], set())

    def test_var_opt_xxx(self):
        Option("setting", "var_option", set(["a", "b"]))

        # store invalid value in config file directly
        self.config.setValue('setting/var_option', object)
        self.assertEqual(self.config.setting["var_option"], set(["a", "b"]))

    def test_upgrade_to_v1_0_0_final_0_A(self):
        TextOption('setting', 'file_naming_format', '')

        self.config.setting['va_file_naming_format'] = 'abc'
        self.config.setting['use_va_format'] = True

        self.assertIn('va_file_naming_format', self.config.setting)
        self.assertIn('use_va_format', self.config.setting)

        upgrade_to_v1_0_0_final_0(self.config, interactive=False, merge=True)
        self.assertNotIn('va_file_naming_format', self.config.setting)
        self.assertNotIn('use_va_format', self.config.setting)
        self.assertIn('file_naming_format', self.config.setting)

    def test_upgrade_to_v1_0_0_final_0_B(self):
        TextOption('setting', 'file_naming_format', '')

        self.config.setting['va_file_naming_format'] = 'abc'
        self.config.setting['use_va_format'] = ""

        self.assertIn('va_file_naming_format', self.config.setting)
        self.assertIn('use_va_format', self.config.setting)

        upgrade_to_v1_0_0_final_0(self.config, interactive=False, merge=False)
        self.assertNotIn('va_file_naming_format', self.config.setting)
        self.assertNotIn('use_va_format', self.config.setting)
        self.assertNotIn('file_naming_format', self.config.setting)

    def test_upgrade_to_v1_3_0_dev_1(self):
        BoolOption('setting', 'windows_compatibility', False)

        self.config.setting['windows_compatible_filenames'] = True
        upgrade_to_v1_3_0_dev_1(self.config)
        self.assertNotIn('windows_compatible_filenames', self.config.setting)
        self.assertTrue(self.config.setting['windows_compatibility'])

    def test_upgrade_to_v1_3_0_dev_2(self):
        TextOption('setting', 'preserved_tags', '')
        self.config.setting['preserved_tags'] = "a b  c  "
        upgrade_to_v1_3_0_dev_2(self.config)
        self.assertEqual("a,b,c", self.config.setting['preserved_tags'])

    def test_upgrade_to_v1_3_0_dev_3(self):
        ListOption("setting", "preferred_release_countries", [])
        ListOption("setting", "preferred_release_formats", [])
        ListOption("setting", "enabled_plugins", [])
        ListOption("setting", "caa_image_types", [])
        ListOption("setting", "metadata_box_sizes", [])

        self.config.setting['preferred_release_countries'] = "a  b  c"
        self.config.setting['preferred_release_formats'] = "a  b  c"
        self.config.setting['enabled_plugins'] = 'a b c'
        self.config.setting['caa_image_types'] = 'a b c'
        self.config.setting['metadata_box_sizes'] = 'a b c'

        upgrade_to_v1_3_0_dev_3(self.config)
        self.assertEqual(["a", "b", "c"], self.config.setting['preferred_release_countries'])
        self.assertEqual(["a", "b", "c"], self.config.setting['preferred_release_formats'])
        self.assertEqual(["a", "b", "c"], self.config.setting['enabled_plugins'])
        self.assertEqual(["a", "b", "c"], self.config.setting['caa_image_types'])
        self.assertEqual(["a", "b", "c"], self.config.setting['metadata_box_sizes'])
