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

"""Selector paths (``a1.d2.t3``, ``c1.f*``, ``u.f*``) over real working-set entities."""

from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.album import Album
from picard.cli.engine.builtins import register_builtins
from picard.cli.engine.candidates import Candidate
from picard.cli.engine.commands import EngineCommandRegistry
from picard.cli.engine.dispatch import dispatch
from picard.cli.engine.selectors import SelectorError
from picard.cli.engine.session import LocalEngineSession
from picard.cluster import Cluster
from picard.file import File
from picard.track import Track
from picard.workspace import workspace


def _track(album, disc, number, title):
    track = Track(f'trk-{title}', album)
    if disc is not None:
        track.metadata['discnumber'] = str(disc)
    if number is not None:
        track.metadata['tracknumber'] = str(number)
    track.metadata['title'] = title
    album.tracks.append(track)
    return track


def _file(wks, name):
    file = File(name)
    wks.files[file.filename] = file
    return file


class _PathTestBase(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        # Moving a file into a container reaches these services.
        self.tagger.acoustid_manager = MagicMock()
        self.tagger.isrc_submit_manager = MagicMock()
        self.tagger.acoustid_client = MagicMock()
        self.session = LocalEngineSession(MagicMock())
        self.wks = workspace()

    def _album(self, key, tracks, loaded=True):
        """Register an album whose tracks are ``(disc, number, title)`` tuples."""
        album = Album(key)
        album.loaded = loaded
        self.wks.albums[key] = album
        for disc, number, title in tracks:
            _track(album, disc, number, title)
        self.session.handle_for(album)
        return album

    def _resolve(self, selector):
        return self.session.resolve(selector)

    def _titles(self, selector):
        entities, unresolved = self._resolve(selector)
        return [e.metadata['title'] for e in entities], unresolved


class SingleDiscAlbumPathTest(_PathTestBase):
    def setUp(self):
        super().setUp()
        self.album = self._album('rel-1', [(1, 1, 'One'), (1, 2, 'Two'), (1, 3, 'Three')])

    def test_track_without_disc(self):
        self.assertEqual((['Two'], []), self._titles('a1.t2'))

    def test_explicit_disc_is_the_same_track(self):
        self.assertEqual(self._titles('a1.t2'), self._titles('a1.d1.t2'))

    def test_all_tracks(self):
        self.assertEqual((['One', 'Two', 'Three'], []), self._titles('a1.t*'))

    def test_disc_stands_for_its_tracks(self):
        self.assertEqual((['One', 'Two', 'Three'], []), self._titles('a1.d1'))

    def test_wildcard_discs_then_track(self):
        self.assertEqual((['One'], []), self._titles('a1.d*.t1'))

    def test_missing_track_is_unresolved(self):
        self.assertEqual(([], ['a1.t9']), self._titles('a1.t9'))

    def test_missing_disc_is_unresolved(self):
        self.assertEqual(([], ['a1.d2']), self._titles('a1.d2'))

    def test_missing_album_is_unresolved(self):
        self.assertEqual(([], ['a9.t1']), self._titles('a9.t1'))

    def test_resolved_tracks_are_handleable(self):
        entities, _ = self._resolve('a1.d1')
        handles = [self.session.handle_for(e) for e in entities]
        self.assertTrue(all(h.startswith('t') for h in handles))
        # Stable identity: the same track resolves to the same handle by path.
        (again,), _ = self._resolve('a1.t2')
        self.assertEqual(handles[1], self.session.handle_for(again))

    def test_pregap_is_track_zero(self):
        _track(self.album, 1, 0, 'Pregap')
        self.assertEqual((['Pregap'], []), self._titles('a1.t0'))


class MultiDiscAlbumPathTest(_PathTestBase):
    def setUp(self):
        super().setUp()
        self.album = self._album(
            'rel-1',
            [(1, 1, 'A1'), (1, 2, 'A2'), (2, 1, 'B1'), (2, 2, 'B2')],
        )

    def test_track_needs_a_disc(self):
        with self.assertRaises(SelectorError) as ctx:
            self._resolve('a1.t1')
        message = str(ctx.exception)
        self.assertIn('a1.t1', message)
        self.assertIn('2 discs', message)
        self.assertIn('d1.t1', message)

    def test_explicit_disc(self):
        self.assertEqual((['B1'], []), self._titles('a1.d2.t1'))
        self.assertEqual((['A2'], []), self._titles('a1.d1.t2'))

    def test_disc_stands_for_its_tracks(self):
        self.assertEqual((['B1', 'B2'], []), self._titles('a1.d2'))

    def test_all_discs(self):
        self.assertEqual((['A1', 'A2', 'B1', 'B2'], []), self._titles('a1.d*'))

    def test_all_tracks_need_no_disc(self):
        self.assertEqual((['A1', 'A2', 'B1', 'B2'], []), self._titles('a1.t*'))

    def test_track_of_every_disc(self):
        self.assertEqual((['A1', 'B1'], []), self._titles('a1.d*.t1'))

    def test_missing_track_on_disc_is_unresolved(self):
        self.assertEqual(([], ['a1.d2.t5']), self._titles('a1.d2.t5'))

    def test_disc_numbers_come_from_the_tags_not_the_position(self):
        # A release whose only disc is numbered 2 is still addressed as disc 2.
        self._album('rel-2', [(2, 1, 'Only')])
        self.assertEqual((['Only'], []), self._titles('a2.d2.t1'))
        self.assertEqual((['Only'], []), self._titles('a2.t1'))


class UnnumberedAlbumPathTest(_PathTestBase):
    """Non-album tracks carry no disc or track numbers: positions, and no discs."""

    def setUp(self):
        super().setUp()
        self.album = self._album('NATS', [(None, None, 'X'), (None, None, 'Y')])

    def test_tracks_are_numbered_by_position(self):
        self.assertEqual((['Y'], []), self._titles('a1.t2'))
        self.assertEqual((['X', 'Y'], []), self._titles('a1.t*'))

    def test_discs_are_not_available(self):
        with self.assertRaises(SelectorError) as ctx:
            self._resolve('a1.d1')
        self.assertIn('no disc numbers', str(ctx.exception))

    def test_position_follows_removals(self):
        self.album.tracks.remove(self.album.tracks[0])
        self.assertEqual((['Y'], []), self._titles('a1.t1'))


class AlbumStatePathTest(_PathTestBase):
    def test_tracks_of_an_unloaded_album_are_an_error(self):
        self._album('rel-1', [(1, 1, 'One')], loaded=False)
        with self.assertRaises(SelectorError) as ctx:
            self._resolve('a1.t1')
        self.assertIn('not loaded', str(ctx.exception))

    def test_loaded_album_without_tracks_is_empty(self):
        self._album('rel-1', [])
        self.assertEqual(([], []), self._titles('a1.t*'))
        self.assertEqual(([], ['a1.t1']), self._titles('a1.t1'))


class FilePathTest(_PathTestBase):
    def setUp(self):
        super().setUp()
        self.album = self._album('rel-1', [(1, 1, 'One'), (1, 2, 'Two')])
        self.on_one = _file(self.wks, 'one.flac')
        self.on_one_too = _file(self.wks, 'one-alt.flac')
        self.on_two = _file(self.wks, 'two.flac')
        self.loose_in_album = _file(self.wks, 'loose.flac')
        self.album.tracks[0].files.extend([self.on_one, self.on_one_too])
        self.album.tracks[1].files.append(self.on_two)
        self.album.unmatched_files.add_file(self.loose_in_album)

    def test_files_of_a_track(self):
        entities, _ = self._resolve('a1.t1.f*')
        self.assertEqual([self.on_one, self.on_one_too], entities)

    def test_file_of_a_track_by_position(self):
        entities, _ = self._resolve('a1.t1.f2')
        self.assertEqual([self.on_one_too], entities)

    def test_missing_file_of_a_track_is_unresolved(self):
        self.assertEqual(([], ['a1.t2.f2']), self._resolve('a1.t2.f2'))

    def test_every_file_of_an_album(self):
        entities, _ = self._resolve('a1.f*')
        self.assertEqual([self.on_one, self.on_one_too, self.on_two, self.loose_in_album], entities)

    def test_files_of_a_disc_view(self):
        entities, _ = self._resolve('a1.d1.f*')
        self.assertEqual([self.on_one, self.on_one_too, self.on_two], entities)

    def test_unmatched_files_of_an_album(self):
        entities, _ = self._resolve('a1.u')
        self.assertEqual([self.loose_in_album], entities)
        self.assertEqual(entities, self._resolve('a1.u.f*')[0])

    def test_path_through_disc_to_file(self):
        entities, _ = self._resolve('a1.d1.t2.f1')
        self.assertEqual([self.on_two], entities)


class ClusterAndBucketPathTest(_PathTestBase):
    def setUp(self):
        super().setUp()
        self.cluster = Cluster('Album', 'Artist')
        self.wks.clusters.append(self.cluster)
        self.session.handle_for(self.cluster)
        self.first = _file(self.wks, 'first.flac')
        self.second = _file(self.wks, 'second.flac')
        self.cluster.add_file(self.first)
        self.cluster.add_file(self.second)
        self.loose = _file(self.wks, 'loose.flac')
        self.wks.unclustered_files.add_file(self.loose)

    def test_files_of_a_cluster(self):
        entities, _ = self._resolve('c1.f*')
        self.assertCountEqual([self.first, self.second], entities)

    def test_file_of_a_cluster_by_position(self):
        entities, _ = self._resolve('c1.f1')
        self.assertEqual(list(self.cluster.files)[:1], entities)

    def test_unclustered_bucket_stands_for_its_files(self):
        self.assertEqual(([self.loose], []), self._resolve('u'))
        self.assertEqual(([self.loose], []), self._resolve('u.f*'))
        self.assertEqual(([self.loose], []), self._resolve('u.f1'))

    def test_universal_cluster_wildcard(self):
        entities, _ = self._resolve('c*.f1')
        self.assertEqual(list(self.cluster.files)[:1], entities)


class CandidatePathTest(_PathTestBase):
    def setUp(self):
        super().setUp()
        self.cluster = Cluster('Album', 'Artist')
        self.other = Cluster('Other', 'Artist')
        self.wks.clusters.extend([self.cluster, self.other])
        for cluster in (self.cluster, self.other):
            self.session.handle_for(cluster)
        self.candidates = [Candidate(MagicMock()) for _ in range(3)]
        self.session.set_candidates(self.cluster, self.candidates)
        self.session.set_candidates(self.other, [Candidate(MagicMock())])

    def test_candidates_of_a_cluster(self):
        self.assertEqual((self.candidates, []), self._resolve('c1.m*'))

    def test_candidate_by_position_is_per_cluster(self):
        self.assertEqual(([self.candidates[1]], []), self._resolve('c1.m2'))
        self.assertEqual(([], ['c2.m2']), self._resolve('c2.m2'))

    def test_candidates_of_a_file(self):
        file = _file(self.wks, 'one.flac')
        self.session.handle_for(file)
        candidate = Candidate(MagicMock())
        self.session.set_candidates(file, [candidate])
        self.assertEqual(([candidate], []), self._resolve('f1.m1'))


class InvalidPathTest(_PathTestBase):
    def setUp(self):
        super().setUp()
        self.album = self._album('rel-1', [(1, 1, 'One')])
        self.file = _file(self.wks, 'one.flac')
        self.session.handle_for(self.file)
        self.cluster = Cluster('Album', 'Artist')
        self.wks.clusters.append(self.cluster)
        self.session.handle_for(self.cluster)

    def test_segments_not_valid_under_their_parent(self):
        for selector in ('f1.t1', 'a1.m1', 'c1.t1', 'a1.t1.t1', 'a1.d1.d1', 'c1.u', 'a1.c1', 'u.m1'):
            with self.subTest(selector=selector):
                with self.assertRaises(SelectorError):
                    self._resolve(selector)

    def test_candidate_has_no_children(self):
        candidate = Candidate(MagicMock())
        self.session.set_candidates(self.cluster, [candidate])
        with self.assertRaises(SelectorError):
            self._resolve('c1.m1.f1')

    def test_a_bucket_cannot_hold_candidates(self):
        with self.assertRaises(SelectorError):
            self._resolve('a1.u.m1')


class PathResultTest(_PathTestBase):
    def test_results_are_deduplicated_across_terms(self):
        self._album('rel-1', [(1, 1, 'One'), (1, 2, 'Two')])
        self.assertEqual((['One', 'Two'], []), self._titles('a1.d1,a1.t*,a1.t1'))

    def test_paths_mix_with_plain_handles(self):
        self._album('rel-1', [(1, 1, 'One')])
        entities, unresolved = self._resolve('a1,a1.t1,a9.t1')
        self.assertEqual(2, len(entities))
        self.assertEqual(['a9.t1'], unresolved)


class PathOfTest(_PathTestBase):
    """The path an entity currently has, which must resolve back to it."""

    def setUp(self):
        super().setUp()
        self.single = self._album('rel-1', [(1, 1, 'One'), (1, 2, 'Two')])
        self.multi = self._album('rel-2', [(1, 1, 'A1'), (2, 1, 'B1'), (2, 2, 'B2')])
        self.nat = self._album('NATS', [(None, None, 'X'), (None, None, 'Y')])
        self.on_track = _file(self.wks, 'on-track.flac')
        self.on_track.move(self.multi.tracks[2])
        self.unmatched = _file(self.wks, 'unmatched.flac')
        self.single.unmatched_files.add_file(self.unmatched)
        self.cluster = Cluster('Album', 'Artist')
        self.wks.clusters.append(self.cluster)
        self.session.handle_for(self.cluster)
        self.clustered = _file(self.wks, 'clustered.flac')
        self.cluster.add_file(self.clustered)
        self.loose = _file(self.wks, 'loose.flac')
        self.wks.unclustered_files.add_file(self.loose)
        self.candidate = Candidate(MagicMock())
        self.session.set_candidates(self.cluster, [Candidate(MagicMock()), self.candidate])

    def _path(self, entity):
        return self.session.path_of(self.session.handle_for(entity))

    def test_track_of_a_single_disc_release_needs_no_disc(self):
        self.assertEqual('a1.t2', self._path(self.single.tracks[1]))

    def test_track_of_a_multi_disc_release_names_its_disc(self):
        self.assertEqual('a2.d2.t2', self._path(self.multi.tracks[2]))

    def test_unnumbered_track_uses_its_position(self):
        self.assertEqual('a3.t2', self._path(self.nat.tracks[1]))

    def test_file_matched_to_a_track(self):
        self.assertEqual('a2.d2.t2.f1', self._path(self.on_track))

    def test_unmatched_file_of_an_album(self):
        self.assertEqual('a1.u.f1', self._path(self.unmatched))

    def test_file_of_a_cluster(self):
        self.assertEqual('c1.f1', self._path(self.clustered))

    def test_unclustered_file(self):
        self.assertEqual('u.f1', self._path(self.loose))

    def test_candidate_of_a_cluster(self):
        self.assertEqual('c1.m2', self._path(self.candidate))

    def test_albums_and_clusters_are_reached_by_handle(self):
        self.assertIsNone(self._path(self.single))
        self.assertIsNone(self._path(self.cluster))

    def test_file_without_a_parent_has_no_path(self):
        self.assertIsNone(self._path(_file(self.wks, 'orphan.flac')))

    def test_unknown_handle_has_no_path(self):
        self.assertIsNone(self.session.path_of('f99'))
        self.assertIsNone(self.session.path_of('not a handle'))

    def test_every_path_resolves_back_to_its_entity(self):
        entities = [
            *self.single.tracks,
            *self.multi.tracks,
            *self.nat.tracks,
            self.on_track,
            self.unmatched,
            self.clustered,
            self.loose,
            self.candidate,
        ]
        for entity in entities:
            path = self._path(entity)
            with self.subTest(path=path):
                self.assertIsNotNone(path)
                self.assertEqual(([entity], []), self._resolve(path))

    def test_path_follows_the_entity_when_it_moves(self):
        handle = self.session.handle_for(self.loose)
        self.assertEqual('u.f1', self.session.path_of(handle))
        self.loose.move(self.cluster)
        self.assertEqual('c1.f2', self.session.path_of(handle))


class ResultPathTest(_PathTestBase):
    """Items of a command result say where their entity currently is."""

    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'va_name': 'Various Artists', 'nat_name': 'Standalone Recordings'})
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.album = self._album('rel-1', [(1, 1, 'One'), (1, 2, 'Two')])
        self.matched = _file(self.wks, 'matched.flac')
        self.matched.move(self.album.tracks[1])

    def test_items_carry_their_path(self):
        result = dispatch(self.session, self.reg, 'tree a1')
        paths = {item.status: item.path for item in result.items if item.status != 'track'}
        self.assertEqual({'album': '', 'file': 'a1.t2.f1'}, paths)
        self.assertEqual(['a1.t1', 'a1.t2'], [item.path for item in result.items if item.status == 'track'])

    def test_path_is_part_of_the_serialized_item(self):
        result = dispatch(self.session, self.reg, 'ls a1.t2')
        self.assertEqual('a1.t2', result.to_dict()['items'][0]['path'])

    def test_a_failing_path_lookup_does_not_fail_the_command(self):
        def broken(handle):
            raise RuntimeError('boom')

        self.session.path_of = broken
        result = dispatch(self.session, self.reg, 'ls a1.t2')
        self.assertTrue(result.ok)
        self.assertEqual([''], [item.path for item in result.items])


