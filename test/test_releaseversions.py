import os.path
import shutil
import sys
import tempfile

from test.picardtestcase import (
    PicardTestCase,
    load_test_json,
)

from picard import config
from picard.i18n import setup_gettext
from picard.releasegroup import ReleaseGroup


settings = {
    "standardize_tracks": False,
    "standardize_artists": False,
    "standardize_releases": False,
    "translate_artist_names": False
}


class ReleaseTest(PicardTestCase):

    def setUp(self):
        super().setUp()
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
        config.setting = settings.copy()
        rlist = load_test_json('release_group_2.json')
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Jewel Case / special')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Digipak / special')
        self.assertEqual(r.versions[2]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Digipak / specialx')

    def test_2(self):
        config.setting = settings.copy()
        rlist = load_test_json('release_group_3.json')
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2011 / FR / CD / label A / cat 123 / special A')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2011 / FR / CD / label A / cat 123')

    def test_3(self):
        config.setting = settings.copy()
        rlist = load_test_json('release_group_4.json')
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2009 / FR / CD / label A / cat 123 / 0123456789')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2009 / FR / CD / label A / cat 123 / [no barcode]')
