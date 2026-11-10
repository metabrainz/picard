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

import json
from unittest.mock import (
    MagicMock,
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase
from test.test_matching import settings as _matching_settings

from picard.cli.engine.dispatch import dispatch
from picard.cluster import Cluster
from picard.workspace import workspace


def _release(mbid, title, artist='The Artist', score=100):
    return {
        'id': mbid,
        'title': title,
        'score': score,
        'artist-credit': [{'artist': {'name': artist, 'sort-name': artist}, 'name': artist}],
    }


class ClusterLookupCommandTest(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        # Reuse the matching test's realistic config, plus lookup thresholds.
        self.set_config_values(
            setting={
                **_matching_settings,
                'match_min_similarity': 0.1,
                'match_min_margin': 0.0,
                'query_limit': 25,
                'always_standardize_multivalue_artist': False,
            }
        )
        self.tagger.mb_api = MagicMock()

        self.cluster = Cluster('Greatest Hits', 'The Artist')
        workspace().clusters.append(self.cluster)

        # Canned candidate releases: an exact title match and a weaker one.
        self.releases = [
            _release('mbid-weak', 'Something Else'),
            _release('mbid-best', 'Greatest Hits'),
        ]

        # find_releases invokes its callback synchronously with our document.
        def fake_find_releases(callback, **kwargs):
            callback({'releases': self.releases}, None, None)
            return MagicMock()  # a task handle

        self.tagger.mb_api.find_releases.side_effect = fake_find_releases

        # Stub the auto-apply so we don't actually load an album over the network.
        # Patch load_album / move_files_to_album on the real Workspace instance.
        # Return a real Album (classified as 'a') so handle_for() works.
        from picard.album import Album

        self._loaded = []

        def fake_load_album(mbid, **kwargs):
            album = Album(mbid)
            self._loaded.append(mbid)
            return album

        wks = workspace()
        p_load = patch.object(wks, 'load_album', side_effect=fake_load_album)
        p_move = patch.object(wks, 'move_files_to_album', MagicMock())
        p_load.start()
        p_move.start()
        self.addCleanup(p_load.stop)
        self.addCleanup(p_move.stop)

    def test_lookup_applies_best_and_exposes_candidates(self):
        result = dispatch(self.session, self.reg, 'cluster lookup')
        self.assertTrue(result.ok)
        self.assertEqual(1, len(result.items))
        item = result.items[0]
        self.assertEqual('matched', item.status)
        # Two candidates captured, exposed as m handles.
        cands = item.data['candidates']
        self.assertEqual(2, len(cands))
        self.assertTrue(all(c['handle'].startswith('m') for c in cands))
        # The exact-title release is the applied one.
        applied = [c for c in cands if c.get('applied')]
        self.assertEqual(1, len(applied))
        self.assertEqual('mbid-best', applied[0]['mbid'])
        # The best release was loaded as the matched album.
        self.assertIn('mbid-best', self._loaded)
        self.assertIsNotNone(item.data['matched_album'])

    def test_lookup_no_releases_reports_no_matches(self):
        self.releases = []

        def fake_find_releases(callback, **kwargs):
            callback({'releases': []}, None, None)
            return MagicMock()

        self.tagger.mb_api.find_releases.side_effect = fake_find_releases
        result = dispatch(self.session, self.reg, 'cluster lookup')
        self.assertEqual('no_matches', result.items[0].status)
        self.assertEqual([], result.items[0].data['candidates'])

    def test_lookup_request_error_is_reported_not_no_matches(self):
        http = MagicMock()
        http.errorString.return_value = 'Service Unavailable'

        def failing_find_releases(callback, **kwargs):
            callback(None, http, 203)  # a truthy network error code
            return MagicMock()

        self.tagger.mb_api.find_releases.side_effect = failing_find_releases
        result = dispatch(self.session, self.reg, 'cluster lookup')
        self.assertTrue(result.ok)
        item = result.items[0]
        self.assertEqual('lookup_failed', item.status)
        self.assertEqual('Service Unavailable', item.data['error'])
        self.assertEqual([], item.data['candidates'])
        self.assertEqual([], self._loaded)

    def test_lookup_result_serializable(self):
        result = dispatch(self.session, self.reg, 'cluster lookup')
        json.dumps(result.to_dict())

    def test_candidate_handles_resolve_for_match(self):
        result = dispatch(self.session, self.reg, 'cluster lookup')
        handle = result.items[0].data['candidates'][0]['handle']
        entities, unresolved = self.session.resolve(handle)
        self.assertEqual(1, len(entities))
        self.assertEqual([], unresolved)

    def test_lookup_release_load_failure_not_reported_as_match(self):
        # Simulate a failed release load (e.g. a 503 from the server): the
        # album comes back with errors populated. The lookup must NOT report a
        # confident match or move files, but still expose the candidates so a
        # retry via `match` is possible.
        from picard.album import Album

        def fake_load_album_error(mbid, **kwargs):
            album = Album(mbid)
            album.error_append("server replied with status code 503")
            self._loaded.append(mbid)
            return album

        workspace().load_album.side_effect = fake_load_album_error
        move_mock = workspace().move_files_to_album

        result = dispatch(self.session, self.reg, 'cluster lookup')
        item = result.items[0]
        self.assertEqual('load_failed', item.status)
        self.assertIsNone(item.data['matched_album'])
        self.assertIn('503', item.data.get('error', ''))
        # Candidates are still exposed for a retry.
        self.assertEqual(2, len(item.data['candidates']))
        # No matched-album handle minted; files were not moved.
        self.assertTrue(all(not h.startswith('a') for h in result.mints))
        move_mock.assert_not_called()


class MatchCommandTest(ClusterLookupCommandTest):
    """Reuses the lookup test harness (mocked find_releases + load_album)."""

    def _lookup(self):
        result = dispatch(self.session, self.reg, 'cluster lookup')
        cluster_handle = result.items[0].handle
        cands = result.items[0].data['candidates']
        return cluster_handle, cands

    def test_match_applies_chosen_candidate(self):
        cluster_handle, cands = self._lookup()
        # Pick the candidate that was NOT auto-applied (the weaker one).
        other = next(c for c in cands if not c.get('applied'))
        result = dispatch(self.session, self.reg, f'match {cluster_handle} {other["handle"]}')
        self.assertTrue(result.ok)
        item = result.items[0]
        self.assertEqual('matched', item.status)
        self.assertEqual(other['handle'], item.data['candidate'])
        # The chosen candidate's release was loaded.
        self.assertIn('mbid-weak', self._loaded)

    def test_match_flips_applied_flag(self):
        cluster_handle, cands = self._lookup()
        other = next(c for c in cands if not c.get('applied'))
        dispatch(self.session, self.reg, f'match {cluster_handle} {other["handle"]}')
        # Re-describe the candidate set: the chosen one is now applied, sole.
        entities, _ = self.session.resolve('m*')
        applied = [c for c in entities if c.applied]
        self.assertEqual(1, len(applied))
        self.assertEqual(other['handle'], self.session.handle_for(applied[0]))

    def test_match_rejects_candidate_of_another_cluster(self):
        _cluster_handle, cands = self._lookup()
        other_cluster = Cluster('Other Album', 'Other Artist')
        workspace().clusters.append(other_cluster)
        other_handle = self.session.handle_for(other_cluster)
        workspace().move_files_to_album.reset_mock()

        result = dispatch(self.session, self.reg, f'match {other_handle} {cands[0]["handle"]}')
        self.assertFalse(result.ok)
        self.assertIn('not a candidate', result.error)
        workspace().move_files_to_album.assert_not_called()

    def test_match_bad_usage_is_failure(self):
        self.assertFalse(dispatch(self.session, self.reg, 'match c1').ok)

    def test_match_unknown_candidate_unresolved(self):
        cluster_handle, _cands = self._lookup()
        result = dispatch(self.session, self.reg, f'match {cluster_handle} m99')
        self.assertFalse(result.ok)
        self.assertIn('m99', result.unresolved)

    def test_match_release_load_failure_is_failure(self):
        cluster_handle, cands = self._lookup()
        other = next(c for c in cands if not c.get('applied'))

        # The chosen candidate's release load fails (server error).
        from picard.album import Album

        def fake_load_album_error(mbid, **kwargs):
            album = Album(mbid)
            album.error_append("server replied with status code 503")
            return album

        workspace().load_album.side_effect = fake_load_album_error
        move_mock = workspace().move_files_to_album
        move_mock.reset_mock()

        result = dispatch(self.session, self.reg, f'match {cluster_handle} {other["handle"]}')
        self.assertFalse(result.ok)
        self.assertIn('503', result.error)
        # Files must not be moved onto a failed album.
        move_mock.assert_not_called()