class SegmentsTest(_PathTestBase):
    """What can follow a path: the basis of tab completion."""

    def _segments(self, base):
        return self.session.path_segments(base)

    def test_single_disc_album(self):
        self._album('rel-1', [(1, 1, 'One'), (1, 2, 'Two')])
        self.assertEqual(['f*', 'u', 'd*', 'd1', 't*', 't1', 't2'], self._segments('a1'))

    def test_multi_disc_album_offers_discs_not_bare_tracks(self):
        self._album('rel-1', [(1, 1, 'A1'), (2, 1, 'B1'), (2, 2, 'B2')])
        self.assertEqual(['f*', 'u', 'd*', 'd1', 'd2', 't*'], self._segments('a1'))

    def test_unnumbered_album_offers_positions(self):
        self._album('NATS', [(None, None, 'X'), (None, None, 'Y')])
        self.assertEqual(['f*', 'u', 't*', 't1', 't2'], self._segments('a1'))

    def test_album_without_tracks(self):
        self._album('rel-1', [], loaded=False)
        self.assertEqual(['f*', 'u'], self._segments('a1'))

    def test_disc_offers_the_numbers_of_its_tracks(self):
        self._album('rel-1', [(1, 1, 'A1'), (2, 1, 'B1'), (2, 2, 'B2')])
        self.assertEqual(['t*', 'f*', 't1', 't2'], self._segments('a1.d2'))

    def test_track_offers_its_files(self):
        album = self._album('rel-1', [(1, 1, 'One')])
        album.tracks[0].files.extend([_file(self.wks, 'a.flac'), _file(self.wks, 'b.flac')])
        self.assertEqual(['f*', 'f1', 'f2'], self._segments('a1.t1'))

    def test_cluster_offers_files_and_candidates(self):
        cluster = Cluster('Album', 'Artist')
        self.wks.clusters.append(cluster)
        self.session.handle_for(cluster)
        self.assertEqual(['f*'], self._segments('c1'))
        self.session.set_candidates(cluster, [Candidate(MagicMock()), Candidate(MagicMock())])
        self.assertEqual(['f*', 'm*', 'm1', 'm2'], self._segments('c1'))

    def test_unclustered_bucket_offers_its_files(self):
        self.wks.unclustered_files.add_file(_file(self.wks, 'loose.flac'))
        self.assertEqual(['f*', 'f1'], self._segments('u'))

    def test_file_offers_its_candidates(self):
        file = _file(self.wks, 'one.flac')
        self.session.handle_for(file)
        self.assertEqual([], self._segments('f1'))
        self.session.set_candidates(file, [Candidate(MagicMock())])
        self.assertEqual(['m*', 'm1'], self._segments('f1'))

    def test_numbered_segments_are_capped(self):
        album = self._album('rel-1', [(1, 1, 'One')])
        album.tracks[0].files.extend(_file(self.wks, f'{n}.flac') for n in range(150))
        segments = self._segments('a1.t1')
        self.assertEqual(1 + 100, len(segments))
        self.assertEqual('f100', segments[-1])

    def test_wildcard_base_merges_its_matches(self):
        self._album('rel-1', [(1, 1, 'One')])
        self._album('rel-2', [(1, 1, 'A1'), (2, 1, 'B1')])
        segments = self._segments('a*')
        self.assertEqual(len(segments), len(set(segments)))
        self.assertIn('d2', segments)

    def test_nothing_follows_an_unknown_or_invalid_base(self):
        self.assertEqual([], self._segments('a9'))
        self.assertEqual([], self._segments('a1.k1'))
        self.assertEqual([], self._segments('a1,c1'))
        self.assertEqual([], self._segments('!'))


