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

from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.album import Album
from picard.cli.engine.builtins import register_builtins
from picard.cli.engine.commands import (
    EngineCommandRegistry,
)
from picard.cli.engine.dispatch import (
    dispatch,
)
from picard.cli.engine.session import LocalEngineSession
from picard.cluster import Cluster
from picard.workspace import workspace


class LsCommandTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.session = LocalEngineSession(MagicMock())
        wks = workspace()
        self.album = Album('rel-1')
        wks.albums = {'rel-1': self.album}
        self.cluster = Cluster('My Cluster', 'An Artist')
        wks.clusters.append(self.cluster)

    def test_ls_lists_top_level_with_handles(self):
        r = dispatch(self.session, self.reg, 'ls')
        self.assertTrue(r.ok)
        handles = {it.handle for it in r.items}
        # One cluster (c1) and one album (a1); exact handles depend on mint order.
        self.assertEqual({'c1', 'a1'}, handles)

    def test_ls_selector_filters(self):
        r = dispatch(self.session, self.reg, 'ls a*')
        self.assertTrue(r.ok)
        self.assertEqual(['a1'], [it.handle for it in r.items])

    def test_ls_selector_split_across_tokens(self):
        dispatch(self.session, self.reg, 'ls')  # mint the handles
        for line in ('ls a1 c1', 'ls a1, c1', 'ls a1,c1', 'ls "a1, c1"'):
            with self.subTest(line=line):
                r = dispatch(self.session, self.reg, line)
                self.assertTrue(r.ok, r.error)
                self.assertEqual({'a1', 'c1'}, {it.handle for it in r.items})

    def test_bad_selector_is_reported_as_such(self):
        for line in ('ls !a1', 'ls a1.', 'ls z9'):
            with self.subTest(line=line):
                r = dispatch(self.session, self.reg, line)
                self.assertFalse(r.ok)
                self.assertIn('invalid selector', r.error)
                self.assertNotIn('failed', r.error)

    def test_ls_album_item_carries_release_ref(self):
        r = dispatch(self.session, self.reg, 'ls a*')
        data = r.items[0].data
        self.assertEqual('release', data['entity_type'])
        self.assertEqual('rel-1', data['mbid'])

    def test_ls_unknown_handle_reported_unresolved(self):
        r = dispatch(self.session, self.reg, 'ls a9')
        self.assertEqual([], r.items)
        self.assertEqual(['a9'], r.unresolved)

    def test_ls_candidate_shows_release_ref_and_title(self):
        # A candidate (m handle) listed via ls must carry the same projection
        # as the lookup listing (type:mbid, title, score), not an empty line.
        from picard.cli.engine.candidates import Candidate
        from picard.matching import SimMatchRelease

        release = {
            'id': 'rel-cand',
            'title': 'A Candidate Release',
            'artist-credit': [{'name': 'The Artist', 'artist': {'name': 'The Artist'}}],
        }
        cand = Candidate(SimMatchRelease(similarity=0.42, release=release))
        (handle,) = self.session.set_candidates(self.cluster, [cand])

        r = dispatch(self.session, self.reg, f'ls {handle}')
        self.assertTrue(r.ok)
        data = r.items[0].data
        self.assertEqual('release', data['entity_type'])
        self.assertEqual('rel-cand', data['mbid'])
        self.assertEqual('A Candidate Release', data['title'])
        self.assertEqual(0.42, data['similarity'])

    def test_ls_result_is_serializable(self):
        import json

        r = dispatch(self.session, self.reg, 'ls')
        json.dumps(r.to_dict())
