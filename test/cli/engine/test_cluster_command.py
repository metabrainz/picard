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

from test.cli.engine.helpers import EngineCommandTestCase

from picard.album import Album
from picard.cli.engine.candidates import Candidate
from picard.cli.engine.dispatch import dispatch
from picard.cluster import Cluster
from picard.file import File


class ClusterCommandTest(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'va_name': 'Various Artists', 'nat_name': 'Standalone Recordings'})

    def _add_unclustered(self, album, artist, name):
        f = File(name)
        f.metadata['album'] = album
        f.metadata['albumartist'] = artist
        self.wks.files[f.filename] = f
        self.wks.unclustered_files.add_file(f)
        return f

    def test_cluster_groups_multi_file_albums(self):
        self._add_unclustered('Album A', 'Artist A', 'a1.flac')
        self._add_unclustered('Album A', 'Artist A', 'a2.flac')
        self._add_unclustered('Album B', 'Artist B', 'b1.flac')
        self._add_unclustered('Album B', 'Artist B', 'b2.flac')

        result = dispatch(self.session, self.reg, 'cluster')
        self.assertTrue(result.ok)
        # Two multi-file albums → two clusters minted.
        self.assertEqual(2, len(result.mints))
        self.assertTrue(all(h.startswith('c') for h in result.mints))
        self.assertEqual(2, len(list(self.wks.clusters)))

    def test_single_file_group_stays_unclustered(self):
        self._add_unclustered('Album A', 'Artist A', 'a1.flac')
        self._add_unclustered('Album A', 'Artist A', 'a2.flac')
        self._add_unclustered('Lonely', 'Nobody', 'solo.flac')

        result = dispatch(self.session, self.reg, 'cluster')
        # Only the 2-file album clusters; the lone file does not.
        self.assertEqual(1, len(result.mints))
        self.assertEqual(1, len(list(self.wks.clusters)))

    def test_cluster_then_ls_shows_clusters(self):
        self._add_unclustered('Album A', 'Artist A', 'a1.flac')
        self._add_unclustered('Album A', 'Artist A', 'a2.flac')
        dispatch(self.session, self.reg, 'cluster')
        listing = dispatch(self.session, self.reg, 'ls c*')
        self.assertEqual(1, len(listing.items))
        self.assertTrue(listing.items[0].handle.startswith('c'))

    def test_cluster_empty_is_ok_no_mints(self):
        result = dispatch(self.session, self.reg, 'cluster')
        self.assertTrue(result.ok)
        self.assertEqual([], result.mints)

    def _cluster_of(self, *files):
        cluster = Cluster('Album A', 'Artist A')
        cluster.add_files(list(files))
        self.wks.clusters.append(cluster)
        return cluster

    def test_cluster_of_a_cluster_groups_its_files_again(self):
        files = [self._add_unclustered('Album A', 'Artist A', f'a{n}.flac') for n in (1, 2)]
        cluster = self._cluster_of(*files)
        handle = self.session.handle_for(cluster)
        result = dispatch(self.session, self.reg, f'cluster {handle}')
        self.assertTrue(result.ok)
        self.assertEqual({self.session.handle_for(f) for f in files}, set(result.resolved))

    def test_album_is_refused_with_a_hint(self):
        album = Album('rel-1')
        self.wks.albums['rel-1'] = album
        handle = self.session.handle_for(album)
        result = dispatch(self.session, self.reg, f'cluster {handle}')
        self.assertFalse(result.ok)
        self.assertIn('neither a file nor a cluster', result.error)
        self.assertIn(f'{handle}.f*', result.error)

    def test_candidate_is_refused(self):
        cluster = self._cluster_of()
        (handle,) = self.session.set_candidates(cluster, [Candidate(MagicMock())])
        result = dispatch(self.session, self.reg, f'cluster {handle}')
        self.assertFalse(result.ok)
        self.assertIn('neither a file nor a cluster', result.error)
