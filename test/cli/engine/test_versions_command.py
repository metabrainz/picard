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

"""``album versions``, ``album switch`` and the ``v`` handles."""

import io
import json
from unittest.mock import patch

from test.cli.engine.helpers import EngineCommandTestCase

from picard.album import (
    Album,
    NatAlbum,
)
from picard.cli.engine.completion import complete
from picard.cli.engine.render import render_result
from picard.cli.engine.session import classify_entity
from picard.cli.engine.versions import Version
from picard.cli.output import CliOutput
from picard.cluster import Cluster


_RG = 'aaaaaaaa-0000-0000-0000-000000000001'
_CURRENT = '11111111-0000-0000-0000-000000000001'
_OTHER = '22222222-0000-0000-0000-000000000002'
_THIRD = '33333333-0000-0000-0000-000000000003'
_STRANGER = '44444444-0000-0000-0000-000000000004'


def _version(release_id, name, totaltracks=10, countries=(), formats=(), **fields):
    version = {
        'id': release_id,
        'name': name,
        'extra': '',
        'tracks': str(totaltracks),
        'year': '2001',
        'country': 'XE',
        'format': 'CD',
        'label': '',
        'catnum': '',
        'packaging': '',
        'barcode': '',
        'disambiguation': '',
        'totaltracks': totaltracks,
        'countries': list(countries),
        'formats': list(formats),
    }
    version.update(fields)
    return version


class VersionsTestCase(EngineCommandTestCase):
    """An album of ten tracks whose release group has three versions."""

    def setUp(self):
        super().setUp()
        self.set_config_values(
            setting={
                'preferred_release_countries': [],
                'preferred_release_formats': [],
            }
        )
        self.album = Album(_CURRENT)
        self.album.loaded = True
        self.wks.albums[_CURRENT] = self.album
        self.group = self.wks.get_release_group_by_id(_RG)
        self.album.release_group = self.group
        self.group.loaded = True
        self.group.versions = [
            _version(_THIRD, 'C third', totaltracks=12),
            _version(_OTHER, 'B other'),
            _version(_CURRENT, 'A current'),
        ]
        self.album_handle = self.session.handle_for(self.album)

    def versions(self, selector=None):
        result = self.run_command(f'album versions {selector or self.album_handle}')
        self.assertTrue(result.ok, result.error)
        return result


class VersionTest(VersionsTestCase):
    def test_classified_as_v(self):
        self.assertEqual('v', classify_entity(Version(self.group.versions[0], (0, 0, 0))))

    def test_describe(self):
        data = Version(_version(_OTHER, 'B other', barcode='123'), (0, 1, 0), current=True).describe()
        self.assertEqual('release', data['entity_type'])
        self.assertEqual(_OTHER, data['mbid'])
        self.assertEqual('B other', data['title'])
        self.assertEqual('123', data['barcode'])
        self.assertTrue(data['current'])
        self.assertFalse(data['preferred'])
        self.assertNotIn('label', data)  # empty fields are dropped
        json.dumps(data)

    def test_preferred_when_every_group_is_zero(self):
        self.assertTrue(Version(self.group.versions[0], (0, 0, 0)).preferred)
        self.assertFalse(Version(self.group.versions[0], (0, 0, 1)).preferred)


class SessionVersionsTest(VersionsTestCase):
    def test_set_versions_mints_v_handles(self):
        versions = [Version(v, (0, 0, 0)) for v in self.group.versions]
        self.assertEqual(['v1', 'v2', 'v3'], self.session.set_versions(self.album, versions))
        self.assertEqual(versions, self.session.versions_for(self.album))
        self.assertEqual(versions, list(self.session.enumerate_prefix('v')))
        entities, unresolved = self.session.resolve('v2')
        self.assertEqual([versions[1]], entities)
        self.assertEqual([], unresolved)

    def test_a_new_listing_replaces_the_handles(self):
        old = [Version(self.group.versions[0], (0, 0, 0))]
        self.session.set_versions(self.album, old)
        self.session.set_versions(self.album, [Version(self.group.versions[1], (0, 0, 0))])
        del old
        self.assertEqual(['v2'], [self.session.handle_for(v) for v in self.session.versions_for(self.album)])

    def test_versions_of_an_unknown_album_are_empty(self):
        self.assertEqual([], self.session.versions_for(Album('x')))


