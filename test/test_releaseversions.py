import json
import os.path
import unittest
import shutil
import sys
import tempfile
from picard import config
from picard.releasegroup import ReleaseGroup
from picard.i18n import setup_gettext


settings = {
    "standardize_tracks": False,
    "standardize_artists": False,
    "standardize_releases": False,
    "translate_artist_names": False
}


class ReleaseTest(unittest.TestCase):

    @staticmethod
    def load_data(filename):
        with open(os.path.join('test', 'data', 'ws_data', filename), encoding='utf-8') as f:
            return json.load(f)

    def setUp(self):
        # we are using temporary locales for tests
        self.tmp_path = tempfile.mkdtemp()
        if sys.hexversion >= 0x020700F0:
            self.addCleanup(shutil.rmtree, self.tmp_path)
        self.localedir = os.path.join(self.tmp_path, 'locale')
        setup_gettext(self.localedir, 'C')

    def tearDown(self):
        if sys.hexversion < 0x020700F0:
            shutil.rmtree(self.tmp_path)

    def test_1(self):
        config.setting = settings
        rlist = self.load_data('release_group_2.json')
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Jewel Case / special')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Digipak / special')
        self.assertEqual(r.versions[2]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Digipak / specialx')

    def test_2(self):
        config.setting = settings
        rlist = self.load_data('release_group_3.json')
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2011 / FR / CD / label A / cat 123 / special A')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2011 / FR / CD / label A / cat 123')

    def test_3(self):
        config.setting = settings
        rlist = self.load_data('release_group_4.json')
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2009 / FR / CD / label A / cat 123 / 0123456789')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2009 / FR / CD / label A / cat 123 / [no barcode]')
