# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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
    ANY,
    MagicMock,
    patch,
)

from test.picardtestcase import (
    PicardTestCase,
    load_test_json,
)

import picard.collection
from picard.collection import (
    Collection,
    add_release_to_user_collections,
    get_user_collection,
    load_user_collections,
)
from picard.webservice.api_helpers import MBAPIHelper


def fake_request_handler(collection_id, releases, handler):
    handler(None, None, None)


def fake_get_collection_list(handler):
    document = load_test_json('collection_list.json')
    handler(document, None, None)


mb_api = MagicMock(auto_spec=MBAPIHelper)
mb_api.put_to_collection.side_effect = fake_request_handler
mb_api.delete_from_collection.side_effect = fake_request_handler
mb_api.get_collection_list.side_effect = fake_get_collection_list


class CollectionTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        picard.collection.user_collections = {}

    def test_collection_init(self):
        collection = Collection('foo', mb_api)
        self.assertEqual('foo', collection.id)
        self.assertEqual('', collection.name)
        self.assertEqual(0, collection.size)
        self.assertEqual(set(), collection.pending_releases)
        self.assertEqual(set(), collection.releases)
        self.assertEqual(mb_api, collection._mb_api)

    def test_collection_size(self):
        collection = Collection('foo', mb_api)
        self.assertEqual(0, collection.size)
        collection.size = 2
        self.assertEqual(2, collection.size)
        collection.size = '10'
        self.assertEqual(10, collection.size)

    def test_collection_add_releases(self):
        releases = {
            '963a7d48-5995-4751-aef8-6727cb879b9c',
            '54292079-790c-4e99-bf8d-12efa29fa3e9',
        }
        collection = Collection('foo', mb_api)
        callback = MagicMock()
        collection.add_releases(releases, callback)
        mb_api.put_to_collection.assert_called_once_with(
            'foo', list(releases), ANY)
        self.assertEqual(2, collection.size)
        self.assertEqual(releases, collection.releases)
        collection.tagger.window.set_statusbar_message.assert_called_once()

    def test_collection_remove_releases(self):
        releases = [
            '963a7d48-5995-4751-aef8-6727cb879b9c',
            '54292079-790c-4e99-bf8d-12efa29fa3e9',
            'd0e5212c-d463-4810-ab0b-a33431b38008',
        ]
        releases_to_remove = set(releases[:2])
        collection = Collection('foo', mb_api)
        collection.releases = set(releases)
        collection.size = len(releases)
        callback = MagicMock()
        collection.remove_releases(releases_to_remove, callback)
        mb_api.delete_from_collection.assert_called_once_with(
            'foo', list(releases_to_remove), ANY)
        self.assertEqual(1, collection.size)
        self.assertEqual({releases[2]}, collection.releases)
        collection.tagger.window.set_statusbar_message.assert_called_once()

    @patch('PyQt6.QtCore.QObject.tagger.mb_api', mb_api, create=True)
    def test_get_user_collection(self):
        self.assertEqual({}, picard.collection.user_collections)
        collection1 = get_user_collection('foo')
        self.assertIsInstance(collection1, Collection)
        self.assertEqual('foo', collection1.id)
        self.assertEqual(collection1, get_user_collection('foo'))
        collection2 = get_user_collection('bar')
        self.assertNotEqual(collection1, collection2)
        self.assertEqual(
            {'foo': collection1, 'bar': collection2},
            picard.collection.user_collections,
        )

    @patch('PyQt6.QtCore.QObject.tagger.mb_api', mb_api, create=True)
    def test_add_release_to_user_collections(self):
        self.set_config_values(persist={'oauth_username': 'theuser'})
        release_node = {
            'id': '54292079-790c-4e99-bf8d-12efa29fa3e9',
            'collections': [{
                'id': '00000000-0000-0000-0000-000000000001',
                'name': 'collection1',
                'editor': 'theuser',
                'release-count': 42
            }, {
                'id': '00000000-0000-0000-0000-000000000002',
                'name': 'collection2',
                'editor': 'otheruser',
                'release-count': 12
            }, {
                'id': '00000000-0000-0000-0000-000000000003',
                'name': 'collection3',
                'editor': 'theuser',
                'release-count': 0
            }]
        }
        add_release_to_user_collections(release_node)
        self.assertEqual(2, len(picard.collection.user_collections))
        collection1 = picard.collection.user_collections['00000000-0000-0000-0000-000000000001']
        collection3 = picard.collection.user_collections['00000000-0000-0000-0000-000000000003']
        self.assertEqual('collection1', collection1.name)
        self.assertIn(release_node['id'], collection1.releases)
        self.assertEqual(42, collection1.size)
        self.assertEqual('collection3', collection3.name)
        self.assertIn(release_node['id'], collection3.releases)
        self.assertEqual(0, collection3.size)

    @patch('PyQt6.QtCore.QObject.tagger.mb_api', mb_api, create=True)
    def test_load_user_collections(self):
        self.tagger.webservice.oauth_manager.is_authorized.return_value = True
        picard.collection.user_collections['old-collection'] = Collection('old-collection', mb_api)
        callback = MagicMock()
        load_user_collections(callback)
        callback.assert_called_once_with()
        self.assertEqual(3, len(picard.collection.user_collections))
        self.assertNotIn('old-collection', picard.collection.user_collections)
        collection1 = picard.collection.user_collections['40734348-a970-491a-a160-722246cfadf4']
        self.assertEqual(collection1.name, 'My Collection')
        self.assertEqual(collection1.size, 402)

    @patch('PyQt6.QtCore.QObject.tagger.mb_api', mb_api, create=True)
    def test_load_user_collections_not_authorized(self):
        self.tagger.webservice.oauth_manager.is_authorized.return_value = False
        picard.collection.user_collections['old-collection'] = Collection('old-collection', mb_api)
        callback = MagicMock()
        load_user_collections(callback)
        callback.assert_not_called()
        self.assertEqual(0, len(picard.collection.user_collections))