class VersionPathTest(VersionsTestCase):
    def setUp(self):
        super().setUp()
        self.versions = [Version(v, (0, 0, 0)) for v in self.group.versions]
        self.session.set_versions(self.album, self.versions)

    def test_path_selects_a_version(self):
        for text, expected in (('a1.v1', [0]), ('a1.v3', [2]), ('a1.v*', [0, 1, 2])):
            with self.subTest(text=text):
                entities, unresolved = self.session.resolve(text)
                self.assertEqual([self.versions[i] for i in expected], entities)
                self.assertEqual([], unresolved)

    def test_missing_version_is_unresolved(self):
        entities, unresolved = self.session.resolve('a1.v9')
        self.assertEqual([], entities)
        self.assertEqual(['a1.v9'], unresolved)

    def test_path_of_a_version(self):
        self.assertEqual('a1.v2', self.session.path_of('v2'))

    def test_path_segments_offer_versions(self):
        segments = self.session.path_segments('a1')
        self.assertIn('v*', segments)
        self.assertIn('v3', segments)

    def test_path_segments_without_versions(self):
        self.session.set_versions(self.album, [])
        self.assertNotIn('v*', self.session.path_segments('a1'))

    def test_a_version_has_no_children(self):
        result = self.run_command('ls v1.t1')
        self.assertFalse(result.ok)

    def test_wildcard_lists_versions(self):
        result = self.run_command('ls v*')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(['v1', 'v2', 'v3'], [item.handle for item in result.items])
        self.assertEqual(['a1.v1', 'a1.v2', 'a1.v3'], [item.path for item in result.items])
        self.assertEqual(_THIRD, result.items[0].data['mbid'])

    def test_remove_skips_versions(self):
        result = self.run_command('remove v1')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(['skipped'], [item.status for item in result.items])

    def test_save_rejects_versions(self):
        result = self.run_command('save v1')
        self.assertFalse(result.ok)
        self.assertIn('release version', result.error)


class AlbumVersionsCommandTest(VersionsTestCase):
    def test_lists_the_versions_in_the_order_of_the_menu(self):
        item = self.versions().items[0]
        self.assertEqual('listed', item.status)
        # The version with the track count of the album first, then by name.
        self.assertEqual([_CURRENT, _OTHER, _THIRD], [v['mbid'] for v in item.data['versions']])
        self.assertEqual(['v1', 'v2', 'v3'], [v['handle'] for v in item.data['versions']])

    def test_marks_the_current_version(self):
        versions = self.versions().items[0].data['versions']
        self.assertEqual([True, False, False], [v.get('current') for v in versions])

    def test_preferred_countries_come_first(self):
        self.set_config_values(setting={'preferred_release_countries': ['FR']})
        self.group.versions[1]['countries'] = ['FR']
        versions = self.versions().items[0].data['versions']
        self.assertEqual([_OTHER, _CURRENT, _THIRD], [v['mbid'] for v in versions])

    def test_mints_the_handles(self):
        result = self.versions()
        self.assertEqual(['v1', 'v2', 'v3'], result.mints)
        self.assertEqual(['a1'], result.resolved)

    def test_a_second_listing_replaces_the_handles(self):
        self.versions()
        self.assertEqual(['v4', 'v5', 'v6'], self.versions().mints)
        self.assertEqual([], self.session.resolve('v1')[0])

    def test_result_is_serializable(self):
        json.dumps(self.versions().to_dict())

    def test_the_versions_are_requested_when_not_loaded(self):
        self.group.loaded = False
        self.group.versions = []

        def load_versions(callback):
            self.group.versions = [_version(_CURRENT, 'A current')]
            self.group.loaded = True
            callback()

        with patch.object(self.group, 'load_versions', side_effect=load_versions) as load:
            item = self.versions().items[0]
        load.assert_called_once()
        self.assertEqual([_CURRENT], [v['mbid'] for v in item.data['versions']])

    def test_the_versions_are_not_requested_again(self):
        with patch.object(self.group, 'load_versions') as load:
            self.versions()
        load.assert_not_called()

    def test_failed_request(self):
        self.group.loaded = False

        def load_versions(callback):
            self.group.loaded = True
            self.group.load_error = "Service Unavailable"
            callback()

        with patch.object(self.group, 'load_versions', side_effect=load_versions):
            item = self.versions().items[0]
        self.assertEqual('load_failed', item.status)
        self.assertEqual("Service Unavailable", item.data['error'])
        self.assertEqual([], self.session.versions_for(self.album))

    def test_timeout(self):
        self.group.loaded = False
        self.session._app.run_until_idle.return_value = False
        with patch.object(self.group, 'load_versions'):
            result = self.versions()
        self.assertEqual('timeout', result.items[0].status)
        self.assertIn('timed out', result.message)

    def test_album_not_loaded(self):
        self.album.release_group = None
        self.assertEqual('not_loaded', self.versions().items[0].status)

    def test_standalone_recordings_have_no_versions(self):
        nat = NatAlbum()
        self.wks.albums['NATS'] = nat
        item = self.versions(self.session.handle_for(nat)).items[0]
        self.assertEqual('no_versions', item.status)

    def test_truncated_listing_says_so(self):
        self.group.versions_count = 250
        self.assertEqual(250, self.versions().items[0].data['total'])

    def test_only_albums_are_listed(self):
        cluster = Cluster('cluster')
        self.wks.clusters.append(cluster)
        result = self.run_command(f'album versions {self.session.handle_for(cluster)}')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([], result.items)

    def test_usage(self):
        self.assertFalse(self.run_command('album versions').ok)

    def test_unresolved(self):
        result = self.run_command('album versions a9')
        self.assertTrue(result.ok)
        self.assertEqual(['a9'], result.unresolved)


