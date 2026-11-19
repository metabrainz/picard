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

"""`move <sources> <destination>`: put files into a track, cluster, album or bucket."""

from unittest.mock import (
    MagicMock,
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase
from test.cli.engine.test_navigation import (
    _file,
    _track,
)

from picard.album import (
    Album,
    NatAlbum,
)
from picard.cli.engine.candidates import Candidate
from picard.cli.engine.dispatch import dispatch
from picard.cluster import Cluster


class _MoveTestBase(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'va_name': 'Various Artists', 'nat_name': 'Standalone Recordings'})

        # A two-disc album, a cluster holding two files, a loose file.
        self.album = Album('rel-1')
        self.album.loaded = True
        self.wks.albums['rel-1'] = self.album
        for disc, number, title in ((1, 1, 'A1'), (1, 2, 'A2'), (2, 1, 'B1')):
            _track(self.album, disc, number, title)
        self.cluster = Cluster('Cluster', 'Artist')
        self.wks.clusters.append(self.cluster)
        self.first = _file(self.wks, 'first.flac')
        self.second = _file(self.wks, 'second.flac')
        self.cluster.add_file(self.first)
        self.cluster.add_file(self.second)
        self.loose = _file(self.wks, 'loose.flac')
        self.wks.unclustered_files.add_file(self.loose)
        # Hand out the handles in a known order: c1, a1, f1 (first), f2, f3.
        for entity in (self.cluster, self.album, self.first, self.second, self.loose):
            self.session.handle_for(entity)

    def _move(self, line):
        return dispatch(self.session, self.reg, line)


class MoveToTrackTest(_MoveTestBase):
    def test_file_to_a_track(self):
        result = self._move('move f1 a1.d2.t1')
        self.assertTrue(result.ok, result.error)
        self.assertIs(self.album.tracks[2], self.first.parent_item)
        (item,) = result.items
        self.assertEqual(('f1', 'moved'), (item.handle, item.status))
        self.assertEqual('c1.f1', item.data['from'])
        self.assertEqual('a1.d2.t1.f1', item.path)

    def test_several_files_go_to_the_following_tracks_as_in_the_gui(self):
        result = self._move('move f1 f2 a1.d1.t2')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(
            [self.album.tracks[1], self.album.tracks[2]], [self.first.parent_item, self.second.parent_item]
        )
        self.assertEqual(['moved', 'moved'], [it.status for it in result.items])

    def test_files_beyond_the_last_track_go_to_the_unmatched_files(self):
        result = self._move('move f1 f2 f3 a1.d2.t1')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(
            [self.album.tracks[2], self.album.unmatched_files, self.album.unmatched_files],
            [self.first.parent_item, self.second.parent_item, self.loose.parent_item],
        )

    def test_track_without_a_disc_on_a_multi_disc_release_is_an_error(self):
        result = self._move('move f1 a1.t1')
        self.assertFalse(result.ok)
        self.assertIn('invalid selector', result.error)
        self.assertIs(self.cluster, self.first.parent_item)


class MoveToClusterAndBucketTest(_MoveTestBase):
    def test_file_to_a_cluster(self):
        result = self._move('move f3 c1')
        self.assertTrue(result.ok, result.error)
        self.assertIs(self.cluster, self.loose.parent_item)
        self.assertEqual('c1.f3', result.items[0].path)

    def test_file_to_the_unclustered_bucket(self):
        result = self._move('move f1 u')
        self.assertTrue(result.ok, result.error)
        self.assertIs(self.wks.unclustered_files, self.first.parent_item)

    def test_file_to_the_unmatched_files_of_an_album(self):
        result = self._move('move f3 a1.u')
        self.assertTrue(result.ok, result.error)
        self.assertIs(self.album.unmatched_files, self.loose.parent_item)
        self.assertEqual('a1.u.f1', result.items[0].path)

    def test_the_sources_may_be_containers(self):
        result = self._move('move c1 a1.u')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([self.album.unmatched_files] * 2, [self.first.parent_item, self.second.parent_item])

    def test_sources_may_be_paths(self):
        result = self._move('move c1.f2 u')
        self.assertTrue(result.ok, result.error)
        self.assertIs(self.wks.unclustered_files, self.second.parent_item)
        self.assertIs(self.cluster, self.first.parent_item)


