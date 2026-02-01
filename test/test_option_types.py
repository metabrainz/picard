# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Bob Swift
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


from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.config import (
    BoolOption,
    FloatOption,
    IntOption,
    ListOption,
    Option,
    TextOption,
)


class OptionTestFailure(Exception):
    pass


class OptionTypeCheckTest(PicardTestCase):
    def test_option_types_valid(self):
        """Test that valid option types do not raise warnings."""

        mock_do_logging = MagicMock()
        mock_do_logging.side_effect = OptionTestFailure('Option type check failed')

        # Save original registry
        option_registry = Option.registry.copy()

        with patch('picard.config.Option._do_logging', mock_do_logging):
            # Valid option settings
            BoolOption('setting', 'valid_bool_option', True)
            IntOption('setting', 'valid_int_option', 42)
            FloatOption('setting', 'valid_float_option', 3.14)
            TextOption('setting', 'valid_text_option', 'default')
            ListOption('setting', 'valid_list_option_1', ['item1', 'item2'])
            ListOption('setting', 'valid_list_option_2', ('item1', 'item2'))
            Option('setting', 'valid_option', {'key': 'value'})

        # Restore original registry
        Option.registry = option_registry

    def test_option_types_invalid(self):
        """Test that invalid option types raise warnings."""

        mock_do_logging = MagicMock()
        mock_do_logging.side_effect = OptionTestFailure('Option type check failed')

        # Save original registry
        option_registry = Option.registry.copy()

        with patch('picard.config.Option._do_logging', mock_do_logging):
            test_defs = [
                # BoolOption tests
                (BoolOption, 'invalid_bool_option_1', 1),
                (BoolOption, 'invalid_bool_option_2', 1.1),
                (BoolOption, 'invalid_bool_option_3', ''),
                (BoolOption, 'invalid_bool_option_4', []),
                (BoolOption, 'invalid_bool_option_5', ()),
                (BoolOption, 'invalid_bool_option_6', {'foo': 'bar'}),
                # IntOption tests
                (IntOption, 'invalid_int_option_1', True),
                (IntOption, 'invalid_int_option_2', 1.1),
                (IntOption, 'invalid_int_option_3', ''),
                (IntOption, 'invalid_int_option_4', []),
                (IntOption, 'invalid_int_option_5', ()),
                (IntOption, 'invalid_int_option_6', {'foo': 'bar'}),
                # FloatOption tests
                (FloatOption, 'invalid_float_option_1', True),
                (FloatOption, 'invalid_float_option_2', 1),
                (FloatOption, 'invalid_float_option_3', ''),
                (FloatOption, 'invalid_float_option_4', []),
                (FloatOption, 'invalid_float_option_5', ()),
                (FloatOption, 'invalid_float_option_6', {'foo': 'bar'}),
                # TextOption tests
                (TextOption, 'invalid_text_option_1', True),
                (TextOption, 'invalid_text_option_2', 1),
                (TextOption, 'invalid_text_option_3', 1.1),
                (TextOption, 'invalid_text_option_4', []),
                (TextOption, 'invalid_text_option_5', ()),
                (TextOption, 'invalid_text_option_6', {'foo': 'bar'}),
                # ListOption tests
                (ListOption, 'invalid_list_option_1', True),
                (ListOption, 'invalid_list_option_2', 1),
                (ListOption, 'invalid_list_option_3', 1.1),
                (ListOption, 'invalid_list_option_4', ''),
                (ListOption, 'invalid_list_option_5', {'foo': 'bar'}),
            ]

            # Invalid option settings
            for test_case in test_defs:
                with self.assertRaises(OptionTestFailure, msg=f"Testing '{test_case[1]}'"):
                    test_case[0]('setting', test_case[1], test_case[2])

        # Restore original registry
        Option.registry = option_registry
