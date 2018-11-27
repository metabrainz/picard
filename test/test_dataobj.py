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

    def test_add_genres(self):
        self.obj.add_genre('genre1', 2)
        self.assertEqual(self.obj.genres['genre1'], 2)
        self.obj.add_genre('genre1', 5)
        self.assertEqual(self.obj.genres['genre1'], 7)

    def test_merge_genres(self):
        genres1 = {'a': 2, 'b': 7}
        genres2 = {'b': 4, 'c': 3}
        DataObject.merge_genres(genres1, genres2)
        self.assertEqual(genres1['a'], 2)
        self.assertEqual(genres1['b'], 11)
        self.assertEqual(genres1['c'], 3)
        self.assertNotIn('a', genres2)
        self.assertEqual(genres2['b'], 4)
        self.assertEqual(genres2['c'], 3)