class MoveToAlbumTest(_MoveTestBase):
    def test_files_are_matched_to_the_album_as_in_the_gui(self):
        with patch.object(self.wks, 'move_files_to_album') as match:
            result = self._move('move f1 f2 a1')
        self.assertTrue(result.ok, result.error)
        match.assert_called_once_with([self.first, self.second], album=self.album)

    def test_non_album_tracks_are_not_a_destination(self):
        nats = NatAlbum()
        self.wks.albums['NATS'] = nats
        handle = self.session.handle_for(nats)
        with patch.object(self.wks, 'move_files_to_album') as match:
            result = self._move(f'move f1 {handle}')
        self.assertFalse(result.ok)
        self.assertIn('non-album', result.error)
        match.assert_not_called()


class MoveSourcesAndSyntaxTest(_MoveTestBase):
    def test_union_of_sources_in_all_spellings(self):
        for number, template in enumerate(('move {a} {b} u', 'move {a}, {b} u', 'move {a},{b} u')):
            with self.subTest(template=template):
                # Fresh files each time: emptying a cluster removes it.
                cluster = Cluster('Another', 'Artist')
                self.wks.clusters.append(cluster)
                files = [_file(self.wks, f'{number}-{name}.flac') for name in 'ab']
                for file in files:
                    cluster.add_file(file)
                a, b = (self.session.handle_for(file) for file in files)
                result = self._move(template.format(a=a, b=b))
                self.assertTrue(result.ok, result.error)
                self.assertEqual(['moved', 'moved'], [it.status for it in result.items])
                self.assertEqual([self.wks.unclustered_files] * 2, [file.parent_item for file in files])

    def test_emptying_a_cluster_removes_it_as_in_the_gui(self):
        result = self._move('move c1 u')
        self.assertTrue(result.ok, result.error)
        self.assertNotIn(self.cluster, self.wks.clusters)

    def test_file_already_there_is_unchanged(self):
        result = self._move('move f1 c1')
        self.assertTrue(result.ok, result.error)
        self.assertEqual('unchanged', result.items[0].status)
        self.assertIs(self.cluster, self.first.parent_item)

    def test_only_the_files_that_need_to_move_are_moved(self):
        result = self._move('move f1 f3 c1')
        self.assertEqual({'f1': 'unchanged', 'f3': 'moved'}, {it.handle: it.status for it in result.items})

    def test_unresolved_source_is_reported_and_the_rest_moved(self):
        result = self._move('move f1 f99 u')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(['f99'], result.unresolved)
        self.assertIs(self.wks.unclustered_files, self.first.parent_item)

    def test_nothing_to_move_is_ok(self):
        result = self._move('move f99 u')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([], result.items)
        self.assertEqual(['f99'], result.unresolved)


class MoveErrorsTest(_MoveTestBase):
    def test_usage(self):
        for line in ('move', 'move f1'):
            with self.subTest(line=line):
                result = self._move(line)
                self.assertFalse(result.ok)
                self.assertIn('usage', result.error)

    def test_destination_that_matches_nothing(self):
        result = self._move('move f1 c9')
        self.assertFalse(result.ok)
        self.assertIn('matches nothing', result.error)
        self.assertIs(self.cluster, self.first.parent_item)

    def test_destination_must_be_one_place(self):
        other = Cluster('Other', 'Artist')
        self.wks.clusters.append(other)
        result = self._move('move f3 c*')
        self.assertFalse(result.ok)
        self.assertIn('name one', result.error)
        self.assertIs(self.wks.unclustered_files, self.loose.parent_item)

    def test_a_disc_is_not_a_destination(self):
        result = self._move('move f1 a1.d2')
        self.assertFalse(result.ok)
        self.assertIn('not a place', result.error)
        self.assertIs(self.cluster, self.first.parent_item)

    def test_a_file_is_not_a_destination(self):
        result = self._move('move f1 f3')
        self.assertFalse(result.ok)
        self.assertIn('not a place', result.error)

    def test_candidates_hold_no_files(self):
        (handle,) = self.session.set_candidates(self.cluster, [Candidate(MagicMock())])
        result = self._move(f'move {handle} u')
        self.assertFalse(result.ok)
        self.assertIn('candidate', result.error)

    def test_save_and_trash_refuse_candidates_too(self):
        (handle,) = self.session.set_candidates(self.cluster, [Candidate(MagicMock())])
        for command in ('save', 'trash'):
            with self.subTest(command=command):
                result = self._move(f'{command} {handle}')
                self.assertFalse(result.ok)
                self.assertIn('lookup candidate', result.error)
                self.assertNotIn('iterfiles', result.error)
                self.assertTrue(result.error.startswith(f'{command}:'))
        self.assertIs(self.cluster, self.first.parent_item)

    def test_destination_is_a_single_term(self):
        result = self._move('move f1 c1,a1')
        self.assertFalse(result.ok)
        self.assertIn('invalid selector', result.error)
