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

"""`file add` applies the Workspace loaded-file placement policy.

Workspace.place_loaded_file holds the per-file placement policy (embedded-MBID
auto-move, etc). The engine's `file add` applies it so a file carrying a
release MBID is moved to its album instead of being left unclustered — matching
the GUI.
"""

import os
from unittest.mock import (
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase

from picard.cli.engine.dispatch import dispatch
from picard.file import File
from picard.util import (
    normpath,
    resolve_fs_path,
)


_VALID_ALBUM_MBID = '00000000-0000-0000-0000-000000000001'
_VALID_RECORDING_MBID = '00000000-0000-0000-0000-000000000002'


class FileAddPlacementTest(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(
            setting={
                'ignore_file_mbids': False,
                'ignore_hidden_files': False,
                'ignore_regex': '',
                'analyze_new_files': False,
                'cluster_new_files': False,
            }
        )

    def _make_file(self, name, albumid=None, recordingid=None):
        # `file add` normalises paths like the GUI does; use the same form here.
        f = File(normpath(resolve_fs_path(name)))
        if albumid:
            f.metadata['musicbrainz_albumid'] = albumid
        if recordingid:
            f.metadata['musicbrainz_recordingid'] = recordingid
        # Pretend the load already succeeded (the registry.open + file.load are
        # patched); place_loaded_file only inspects metadata/state.
        f.state = File.State.NORMAL
        return f

    def _dispatch_add(self, files):
        # Patch path expansion and the format registry so `file add` operates on
        # our in-memory File objects without touching disk.
        paths = [f.filename for f in files]
        by_path = {f.filename: f for f in files}
        with (
            patch('picard.cli.engine.builtins.files._expand_input_paths', return_value=(paths, [])),
            patch('picard.workspace.services') as mock_services,
            patch.object(File, 'load', lambda self, callback: callback(self)),
        ):
            mock_services.return_value.format_registry.open.side_effect = lambda p: by_path[p]
            return dispatch(self.session, self.reg, 'file add x')

    def test_files_are_added_in_filename_order(self):
        # A directory scan returns files in no particular order; the handles
        # (f1, f2, ...) must follow the filenames, as in the GUI.
        files = [self._make_file(name) for name in ('03 c.flac', '01 a.flac', '02 b.flac')]
        result = self._dispatch_add(files)
        self.assertEqual(['01 a.flac', '02 b.flac', '03 c.flac'], [it.data['filename'] for it in result.items])
        self.assertEqual(['f1', 'f2', 'f3'], [it.handle for it in result.items])
        self.assertEqual(['f1', 'f2', 'f3'], result.mints)

    def test_already_loaded_file_is_not_added_twice(self):
        f = self._make_file('plain.flac')
        first = self._dispatch_add([f])
        self.assertEqual(['added'], [it.status for it in first.items])

        # Adding the same path again must not open a second File.
        second = self._dispatch_add([f])
        self.assertTrue(second.ok)
        self.assertEqual(['already_loaded'], [it.status for it in second.items])
        self.assertEqual(first.items[0].handle, second.items[0].handle)
        self.assertEqual([], second.mints)
        self.assertEqual(1, len(self.wks.unclustered_files.files))
        self.assertIs(f, self.wks.files[f.filename])

    def test_files_matching_ignore_rules_are_not_added(self):
        self.set_config_values(setting={'ignore_hidden_files': False, 'ignore_regex': r'\.bak$'})
        skipped_regex = self._make_file('song.bak')
        skipped_smb = self._make_file('.smbdelete1234')
        kept = self._make_file('song.flac')
        result = self._dispatch_add([skipped_regex, skipped_smb, kept])
        self.assertTrue(result.ok)
        ignored = {it.data['path'] for it in result.items if it.status == 'ignored'}
        self.assertEqual({skipped_regex.filename, skipped_smb.filename}, ignored)
        self.assertEqual(1, len([it for it in result.items if it.status == 'added']))
        self.assertEqual([kept], list(self.wks.unclustered_files.files))
        self.assertNotIn(skipped_regex.filename, self.wks.files)

    def test_file_with_album_mbid_is_moved_to_album(self):
        f = self._make_file('tagged.flac', albumid=_VALID_ALBUM_MBID)
        with patch.object(self.wks, 'move_file_to_album') as mock_move:
            result = self._dispatch_add([f])
            self.assertTrue(result.ok)
            mock_move.assert_called_once_with(f, _VALID_ALBUM_MBID)

    def test_file_with_album_and_recording_mbid_moved_to_track(self):
        f = self._make_file('tagged.flac', albumid=_VALID_ALBUM_MBID, recordingid=_VALID_RECORDING_MBID)
        with patch.object(self.wks, 'move_file_to_track') as mock_move:
            result = self._dispatch_add([f])
            self.assertTrue(result.ok)
            mock_move.assert_called_once_with(f, _VALID_ALBUM_MBID, _VALID_RECORDING_MBID)

    def test_untagged_file_is_not_auto_moved(self):
        f = self._make_file('plain.flac')
        with (
            patch.object(self.wks, 'move_file_to_album') as mock_album,
            patch.object(self.wks, 'move_file_to_track') as mock_track,
            patch.object(self.wks, 'move_file_to_nat') as mock_nat,
        ):
            result = self._dispatch_add([f])
            self.assertTrue(result.ok)
            mock_album.assert_not_called()
            mock_track.assert_not_called()
            mock_nat.assert_not_called()

    def test_ignore_file_mbids_disables_auto_move(self):
        self.set_config_values(setting={'ignore_file_mbids': True})
        f = self._make_file('tagged.flac', albumid=_VALID_ALBUM_MBID)
        with patch.object(self.wks, 'move_file_to_album') as mock_move:
            result = self._dispatch_add([f])
            self.assertTrue(result.ok)
            mock_move.assert_not_called()

    def test_unplaced_files_are_clustered_when_cluster_new_files_is_set(self):
        # As in the GUI: the files left over once every load is done are clustered.
        self.set_config_values(setting={'cluster_new_files': True})
        files = [self._make_file(name) for name in ('01 a.flac', '02 b.flac')]
        with patch.object(self.wks, 'cluster') as mock_cluster:
            result = self._dispatch_add(files)
        self.assertTrue(result.ok)
        mock_cluster.assert_called_once_with(files)

    def test_files_are_not_clustered_unless_asked(self):
        files = [self._make_file(name) for name in ('01 a.flac', '02 b.flac')]
        with patch.object(self.wks, 'cluster') as mock_cluster:
            self._dispatch_add(files)
        mock_cluster.assert_not_called()

    def test_files_with_a_release_mbid_are_not_clustered(self):
        self.set_config_values(setting={'cluster_new_files': True})
        tagged = self._make_file('tagged.flac', albumid=_VALID_ALBUM_MBID)
        with (
            patch.object(self.wks, 'cluster') as mock_cluster,
            patch.object(self.wks, 'move_file_to_album'),
        ):
            self._dispatch_add([tagged])
        mock_cluster.assert_not_called()


class FileAddUnsupportedTest(EngineCommandTestCase):
    """Unsupported files: ignored when a folder or a pattern brought them in, reported when named."""

    def setUp(self):
        super().setUp()
        self.set_config_values(
            setting={
                'ignore_file_mbids': True,
                'ignore_hidden_files': False,
                'ignore_regex': '',
                'recursively_add_files': True,
                'analyze_new_files': False,
                'cluster_new_files': False,
            }
        )
        self.root = normpath(self.mktmpdir())
        self.track = self._touch('01 track.flac')
        self.cover = self._touch('cover.jpg')

    def _touch(self, name):
        path = os.path.join(self.root, name)
        open(path, 'w').close()
        return path

    def _add(self, *words):
        def open_file(path):
            if path.endswith('.jpg'):
                return None  # not an audio format
            file = File(path)
            file.state = File.State.NORMAL
            return file

        with (
            patch('picard.workspace.services') as mock_services,
            patch.object(File, 'load', lambda self, callback: callback(self)),
        ):
            mock_services.return_value.format_registry.open.side_effect = open_file
            return dispatch(self.session, self.reg, 'file add ' + ' '.join(f'"{word}"' for word in words))

    def test_unsupported_file_found_in_a_folder_is_ignored_silently(self):
        result = self._add(self.root)
        self.assertTrue(result.ok, result.error)
        self.assertEqual(['added'], [it.status for it in result.items])
        self.assertEqual('01 track.flac', result.items[0].data['filename'])

    def test_unsupported_file_matched_by_a_pattern_is_ignored_silently(self):
        result = self._add(os.path.join(self.root, '*'))
        self.assertEqual(['added'], [it.status for it in result.items])

    def test_unsupported_file_named_explicitly_is_reported(self):
        result = self._add(self.cover)
        self.assertEqual(['unsupported'], [it.status for it in result.items])
        self.assertEqual(self.cover, result.items[0].data['path'])

    def test_named_and_found_together(self):
        result = self._add(self.root, self.cover)
        # Once each, although the folder brought the cover in too.
        self.assertCountEqual(['added', 'unsupported'], [it.status for it in result.items])
