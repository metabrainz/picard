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

"""`tree` command: show the working set as an indented tree (the GUI panes).

Builds a working set directly against the Workspace registries (an unclustered
file, a cluster with files, an album with a track and a matched file) and
checks the depth-tagged, hierarchical item list.
"""

from test.cli.engine.helpers import EngineCommandTestCase

from picard.album import Album
from picard.cli.engine.dispatch import dispatch
from picard.cluster import Cluster
from picard.file import File
from picard.track import Track


class TreeCommandTest(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'va_name': 'Various Artists', 'nat_name': 'Standalone Recordings'})

    def test_empty_working_set_is_ok_empty(self):
        result = dispatch(self.session, self.reg, 'tree')
        self.assertTrue(result.ok)
        self.assertEqual([], result.items)

    def test_tree_shows_panes_with_depths(self):
        # Unclustered file (depth 0).
        loose = File('loose.flac')
        self.wks.files[loose.filename] = loose
        self.wks.unclustered_files.add_file(loose)

        # A cluster with one file (cluster depth 0, file depth 1).
        cluster = Cluster('Some Album', 'Some Artist')
        self.wks.clusters.append(cluster)
        cfile = File('clustered.flac')
        self.wks.files[cfile.filename] = cfile
        cluster.add_file(cfile)

        # An album with a track that has a matched file, plus an unmatched file.
        album = Album('rel-1')
        self.wks.albums['rel-1'] = album
        track = Track('trk-1', album)
        album.tracks.append(track)
        matched = File('matched.flac')
        self.wks.files[matched.filename] = matched
        track.files.append(matched)
        unmatched = File('unmatched.flac')
        self.wks.files[unmatched.filename] = unmatched
        album.unmatched_files.add_file(unmatched)

        result = dispatch(self.session, self.reg, 'tree')
        self.assertTrue(result.ok)

        # Collapse to (status, depth) in emission order for a structural check.
        shape = [(it.status, it.data.get('depth')) for it in result.items]
        self.assertEqual(
            [
                ('unclustered', 0),
                ('cluster', 0),
                ('file', 1),
                ('album', 0),
                ('track', 1),
                ('file', 2),
                ('unmatched', 1),
            ],
            shape,
        )
        # Every row carries a resolvable handle.
        self.assertTrue(all(it.handle for it in result.items))

    def test_tree_handles_are_actionable(self):
        # A handle emitted by tree resolves back to the same entity via ls.
        cluster = Cluster('Album', 'Artist')
        self.wks.clusters.append(cluster)
        tree = dispatch(self.session, self.reg, 'tree')
        cluster_item = next(it for it in tree.items if it.status == 'cluster')
        listed = dispatch(self.session, self.reg, 'ls ' + cluster_item.handle)
        self.assertEqual([cluster_item.handle], [it.handle for it in listed.items])

    def test_tree_selector_scopes_to_subtree(self):
        # Build two albums; `tree <handle>` shows only the selected one.
        album1 = Album('rel-1')
        self.wks.albums['rel-1'] = album1
        album1.tracks.append(Track('t-1', album1))
        album2 = Album('rel-2')
        self.wks.albums['rel-2'] = album2
        album2.tracks.append(Track('t-2', album2))

        a1_handle = self.session.handle_for(album1)
        result = dispatch(self.session, self.reg, 'tree ' + a1_handle)
        self.assertTrue(result.ok)
        # Only album1 and its single track, nothing from album2.
        statuses = [it.status for it in result.items]
        self.assertEqual(['album', 'track'], statuses)
        self.assertEqual(a1_handle, result.items[0].handle)
        self.assertEqual(0, result.items[0].data.get('depth'))
        self.assertEqual(1, result.items[1].data.get('depth'))

    def test_tree_selector_track_shows_its_files(self):
        album = Album('rel-1')
        self.wks.albums['rel-1'] = album
        track = Track('trk-1', album)
        album.tracks.append(track)
        matched = File('matched.flac')
        self.wks.files[matched.filename] = matched
        track.files.append(matched)
        track_handle = self.session.handle_for(track)

        result = dispatch(self.session, self.reg, f'tree {track_handle}')
        self.assertTrue(result.ok)
        self.assertEqual([('track', 0), ('file', 1)], [(it.status, it.data.get('depth')) for it in result.items])

    def test_tree_selector_path_to_a_disc(self):
        album = Album('rel-1')
        album.loaded = True
        self.wks.albums['rel-1'] = album
        for disc, number in ((1, 1), (2, 1)):
            track = Track(f'trk-{disc}', album)
            track.metadata['discnumber'] = str(disc)
            track.metadata['tracknumber'] = str(number)
            album.tracks.append(track)
        self.session.handle_for(album)

        result = dispatch(self.session, self.reg, 'tree a1.d2')
        self.assertTrue(result.ok)
        self.assertEqual([('track', 0)], [(it.status, it.data.get('depth')) for it in result.items])

    def test_tree_selector_unresolved_reported(self):
        result = dispatch(self.session, self.reg, 'tree a999')
        self.assertTrue(result.ok)
        self.assertEqual([], result.items)
        self.assertEqual(['a999'], result.unresolved)
