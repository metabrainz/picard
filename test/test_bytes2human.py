import locale
import os.path
import shutil
import subprocess
import sys
import tempfile
import unittest

from picard.i18n import setup_gettext
from picard.util import bytes2human


class Testbytes2human(unittest.TestCase):
    def setUp(self):
        # we are using temporary locales for tests
        self.tmp_path = tempfile.mkdtemp().decode("utf-8")
        if sys.hexversion >= 0x020700F0:
            self.addCleanup(shutil.rmtree, self.tmp_path)
        self.localedir = os.path.join(self.tmp_path, 'locale')

    def tearDown(self):
        if sys.hexversion < 0x020700F0:
            shutil.rmtree(self.tmp_path)

    def test_00(self):
        # testing with default C locale, english
        lang = 'C'
        setup_gettext(self.localedir, lang)
        self.run_test(lang)

        self.assertEqual(bytes2human.binary(1000), '1000 B')
        self.assertEqual(bytes2human.binary(1023), '1023 B')
        self.assertEqual(bytes2human.binary(1024), '1 KiB')
        self.assertEqual(bytes2human.binary(1048575), '1023.9 KiB')
        self.assertEqual(bytes2human.binary(1048575, 3), '1023.999 KiB')
        self.assertEqual(bytes2human.binary(1048576), '1 MiB')
        self.assertEqual(bytes2human.binary(1073741823), '1023.9 MiB')
        self.assertEqual(bytes2human.binary(1073741824), '1 GiB')
        self.assertEqual(bytes2human.binary(1099511627775), '1023.9 GiB')
        self.assertEqual(bytes2human.binary(1099511627776), '1 TiB')
        self.assertEqual(bytes2human.binary(1125899906842623), '1023.9 TiB')
        self.assertEqual(bytes2human.binary(1125899906842624), '1 PiB')
        self.assertEqual(bytes2human.binary(45682), '44.6 KiB')
        self.assertEqual(bytes2human.binary(45682), '44.6 KiB')
        self.assertEqual(bytes2human.binary(-45682), '-44.6 KiB')
        self.assertEqual(bytes2human.binary(-45682, 2), '-44.61 KiB')
        self.assertEqual(bytes2human.decimal(999), '999 B')
        self.assertEqual(bytes2human.decimal(1000), '1 kB')
        self.assertEqual(bytes2human.decimal(999999), '999.9 kB')
        self.assertEqual(bytes2human.decimal(999999, 3), '999.999 kB')
        self.assertEqual(bytes2human.decimal(1000000), '1 MB')
        self.assertEqual(bytes2human.decimal(999999999), '999.9 MB')
        self.assertEqual(bytes2human.decimal(1000000000), '1 GB')
        self.assertEqual(bytes2human.decimal(999999999999), '999.9 GB')
        self.assertEqual(bytes2human.decimal(1000000000000), '1 TB')
        self.assertEqual(bytes2human.decimal(999999999999999), '999.9 TB')
        self.assertEqual(bytes2human.decimal(1000000000000000), '1 PB')
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
            bytes2human.decimal(u'123')
        except Exception as e:
            self.fail('Unexpected exception: %s' % e)

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
        #self.maxDiff = None
        self.assertEqual(testlist, expected)
        if create_test_data:
            # be sure it is disabled
            self.fail('!!! UNSET create_test_data mode !!! (%s)' % filename)

    def _create_testlist(self):
        values = [0, 1]
        for n in [1000, 1024]:
            p = 1
            for e in range(0, 6):
                p *= n
                for x in [0.1, 0.5, 0.99, 0.9999, 1, 1.5]:
                    values.append(int(p * x))
        l = []
        for x in sorted(values):
            l.append(";".join([str(x), bytes2human.decimal(x),
                               bytes2human.binary(x),
                               bytes2human.short_string(x, 1024, 2)]))
        return l

    def _save_expected_to(self, path, a_list):
        with open(path, 'wb') as f:
            f.writelines([l + "\n" for l in a_list])
            f.close()

    def _read_expected_from(self, path):
        with open(path, 'rU') as f:
            lines = [l.rstrip("\n") for l in f.readlines()]
            f.close()
            return lines
