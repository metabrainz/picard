# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018 Philipp Wolfer
# Copyright (C) 2020-2021 Laurent Monin
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


from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard import config
from picard.dataobj import DataObject


class DataObjectTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.obj = DataObject('id')

    def test_set_genre_inc_params_no_genres(self):
        inc = set()
        config.setting['use_genres'] = False
        require_auth = self.obj.set_genre_inc_params(inc)
        self.assertEqual(set(), inc)
        self.assertFalse(require_auth)

    def test_set_genre_inc_params_with_genres(self):
        inc = set()
        config.setting['use_genres'] = True
        config.setting['folksonomy_tags'] = False
        config.setting['only_my_genres'] = False
        require_auth = self.obj.set_genre_inc_params(inc)
        self.assertIn('genres', inc)
        self.assertFalse(require_auth)

    def test_set_genre_inc_params_with_user_genres(self):
        inc = set()
        config.setting['use_genres'] = True
        config.setting['folksonomy_tags'] = False
        config.setting['only_my_genres'] = True
        require_auth = self.obj.set_genre_inc_params(inc)
        self.assertIn('user-genres', inc)
        self.assertTrue(require_auth)

    def test_set_genre_inc_params_with_tags(self):
        inc = set()
        config.setting['use_genres'] = True
        config.setting['folksonomy_tags'] = True
        config.setting['only_my_genres'] = False
        require_auth = self.obj.set_genre_inc_params(inc)
        self.assertIn('tags', inc)
        self.assertFalse(require_auth)

    def test_set_genre_inc_params_with_user_tags(self):
        inc = set()
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

    def test_set_genre_inc_custom_config(self):
        inc = set()
        config.setting['use_genres'] = False
        config.setting['folksonomy_tags'] = False
        config.setting['only_my_genres'] = False
        custom_config = Mock()
        custom_config.setting = {
            'use_genres': True,
            'folksonomy_tags': True,
            'only_my_genres': True,
        }
        require_auth = self.obj.set_genre_inc_params(inc, custom_config)
        self.assertIn('user-tags', inc)
        self.assertTrue(require_auth)
