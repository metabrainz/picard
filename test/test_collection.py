# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
# Copyright (C) 2025-2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


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
        self.tagger.mb_api = mb_api
        self.notifier = MagicMock()
        patcher = patch('picard.collection.notifier', return_value=self.notifier)
        patcher.start()
        self.addCleanup(patcher.stop)
        picard.collection.user_collections = {}
        mb_api.reset_mock()

    def test_collection_init(self):
        collection = Collection('foo')
        self.assertEqual('foo', collection.id)
        self.assertEqual('', collection.name)
        self.assertEqual(0, collection.size)
        self.assertEqual(set(), collection.pending_releases)
        self.assertEqual(set(), collection.releases)

    def test_collection_size(self):
        collection = Collection('foo')
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
        collection = Collection('foo')
        callback = MagicMock()
        collection.add_releases(releases, callback)
        mb_api.put_to_collection.assert_called_once_with('foo', list(releases), ANY)
        self.assertEqual(2, collection.size)
        self.assertEqual(releases, collection.releases)
        self.notifier.status_message.assert_called_once()

    def test_collection_remove_releases(self):
        releases = [
            '963a7d48-5995-4751-aef8-6727cb879b9c',
            '54292079-790c-4e99-bf8d-12efa29fa3e9',
            'd0e5212c-d463-4810-ab0b-a33431b38008',
        ]
        releases_to_remove = set(releases[:2])
        collection = Collection('foo')
        collection.releases = set(releases)
        collection.size = len(releases)
        callback = MagicMock()
        collection.remove_releases(releases_to_remove, callback)
        mb_api.delete_from_collection.assert_called_once_with('foo', list(releases_to_remove), ANY)
        self.assertEqual(1, collection.size)
        self.assertEqual({releases[2]}, collection.releases)
        self.notifier.status_message.assert_called_once()

    def test_releases_sent_in_several_requests_are_counted_once(self):
        releases = {f'00000000-0000-0000-0000-00000000000{i}' for i in range(5)}
        collection = Collection('foo')
        callback = MagicMock()
        replies = []
        # A local mock, the replies are kept to be given later, one at a time.
        slow_api = MagicMock()
        slow_api.put_to_collection.side_effect = lambda collection_id, batch, handler: replies.append((batch, handler))
        self.tagger.mb_api = slow_api
        with patch('picard.collection.COLLECTION_BATCH_SIZE', 2):
            collection.add_releases(releases, callback)
        self.assertEqual([2, 2, 1], [len(batch) for batch, _handler in replies])
        self.assertEqual(releases, {release for batch, _handler in replies for release in batch})

        # The first reply: only its own releases are done, the others are still being sent.
        batch, handler = replies[0]
        handler(None, None, None)
        self.assertEqual(set(batch), collection.releases)
        self.assertEqual(2, collection.size)
        self.assertEqual(releases - set(batch), collection.pending_releases)
        self.assertEqual(1, callback.call_count)

        for _batch, handler in replies[1:]:
            handler(None, None, None)
        self.assertEqual(releases, collection.releases)
        self.assertEqual(5, collection.size)
        self.assertEqual(set(), collection.pending_releases)
        self.assertEqual(3, callback.call_count)

    def test_releases_removed_in_several_requests_are_counted_once(self):
        releases = {f'00000000-0000-0000-0000-00000000000{i}' for i in range(5)}
        collection = Collection('foo')
        collection.releases = set(releases)
        collection.size = 5
        callback = MagicMock()
        with patch('picard.collection.COLLECTION_BATCH_SIZE', 2):
            collection.remove_releases(set(releases), callback)
        self.assertEqual(3, mb_api.delete_from_collection.call_count)
        self.assertEqual(0, collection.size)
        self.assertEqual(set(), collection.releases)
        self.assertEqual(3, callback.call_count)

    def test_a_failed_request_of_several_leaves_the_others_to_count(self):
        releases = {f'00000000-0000-0000-0000-00000000000{i}' for i in range(4)}
        collection = Collection('foo')
        callback = MagicMock()
        reply = MagicMock()
        reply.errorString.return_value = 'Service Unavailable'
        replies = []
        api = MagicMock()
        api.put_to_collection.side_effect = lambda collection_id, batch, handler: replies.append((batch, handler))
        self.tagger.mb_api = api
        with patch('picard.collection.COLLECTION_BATCH_SIZE', 2):
            collection.add_releases(releases, callback)
        (first, first_handler), (_second, second_handler) = replies
        first_handler(None, reply, 503)
        second_handler(None, None, None)
        self.assertEqual(set(_second), collection.releases)
        self.assertEqual(2, collection.size)
        self.assertEqual(set(), collection.pending_releases)
        callback.assert_any_call(error='Service Unavailable')
        self.assertEqual(2, callback.call_count)

    def test_collection_modification_error_is_reported(self):
        releases = {'963a7d48-5995-4751-aef8-6727cb879b9c'}
        reply = MagicMock()
        reply.errorString.return_value = 'Service Unavailable'
        # A local mock: the module-level one is shared by the other tests.
        failing_api = MagicMock()
        failing_api.put_to_collection.side_effect = lambda collection_id, releases, handler: handler(None, reply, 503)
        failing_api.delete_from_collection.side_effect = failing_api.put_to_collection.side_effect
        self.tagger.mb_api = failing_api
        for method in ('add_releases', 'remove_releases'):
            with self.subTest(method=method):
                collection = Collection('foo')
                collection.releases = set(releases) if method == 'remove_releases' else set()
                collection.size = len(collection.releases)
                callback = MagicMock()
                getattr(collection, method)(set(releases), callback)
                callback.assert_called_once_with(error='Service Unavailable')
                self.assertEqual(set(), collection.pending_releases)
                self.assertEqual(len(collection.releases), collection.size)

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

    def test_add_release_to_user_collections(self):
        self.set_config_values(persist={'oauth_username': 'theuser'})
        release_node = {
            'id': '54292079-790c-4e99-bf8d-12efa29fa3e9',
            'collections': [
                {
                    'id': '00000000-0000-0000-0000-000000000001',
                    'name': 'collection1',
                    'editor': 'theuser',
                    'release-count': 42,
                },
                {
                    'id': '00000000-0000-0000-0000-000000000002',
                    'name': 'collection2',
                    'editor': 'otheruser',
                    'release-count': 12,
                },
                {
                    'id': '00000000-0000-0000-0000-000000000003',
                    'name': 'collection3',
                    'editor': 'theuser',
                    'release-count': 0,
                },
            ],
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

    def test_load_user_collections(self):
        self.tagger.webservice.oauth_manager.is_authorized.return_value = True
        picard.collection.user_collections['old-collection'] = Collection('old-collection')
        callback = MagicMock()
        load_user_collections(callback)
        callback.assert_called_once_with()
        self.assertEqual(3, len(picard.collection.user_collections))
        self.assertNotIn('old-collection', picard.collection.user_collections)
        collection1 = picard.collection.user_collections['40734348-a970-491a-a160-722246cfadf4']
        self.assertEqual(collection1.name, 'My Collection')
        self.assertEqual(collection1.size, 402)

    def test_load_user_collections_not_authorized(self):
        self.tagger.webservice.oauth_manager.is_authorized.return_value = False
        picard.collection.user_collections['old-collection'] = Collection('old-collection')
        callback = MagicMock()
        load_user_collections(callback)
        # Told at once: there is nothing to wait for.
        callback.assert_called_once_with()
        self.assertEqual(0, len(picard.collection.user_collections))

    def test_load_user_collections_disabled(self):
        self.tagger.webservice.oauth_manager.is_authorized.return_value = True
        self.set_config_values(setting={'enable_user_collections': False})
        picard.collection.user_collections['old-collection'] = Collection('old-collection')
        callback = MagicMock()
        load_user_collections(callback)
        callback.assert_called_once_with()
        self.assertEqual(0, len(picard.collection.user_collections))
        mb_api.get_collection_list.assert_not_called()

    def test_load_user_collections_error(self):
        self.tagger.webservice.oauth_manager.is_authorized.return_value = True
        picard.collection.user_collections['old-collection'] = Collection('old-collection')
        reply = MagicMock()
        reply.errorString.return_value = 'Service unavailable'
        failing_api = MagicMock()
        failing_api.get_collection_list.side_effect = lambda handler: handler(None, reply, 'error')
        self.tagger.mb_api = failing_api
        callback = MagicMock()
        load_user_collections(callback)
        # The callback is told why, and the collections known so far are kept.
        callback.assert_called_once_with(error='Service unavailable')
        self.assertIn('old-collection', picard.collection.user_collections)
        self.notifier.status_message.assert_called_once()
