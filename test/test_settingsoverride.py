from test.picardtestcase import PicardTestCase

from picard import config
from picard.util.settingsoverride import SettingsOverride


class SettingsOverrideTest(PicardTestCase):

    def setUp(self):
        self.config = {'key1': 'origval1', 'key2': 'origval2'}
        config.setting = self.config.copy()
        self.new_settings = {'key1': 'newval2'}

    def test_read_orig_settings(self):
        override = SettingsOverride(config.setting, self.new_settings)
        self.assertEqual(override['key1'], 'newval2')
        self.assertEqual(override['key2'], 'origval2')
        with self.assertRaises(KeyError):
            x = override['key3']

    def test_read_orig_settings_kw(self):
        override = SettingsOverride(config.setting, key1='newval2')
        self.assertEqual(override['key1'], 'newval2')
        self.assertEqual(override['key2'], 'origval2')

    def test_write_orig_settings(self):
        override = SettingsOverride(config.setting, self.new_settings)
        override['key1'] = 'newval3'
        self.assertEqual(override['key1'], 'newval3')
        self.assertEqual(config.setting['key1'], 'origval1')

        override['key2'] = 'newval4'
        self.assertEqual(override['key2'], 'newval4')
        self.assertEqual(config.setting['key2'], 'origval2')

        override['key3'] = 'newval5'
        self.assertEqual(override['key3'], 'newval5')
        with self.assertRaises(KeyError):
            x = config.setting['key3']

    def test_del_orig_settings(self):
        override = SettingsOverride(config.setting, self.new_settings)

        override['key1'] = 'newval3'
        self.assertEqual(override['key1'], 'newval3')
        del override['key1']
        self.assertEqual(override['key1'], 'origval1')

        self.assertEqual(override['key2'], 'origval2')
        del override['key2']
        self.assertEqual(override['key2'], 'origval2')
