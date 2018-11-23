from test.picardtestcase import PicardTestCase

from picard import config
from picard.dataobj import DataObject


class DataObjectTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.obj = DataObject('id')

    def test_set_genre_inc_params_no_genres(self):
        inc = []
        config.setting['use_genres'] = False
        require_auth = self.obj.set_genre_inc_params(inc)
        self.assertEqual([], inc)
        self.assertFalse(require_auth)

    def test_set_genre_inc_params_with_genres(self):
        inc = []
        config.setting['use_genres'] = True
        config.setting['folksonomy_tags'] = False
        config.setting['only_my_genres'] = False
        require_auth = self.obj.set_genre_inc_params(inc)
        self.assertIn('genres', inc)
        self.assertFalse(require_auth)

    def test_set_genre_inc_params_with_user_genres(self):
        inc = []
        config.setting['use_genres'] = True
        config.setting['folksonomy_tags'] = False
        config.setting['only_my_genres'] = True
        require_auth = self.obj.set_genre_inc_params(inc)
        self.assertIn('user-genres', inc)
        self.assertTrue(require_auth)

    def test_set_genre_inc_params_with_tags(self):
        inc = []
        config.setting['use_genres'] = True
        config.setting['folksonomy_tags'] = True
        config.setting['only_my_genres'] = False
        require_auth = self.obj.set_genre_inc_params(inc)
        self.assertIn('tags', inc)
        self.assertFalse(require_auth)

    def test_set_genre_inc_params_with_user_tags(self):
        inc = []
        config.setting['use_genres'] = True
        config.setting['folksonomy_tags'] = True
        config.setting['only_my_genres'] = True
        require_auth = self.obj.set_genre_inc_params(inc)
        self.assertIn('user-tags', inc)
        self.assertTrue(require_auth)
