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

from unittest.mock import (
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase

from picard.album import Album
from picard.cli.engine.candidates import Candidate
from picard.cli.engine.dispatch import dispatch
from picard.cluster import Cluster
from picard.matching import SimMatchRelease
from picard.track import Track
from picard.workspace import workspace


_MBID = '1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d'


class AlbumLoadCommandTest(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self._loaded = []

        def fake_load_album(mbid, **kwargs):
            album = Album(mbid)
            self._loaded.append(mbid)
            workspace().albums[mbid] = album
            return album

        p = patch.object(workspace(), 'load_album', side_effect=fake_load_album)
        p.start()
        self.addCleanup(p.stop)

    def test_load_by_mbid_mints_album(self):
        result = dispatch(self.session, self.reg, f'album load {_MBID}')
        self.assertTrue(result.ok)
        self.assertEqual([_MBID], self._loaded)
        self.assertEqual(1, len(result.mints))
        self.assertTrue(result.mints[0].startswith('a'))
        self.assertEqual('loaded', result.items[0].status)

    def test_load_by_url(self):
        result = dispatch(self.session, self.reg, f'album load https://musicbrainz.org/release/{_MBID}')
        self.assertTrue(result.ok)
        self.assertEqual([_MBID], self._loaded)

    def test_accepted_spellings(self):
        for text in (
            _MBID,
            f'release:{_MBID}',  # the form shown by `ls` / `tree` round-trips
            f'mbid://{_MBID}',
            f'https://musicbrainz.org/release/{_MBID}',
            f'https://musicbrainz.org/release/{_MBID}/',
            f'https://musicbrainz.org/release/{_MBID}/cover-art',
        ):
            with self.subTest(text=text):
                self._loaded.clear()
                workspace().albums.clear()
                result = dispatch(self.session, self.reg, f'album load {text}')
                self.assertTrue(result.ok, result.error)
                self.assertEqual([_MBID], self._loaded)

    def test_rejected_spellings(self):
        for text in ('nope', 'release:not-an-mbid', 'https://example.com/foo'):
            with self.subTest(text=text):
                result = dispatch(self.session, self.reg, f'album load {text}')
                self.assertFalse(result.ok)
                self.assertIn('not a release MBID or URL', result.error)
        self.assertEqual([], self._loaded)

    def test_other_entities_are_not_loaded_as_releases(self):
        for entity in ('artist', 'recording', 'release-group'):
            with self.subTest(entity=entity):
                result = dispatch(self.session, self.reg, f'album load https://musicbrainz.org/{entity}/{_MBID}')
                self.assertFalse(result.ok)
                self.assertIn(f'is a {entity}, not a release', result.error)
        self.assertEqual([], self._loaded)

    def test_load_invalid_is_failure(self):
        result = dispatch(self.session, self.reg, 'album load nope')
        self.assertFalse(result.ok)
        self.assertEqual([], self._loaded)

    def test_load_missing_arg_is_failure(self):
        self.assertFalse(dispatch(self.session, self.reg, 'album load').ok)

    def test_loaded_album_is_listable(self):
        dispatch(self.session, self.reg, f'album load {_MBID}')
        listing = dispatch(self.session, self.reg, 'ls a*')
        self.assertEqual(1, len(listing.items))


class RefreshCommandTest(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.album = Album(_MBID)
        self.album.loaded = True
        workspace().albums[_MBID] = self.album
        self.run_command('ls')
        self.refreshed = []

        def fake_refresh(objs):
            self.refreshed.extend(objs)

        p = patch.object(workspace(), 'refresh', side_effect=fake_refresh)
        p.start()
        self.addCleanup(p.stop)

    def test_the_albums_are_refreshed_without_a_selector(self):
        result = self.run_command('refresh')
        self.assertTrue(result.ok, result.error)
        self.assertEqual([self.album], self.refreshed)
        self.assertEqual(['refreshed'], [item.status for item in result.items])

    def test_an_album_that_is_not_loaded_afterwards_is_pending(self):
        self.album.loaded = False
        self.assertEqual('pending', self.run_command('refresh a1').items[0].status)

    def test_an_album_with_errors_is_reported(self):
        self.album.error_append('boom')
        self.assertEqual('error', self.run_command('refresh a1').items[0].status)

    def test_an_album_that_is_still_loading_is_not_refreshed_again(self):
        with patch.object(Album, 'has_critical_tasks', return_value=True):
            result = self.run_command('refresh a1')
        self.assertEqual('pending', result.items[0].status)

    def test_what_cannot_be_refreshed_is_reported_as_unsupported(self):
        cluster = Cluster('Cluster', 'Artist')
        workspace().clusters.append(cluster)
        self.run_command('ls')
        result = self.run_command('refresh c1')
        self.assertEqual(['unsupported'], [item.status for item in result.items])
        self.assertEqual([], self.refreshed)

    def test_a_track_of_an_album_is_unsupported(self):
        track = Track('track-1')
        track.album = self.album
        self.album.tracks.append(track)
        self.run_command('ls')
        result = self.run_command('refresh a1.t1')
        self.assertEqual(['unsupported'], [item.status for item in result.items])
        self.assertEqual([], self.refreshed)
        # It says what to do instead.
        self.assertIn("a track is refreshed with its album, see 'refresh a1'", result.message)
        self.assertTrue(result.message.startswith('t1:'), result.message)

    def test_a_lookup_candidate_cannot_be_refreshed(self):
        cluster = Cluster('Cluster', 'Artist')
        workspace().clusters.append(cluster)
        release = {'id': 'rel-cand', 'title': 'A Release', 'artist-credit': []}
        (handle,) = self.session.set_candidates(cluster, [Candidate(SimMatchRelease(similarity=0.4, release=release))])
        result = self.run_command(f'refresh {handle}')
        self.assertFalse(result.ok)
        self.assertIn('cannot be refreshed', result.error)
        self.assertEqual([], self.refreshed)
