#
# Copyright (C) 2026 Laurent Monin
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

"""``collection ls``, ``collection add``, ``collection rm`` and the ``k`` handles."""

import json
from unittest.mock import MagicMock

from test.cli.engine.helpers import EngineCommandTestCase

from picard import collection as collection_module
from picard.album import (
    Album,
    NatAlbum,
)
from picard.cli.engine.session import classify_entity
from picard.collection import Collection


_RELEASE_1 = '11111111-0000-0000-0000-000000000001'
_RELEASE_2 = '22222222-0000-0000-0000-000000000002'
_COLLECTION_1 = 'cccccccc-0000-0000-0000-000000000001'
_COLLECTION_2 = 'cccccccc-0000-0000-0000-000000000002'


def _node(collection_id, name, count):
    return {'id': collection_id, 'name': name, 'entity-type': 'release', 'release-count': count}


class CollectionCommandTestCase(EngineCommandTestCase):
    """A user with two collections, and a web service that answers at once."""

    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'enable_user_collections': True})
        self.oauth = MagicMock()
        self.oauth.is_authorized.return_value = True
        self.tagger.webservice = MagicMock()
        self.tagger.webservice.oauth_manager = self.oauth
        self.remote = {_COLLECTION_1: {_RELEASE_1}, _COLLECTION_2: set()}
        self.fail_with = None
        self.api = MagicMock()
        self.api.get_collection_list.side_effect = self._get_collection_list
        self.api.put_to_collection.side_effect = self._put
        self.api.delete_from_collection.side_effect = self._delete
        self.tagger.mb_api = self.api
        self._saved = collection_module.user_collections
        collection_module.user_collections = {}
        self.addCleanup(self._restore)
        self.albums = []
        for release_id in (_RELEASE_1, _RELEASE_2):
            album = Album(release_id)
            album.loaded = True
            self.wks.albums[release_id] = album
            self.albums.append(album)

    def _restore(self):
        collection_module.user_collections = self._saved

    def _get_collection_list(self, handler):
        nodes = [
            _node(_COLLECTION_1, 'Favourites', len(self.remote[_COLLECTION_1])),
            _node(_COLLECTION_2, 'To buy', len(self.remote[_COLLECTION_2])),
        ]
        handler({'collections': nodes}, None, None)

    def _reply(self):
        reply = MagicMock()
        reply.errorString.return_value = self.fail_with
        return reply

    def _put(self, collection_id, releases, handler):
        if self.fail_with:
            handler(None, self._reply(), 503)
            return
        self.remote[collection_id] |= set(releases)
        handler(None, None, None)

    def _delete(self, collection_id, releases, handler):
        if self.fail_with:
            handler(None, self._reply(), 503)
            return
        self.remote[collection_id] -= set(releases)
        handler(None, None, None)

    def listed(self):
        result = self.run_command('collection ls')
        self.assertTrue(result.ok, result.error)
        return result


class CollectionHandleTest(CollectionCommandTestCase):
    def test_classified_as_k(self):
        self.assertEqual('k', classify_entity(Collection('x')))

    def test_k_handles_resolve(self):
        self.listed()
        entities, unresolved = self.session.resolve('k*')
        self.assertEqual(['Favourites', 'To buy'], [c.name for c in entities])
        self.assertEqual([], unresolved)
        self.assertEqual(['Favourites'], [c.name for c in self.session.resolve('k1')[0]])

    def test_ls_shows_collections_and_remove_skips_them(self):
        self.listed()
        self.assertEqual(['skipped'], [i.status for i in self.run_command('remove k1').items])
        self.assertEqual(2, len(self.run_command('ls k*').items))

    def test_a_collection_cannot_be_saved(self):
        self.listed()
        result = self.run_command('save k1')
        self.assertFalse(result.ok)
        self.assertIn('collection', result.error)

    def test_tree_of_a_collection(self):
        self.listed()
        self.assertEqual(['collection'], [i.status for i in self.run_command('tree k1').items])