class ResolveTargetsTest(_PathTestBase):
    """resolve_targets() names a place; resolve() would expand it into its contents."""

    def setUp(self):
        super().setUp()
        self.album = self._album('rel-1', [(1, 1, 'A1'), (2, 1, 'B1')])
        self.loose = _file(self.wks, 'loose.flac')
        self.wks.unclustered_files.add_file(self.loose)
        self.cluster = Cluster('Album', 'Artist')
        self.wks.clusters.append(self.cluster)
        self.session.handle_for(self.cluster)

    def test_bucket_is_the_bucket_not_its_files(self):
        self.assertEqual([self.wks.unclustered_files], self.session.resolve_targets('u'))
        self.assertEqual(([self.loose], []), self._resolve('u'))

    def test_album_bucket(self):
        self.assertEqual([self.album.unmatched_files], self.session.resolve_targets('a1.u'))

    def test_disc_is_a_disc_not_its_tracks(self):
        (disc,) = self.session.resolve_targets('a1.d2')
        self.assertEqual(2, disc.number)
        self.assertEqual([self.album.tracks[1]], disc.tracks)

    def test_plain_handles_and_tracks(self):
        self.assertEqual([self.cluster], self.session.resolve_targets('c1'))
        self.assertEqual([self.album.tracks[1]], self.session.resolve_targets('a1.d2.t1'))

    def test_nothing_matches(self):
        self.assertEqual([], self.session.resolve_targets('c9'))
        self.assertEqual([], self.session.resolve_targets('a1.d3.t1'))

    def test_only_one_term_is_accepted(self):
        with self.assertRaises(SelectorError):
            self.session.resolve_targets('c1,a1')

    def test_ambiguous_track_is_still_an_error(self):
        with self.assertRaises(SelectorError):
            self.session.resolve_targets('a1.t1')
