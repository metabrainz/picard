# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013, 2019-2021 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018-2020 Philipp Wolfer
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


import os.path

from test.picardtestcase import PicardTestCase

from picard.i18n import setup_gettext
from picard.util import bytes2human


class Testbytes2human(PicardTestCase):
    def setUp(self):
        super().setUp()
        # we are using temporary locales for tests
        self.tmp_path = self.mktmpdir()
        self.localedir = os.path.join(self.tmp_path, 'locale')

    def test_00(self):
        # testing with default C locale, english
        lang = 'C'
        setup_gettext(self.localedir, lang)
        self.run_test(lang)

        self.assertEqual(bytes2human.binary(45682), '44.6 KiB')
        self.assertEqual(bytes2human.binary(-45682), '-44.6 KiB')
        self.assertEqual(bytes2human.binary(-45682, 2), '-44.61 KiB')
        self.assertEqual(bytes2human.decimal(45682), '45.7 kB')
        self.assertEqual(bytes2human.decimal(45682, 2), '45.68 kB')
        self.assertEqual(bytes2human.decimal(9223372036854775807), '9223.4 PB')
        self.assertEqual(bytes2human.decimal(9223372036854775807, 3), '9223.372 PB')
        self.assertEqual(bytes2human.decimal(123.6), '123 B')
        self.assertRaises(ValueError, bytes2human.decimal, 'xxx')
        self.assertRaises(ValueError, bytes2human.decimal, '123.6')
        self.assertRaises(ValueError, bytes2human.binary, 'yyy')
        self.assertRaises(ValueError, bytes2human.binary, '456yyy')
        try:
            bytes2human.decimal('123')
        except Exception as e:
            self.fail('Unexpected exception: %s' % e)

    def test_calc_unit_raises_value_error(self):
        self.assertRaises(ValueError, bytes2human.calc_unit, 1, None)
        self.assertRaises(ValueError, bytes2human.calc_unit, 1, 100)
        self.assertRaises(ValueError, bytes2human.calc_unit, 1, 999)
        self.assertRaises(ValueError, bytes2human.calc_unit, 1, 1023)
        self.assertRaises(ValueError, bytes2human.calc_unit, 1, 1025)
        self.assertEqual((1.0, 'B'), bytes2human.calc_unit(1, 1024))
        self.assertEqual((1.0, 'B'), bytes2human.calc_unit(1, 1000))

    def run_test(self, lang='C', create_test_data=False):
        """
        Compare data generated with sample files
        Setting create_test_data to True will generated sample files
        from code execution (developer-only, check carefully)
        """
        filename = os.path.join('test', 'data', 'b2h_test_%s.dat' % lang)
        testlist = self._create_testlist()
        if create_test_data:
            self._save_expected_to(filename, testlist)
        expected = self._read_expected_from(filename)
        self.assertEqual(testlist, expected)
        if create_test_data:
            # be sure it is disabled
            self.fail('!!! UNSET create_test_data mode !!! (%s)' % filename)

    @staticmethod
    def _create_testlist():
        values = [0, 1]
        for n in [1000, 1024]:
            p = 1
            for e in range(0, 6):
                p *= n
                for x in [0.1, 0.5, 0.99, 0.9999, 1, 1.5]:
                    values.append(int(p * x))
        list = []
        for x in sorted(values):
            list.append(";".join([str(x), bytes2human.decimal(x),
                                  bytes2human.binary(x),
                                  bytes2human.short_string(x, 1024, 2)]))
        return list

    @staticmethod
    def _save_expected_to(path, a_list):
        with open(path, 'wb') as f:
            f.writelines([line + "\n" for line in a_list])
            f.close()

    @staticmethod
    def _read_expected_from(path):
        with open(path, 'r') as f:
            lines = [line.rstrip("\n") for line in f.readlines()]
            f.close()
            return lines

    def test_calc_unit(self):
        self.assertEqual(bytes2human.calc_unit(12456, 1024), (12.1640625, 'KiB'))
        self.assertEqual(bytes2human.calc_unit(-12456, 1000), (-12.456, 'kB'))
        self.assertRaises(ValueError, bytes2human.calc_unit, 0, 1001)