class CollectionLsTest(CollectionCommandTestCase):
    def test_lists_the_collections(self):
        result = self.listed()
        self.assertEqual(['k1', 'k2'], [i.handle for i in result.items])
        self.assertEqual(['k1', 'k2'], result.mints)
        first = result.items[0]
        self.assertEqual('collection', first.data['entity_type'])
        self.assertEqual(_COLLECTION_1, first.data['mbid'])
        self.assertEqual('Favourites', first.data['title'])
        self.assertEqual(1, first.data['size'])
        json.dumps(result.to_dict())

    def test_lists_the_albums_known_to_be_in(self):
        self.listed()
        get = collection_module.user_collections[_COLLECTION_1]
        get.releases = {_RELEASE_1}
        result = self.run_command('collection ls')
        album_handle = self.session.handle_for(self.albums[0])
        self.assertEqual([album_handle], result.items[0].data['albums'])
        self.assertEqual([], result.items[1].data['albums'])

    def test_standalone_recordings_are_not_listed_as_in(self):
        self.listed()
        collection_module.user_collections[_COLLECTION_1].releases = {'NATS'}
        self.wks.albums['NATS'] = NatAlbum()
        self.assertEqual([], self.run_command('collection ls').items[0].data['albums'])

    def test_not_logged_in(self):
        self.oauth.is_authorized.return_value = False
        result = self.run_command('collection ls')
        self.assertFalse(result.ok)
        self.assertIn("not logged in (see 'login')", result.error)
        self.api.get_collection_list.assert_not_called()

    def test_disabled(self):
        self.set_config_values(setting={'enable_user_collections': False})
        result = self.run_command('collection ls')
        self.assertFalse(result.ok)
        self.assertIn('enable_user_collections', result.error)

    def test_request_failed(self):
        reply = MagicMock()
        reply.errorString.return_value = 'Service Unavailable'
        self.api.get_collection_list.side_effect = lambda handler: handler(None, reply, 503)
        result = self.run_command('collection ls')
        self.assertFalse(result.ok)
        self.assertIn('Service Unavailable', result.error)

    def test_timeout(self):
        self.api.get_collection_list.side_effect = lambda handler: None
        self.session._app.run_until_idle.return_value = False
        result = self.run_command('collection ls')
        self.assertFalse(result.ok)
        self.assertIn('timed out', result.error)