class AlbumSwitchCommandTest(VersionsTestCase):
    def setUp(self):
        super().setUp()
        self.switch_calls = []

        def switch(mbid):
            # What Album.switch_release_version does when the release is not loaded.
            self.switch_calls.append(mbid)
            del self.wks.albums[self.album.id]
            self.album.id = mbid
            self.wks.albums[mbid] = self.album

        patcher = patch.object(self.album, 'switch_release_version', side_effect=switch)
        patcher.start()
        self.addCleanup(patcher.stop)

    def switch(self, version):
        return self.run_command(f'album switch {self.album_handle} {version}')

    def test_switch_to_a_listed_version(self):
        self.versions()
        result = self.switch('v2')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([_OTHER], self.switch_calls)
        item = result.items[0]
        self.assertEqual('switched', item.status)
        self.assertEqual(self.album_handle, item.handle)
        self.assertEqual(_OTHER, item.data['mbid'])
        self.assertEqual(_CURRENT, item.data['previous'])
        self.assertEqual([], result.mints)

    def test_a_version_alone_says_the_album(self):
        self.versions()
        for text in ('v2', 'a1.v2'):
            with self.subTest(text=text):
                self.switch_calls.clear()
                result = self.run_command(f'album switch {text}')
                self.assertTrue(result.ok, result.error)
                self.assertEqual([_OTHER], self.switch_calls)
                self.assertEqual(self.album_handle, result.items[0].handle)
                self.album.id = _CURRENT
                self.wks.albums.clear()
                self.wks.albums[_CURRENT] = self.album

    def test_a_single_word_that_is_not_a_listed_version_is_a_usage_error(self):
        self.versions()
        for text in ('a1', 'v9'):
            with self.subTest(text=text):
                result = self.run_command(f'album switch {text}')
                self.assertFalse(result.ok)
                self.assertIn('usage', result.error)
        # An MBID does not say which album it is for.
        self.assertFalse(self.run_command(f'album switch {_OTHER}').ok)
        self.assertEqual([], self.switch_calls)

    def test_switch_by_path(self):
        self.versions()
        self.assertTrue(self.switch('a1.v3').ok)
        self.assertEqual([_THIRD], self.switch_calls)

    def test_switch_by_release_reference(self):
        for text in (_OTHER, f'release:{_OTHER}', f'https://musicbrainz.org/release/{_OTHER}'):
            with self.subTest(text=text):
                self.switch_calls.clear()
                self.album.id = _CURRENT
                self.wks.albums.clear()
                self.wks.albums[_CURRENT] = self.album
                result = self.switch(text)
                self.assertTrue(result.ok, result.error)
                self.assertEqual([_OTHER], self.switch_calls)

    def test_the_current_marker_follows(self):
        self.versions()
        self.switch('v2')
        self.assertEqual(
            [False, True, False],
            [v.current for v in self.session.versions_for(self.album)],
        )

    def test_switch_to_the_current_release_does_nothing(self):
        result = self.switch(_CURRENT)
        self.assertTrue(result.ok, result.error)
        self.assertEqual('unchanged', result.items[0].status)
        self.assertEqual([], self.switch_calls)

    def test_a_release_of_another_group_is_refused(self):
        result = self.switch(_STRANGER)
        self.assertFalse(result.ok)
        self.assertIn('not a version', result.error)
        self.assertEqual([], self.switch_calls)

    def test_not_a_release(self):
        result = self.switch(f'https://musicbrainz.org/artist/{_OTHER}')
        self.assertFalse(result.ok)
        self.assertIn('is a artist, not a release', result.error)

    def test_a_version_of_another_album_is_refused(self):
        other = Album(_STRANGER)
        other.release_group = self.group
        other.loaded = True
        self.wks.albums[_STRANGER] = other
        self.session.set_versions(other, [Version(self.group.versions[1], (0, 0, 0))])
        version_handle = self.session.handle_for(self.session.versions_for(other)[0])
        result = self.switch(version_handle)
        self.assertFalse(result.ok)
        self.assertIn('is not a version listed for', result.error)
        self.assertEqual([], self.switch_calls)

    def test_not_a_version(self):
        for text in ('a1', 'f*', 'v9', '??'):
            with self.subTest(text=text):
                self.assertFalse(self.switch(text).ok)
        self.assertEqual([], self.switch_calls)

    def test_needs_one_album(self):
        self.wks.albums[_STRANGER] = Album(_STRANGER)
        result = self.run_command(f'album switch a* {_OTHER}')
        self.assertFalse(result.ok)
        self.assertIn('exactly one album', result.error)

    def test_unknown_album(self):
        result = self.run_command(f'album switch a9 {_OTHER}')
        self.assertFalse(result.ok)
        self.assertEqual(['a9'], result.unresolved)

    def test_usage(self):
        self.assertFalse(self.run_command('album switch').ok)
        self.assertFalse(self.run_command(f'album switch {self.album_handle}').ok)

    def test_album_still_loading(self):
        with patch.object(self.album, 'has_critical_tasks', return_value=True):
            result = self.switch(_OTHER)
        self.assertFalse(result.ok)
        self.assertIn('still loading', result.error)

    def test_album_not_loaded(self):
        self.album.release_group = None
        result = self.switch(_OTHER)
        self.assertFalse(result.ok)
        self.assertIn('not a loaded release', result.error)

    def test_failed_versions_request(self):
        self.group.loaded = False

        def load_versions(callback):
            self.group.loaded = True
            self.group.load_error = "Service Unavailable"
            callback()

        with patch.object(self.group, 'load_versions', side_effect=load_versions):
            result = self.switch(_OTHER)
        self.assertFalse(result.ok)
        self.assertIn('Service Unavailable', result.error)
        self.assertEqual([], self.switch_calls)

    def test_load_error_is_reported(self):
        def switch(mbid):
            del self.wks.albums[self.album.id]
            self.album.id = mbid
            self.wks.albums[mbid] = self.album
            self.album.errors.append("Service Unavailable")

        self.album.switch_release_version.side_effect = switch
        item = self.switch(_OTHER).items[0]
        self.assertEqual('load_failed', item.status)
        self.assertEqual("Service Unavailable", item.data['error'])

    def test_not_loaded_in_time(self):
        def switch(mbid):
            del self.wks.albums[self.album.id]
            self.album.id = mbid
            self.wks.albums[mbid] = self.album
            self.album.loaded = False

        self.album.switch_release_version.side_effect = switch
        self.session._app.run_until_idle.return_value = False
        result = self.switch(_OTHER)
        self.assertEqual('timeout', result.items[0].status)
        self.assertIn('timed out', result.message)

    def test_release_already_loaded_gets_the_files(self):
        merged = Album(_OTHER)
        merged.loaded = True
        self.wks.albums[_OTHER] = merged

        def switch(mbid):
            # What the core does when the release is in the working set: the
            # files go there and this album is removed.
            del self.wks.albums[self.album.id]

        self.album.switch_release_version.side_effect = switch
        result = self.switch(_OTHER)
        self.assertTrue(result.ok, result.error)
        item = result.items[0]
        self.assertEqual('switched', item.status)
        self.assertEqual(self.session.handle_for(merged), item.handle)
        self.assertEqual([item.handle], result.mints)
        self.assertNotEqual(self.album_handle, item.handle)


class VersionsRenderAndCompletionTest(VersionsTestCase):
    def test_render_lists_the_versions(self):
        buf = io.StringIO()
        render_result(self.versions(), CliOutput(stdout=buf, stderr=buf, color=False))
        text = buf.getvalue()
        self.assertIn(f"* v1  release:{_CURRENT}  A current", text)
        self.assertIn(f"  v2  release:{_OTHER}  B other", text)

    def test_render_says_when_the_list_is_cut(self):
        self.group.versions_count = 250
        buf = io.StringIO()
        render_result(self.versions(), CliOutput(stdout=buf, stderr=buf, color=False))
        self.assertIn("250 releases in the group", buf.getvalue())

    def test_completion_offers_versions(self):
        self.versions()
        self.assertIn('v1', complete('album switch a1 v', 'v', self.reg, self.session))
        self.assertIn('v*', complete('ls v', 'v', self.reg, self.session))
        self.assertIn('a1.v2', complete('ls a1.v', 'a1.v', self.reg, self.session))