class CollectionAddRmTest(CollectionCommandTestCase):
    def setUp(self):
        super().setUp()
        self.listed()
        self.second = self.session.handle_for(self.albums[1])

    def test_add(self):
        result = self.run_command(f'collection add k2 {self.second}')
        self.assertTrue(result.ok, result.error)
        item = result.items[0]
        self.assertEqual('added', item.status)
        self.assertEqual('k2', item.handle)
        self.assertEqual({_RELEASE_2}, self.remote[_COLLECTION_2])
        self.assertEqual(1, item.data['size'])
        self.assertEqual([self.second], item.data['albums'])
        self.assertEqual(['k2', self.second], result.resolved)

    def test_add_several_albums(self):
        result = self.run_command('collection add k2 a*')
        self.assertEqual('added', result.items[0].status)
        self.assertEqual({_RELEASE_1, _RELEASE_2}, self.remote[_COLLECTION_2])
        self.assertEqual(2, result.items[0].data['size'])

    def test_add_what_is_known_to_be_in_changes_nothing(self):
        collection_module.user_collections[_COLLECTION_1].releases = {_RELEASE_1}
        result = self.run_command(f'collection add k1 {self.session.handle_for(self.albums[0])}')
        self.assertEqual('unchanged', result.items[0].status)
        self.api.put_to_collection.assert_not_called()

    def test_only_what_is_missing_is_sent(self):
        collection_module.user_collections[_COLLECTION_1].releases = {_RELEASE_1}
        self.run_command('collection add k1 a*')
        self.assertEqual([_RELEASE_2], self.api.put_to_collection.call_args.args[1])

    def test_rm(self):
        result = self.run_command(f'collection rm k1 {self.session.handle_for(self.albums[0])}')
        self.assertTrue(result.ok, result.error)
        self.assertEqual('removed', result.items[0].status)
        self.assertEqual(set(), self.remote[_COLLECTION_1])
        self.assertEqual(0, result.items[0].data['size'])

    def test_rm_is_sent_even_if_the_album_does_not_know(self):
        # collection.releases is empty: the album was loaded before the login.
        self.run_command(f'collection rm k1 {self.session.handle_for(self.albums[0])}')
        self.api.delete_from_collection.assert_called_once()

    def test_standalone_recordings_are_left_out(self):
        nat = NatAlbum()
        self.wks.albums['NATS'] = nat
        result = self.run_command(f'collection add k2 {self.session.handle_for(nat)}')
        self.assertFalse(result.ok)
        self.assertIn('no album selected', result.error)
        self.api.put_to_collection.assert_not_called()

    def test_failure_is_reported(self):
        self.fail_with = 'Service Unavailable'
        for verb in ('add', 'rm'):
            with self.subTest(verb=verb):
                item = self.run_command(f'collection {verb} k1 {self.second}').items[0]
                self.assertEqual('failed', item.status)
                self.assertEqual('Service Unavailable', item.data['error'])

    def test_a_request_still_running_is_not_reported_as_done(self):
        # The releases are in flight from a command that gave up waiting: the
        # collection sends nothing and nothing answers.
        collection_module.user_collections[_COLLECTION_2].pending_releases = {_RELEASE_2}
        result = self.run_command(f'collection add k2 {self.second}')
        self.api.put_to_collection.assert_not_called()
        self.assertEqual('timeout', result.items[0].status)
        self.assertIn('still', result.message)

    def test_a_request_of_several_that_failed_is_reported_as_failed_with_a_hint(self):
        # Several requests are made for many releases: one is refused, the others are not.
        def put(collection_id, releases, handler):
            handler(None, None, None)
            handler(None, self._reply(), 503)

        self.fail_with = 'Service Unavailable'
        self.api.put_to_collection.side_effect = put
        result = self.run_command(f'collection add k2 {self.second}')
        item = result.items[0]
        self.assertEqual('failed', item.status)
        self.assertIn('Service Unavailable', item.data['error'])
        self.assertIn('collection ls', result.message)

    def test_timeout(self):
        self.api.put_to_collection.side_effect = lambda *a: None
        self.session._app.run_until_idle.return_value = False
        result = self.run_command(f'collection add k2 {self.second}')
        self.assertEqual('timeout', result.items[0].status)
        self.assertIn('timed out', result.message)

    def test_needs_one_collection(self):
        for text in ('k*', 'a1', 'k9'):
            with self.subTest(text=text):
                result = self.run_command(f'collection add {text} a1')
                self.assertFalse(result.ok)
                self.assertIn('exactly one collection', result.error)
        self.api.put_to_collection.assert_not_called()

    def test_usage(self):
        for line in ('collection add', 'collection add k1', 'collection rm', 'collection rm k1'):
            with self.subTest(line=line):
                result = self.run_command(line)
                self.assertFalse(result.ok)
                self.assertIn('usage', result.error)

    def test_not_logged_in(self):
        self.oauth.is_authorized.return_value = False
        result = self.run_command('collection add k1 a1')
        self.assertFalse(result.ok)
        self.assertIn('not logged in', result.error)

    def test_collections_expire_with_a_logout(self):
        collection_module.user_collections.clear()
        result = self.run_command('collection add k1 a1')
        self.assertFalse(result.ok)
        self.assertEqual([], self.session.resolve('k*')[0])
