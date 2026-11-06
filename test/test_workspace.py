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


import os
from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import (
    PicardTestCase,
    set_hidden_attribute,
)

from picard.album import Album
from picard.cluster import (
    Cluster,
    ClusterList,
    UnclusteredFiles,
)
from picard.file import File
from picard.track import Track
from picard.workspace import (
    OpenedFiles,
    Workspace,
    set_workspace_provider,
    workspace,
)


class WorkspaceAutotagTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        # autotag flashes via notifier().flash_busy(); patch the accessor in
        # picard.workspace and assert on the facade's method.
        patcher = patch('picard.workspace.notifier')
        self.mock_flash = patcher.start().return_value.flash_busy
        self.addCleanup(patcher.stop)

    def test_autotag_flashes_once_for_batch(self):
        obj1 = MagicMock(can_autotag=True)
        obj2 = MagicMock(can_autotag=True)
        Workspace().autotag([obj1, obj2])
        self.mock_flash.assert_called_once_with()
        obj1.lookup_metadata.assert_called_once_with()
        obj2.lookup_metadata.assert_called_once_with()

    def test_autotag_does_not_flash_when_nothing_taggable(self):
        obj = MagicMock(can_autotag=False)
        Workspace().autotag([obj])
        self.mock_flash.assert_not_called()
        obj.lookup_metadata.assert_not_called()


class WorkspaceTest(PicardTestCase):
    def test_initial_fields(self):
        w = Workspace()
        self.assertEqual(w.files, {})
        self.assertEqual(w.albums, {})
        self.assertEqual(w.release_groups, {})
        self.assertEqual(w.mbid_redirects, {})
        self.assertIsInstance(w.clusters, ClusterList)
        self.assertIsInstance(w.unclustered_files, UnclusteredFiles)
        self.assertIsNone(w.nats)

    def test_initial_bookkeeping(self):
        w = Workspace()
        self.assertEqual(w._pending_files_count, 0)
        self.assertEqual(w._saving_files_count, 0)
        self.assertEqual(w._saving_dirty_image_parents, set())
        self.assertFalse(w._restoring_session)

    def test_registries_are_per_instance(self):
        a = Workspace()
        b = Workspace()
        a.files['x'] = object()
        self.assertEqual(b.files, {})
        self.assertIsNot(a.clusters, b.clusters)
        self.assertIsNot(a.unclustered_files, b.unclustered_files)


class WorkspaceAccessorTest(PicardTestCase):
    def test_process_wide_accessor_is_stable(self):
        self.assertIs(workspace(), workspace())
        self.assertIsInstance(workspace(), Workspace)

    def test_set_workspace_provider_installs(self):
        provider = Workspace()
        self.addCleanup(set_workspace_provider, None)
        set_workspace_provider(provider)
        self.assertIs(workspace(), provider)

    def test_set_workspace_provider_none_installs_fresh_empty(self):
        provider = Workspace()
        provider.files['x'] = object()
        set_workspace_provider(provider)
        self.assertIs(workspace(), provider)
        # Passing None installs a fresh, empty workspace (not the old provider).
        set_workspace_provider(None)
        self.assertIsNot(workspace(), provider)
        self.assertEqual(workspace().files, {})


class WorkspaceClusterFilesTest(PicardTestCase):
    """Synchronous cluster_files + the shared per-group apply_file_cluster."""

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.set_config_values(setting={'va_name': 'Various Artists', 'nat_name': 'Standalone Recordings'})
        # File._move touches the acoustid/isrc managers via services(); the mock
        # tagger is the services provider in tests, so stub them.
        self.tagger.acoustid_manager = MagicMock()
        self.tagger.isrc_submit_manager = MagicMock()
        self.wks = Workspace()
        self.addCleanup(set_workspace_provider, None)
        set_workspace_provider(self.wks)

    def _add_unclustered(self, album, artist, name):
        from picard.file import File

        f = File(name)
        f.metadata['album'] = album
        f.metadata['albumartist'] = artist
        self.wks.files[f.filename] = f
        self.wks.unclustered_files.add_file(f)
        return f

    def test_cluster_files_groups_multi_file_albums(self):
        self._add_unclustered('Album A', 'Artist A', 'a1.flac')
        self._add_unclustered('Album A', 'Artist A', 'a2.flac')
        self._add_unclustered('Album B', 'Artist B', 'b1.flac')
        self._add_unclustered('Album B', 'Artist B', 'b2.flac')
        touched = self.wks.cluster_files(list(self.wks.unclustered_files.files))
        self.assertEqual(2, len(touched))
        self.assertEqual(2, len(list(self.wks.clusters)))

    def test_cluster_files_single_file_group_stays_unclustered(self):
        self._add_unclustered('Album A', 'Artist A', 'a1.flac')
        self._add_unclustered('Album A', 'Artist A', 'a2.flac')
        self._add_unclustered('Lonely', 'Nobody', 'solo.flac')
        touched = self.wks.cluster_files(list(self.wks.unclustered_files.files))
        # Only the 2-file album clusters; the lone file does not.
        self.assertEqual(1, len(touched))
        self.assertEqual(1, len(list(self.wks.clusters)))

    def test_cluster_files_empty_returns_empty(self):
        self.assertEqual([], self.wks.cluster_files([]))
        self.assertEqual(0, len(list(self.wks.clusters)))

    def test_apply_file_cluster_single_file_returns_unclustered(self):
        f = self._add_unclustered('Lonely', 'Nobody', 'solo.flac')
        file_cluster = MagicMock(files=[f], title='Lonely', artist='Nobody')
        container = self.wks.apply_file_cluster(file_cluster)
        self.assertIs(container, self.wks.unclustered_files)


class WorkspaceAsyncClusterTest(PicardTestCase):
    """Asynchronous cluster(): dispatch on a worker thread, apply in batches."""

    def setUp(self):
        super().setUp()
        self.wks = Workspace()
        self.addCleanup(set_workspace_provider, None)
        set_workspace_provider(self.wks)

    def test_cluster_flashes_and_dispatches_when_files_present(self):
        files = (MagicMock(), MagicMock())
        with (
            patch('picard.workspace.notifier') as mock_notifier,
            patch('picard.workspace.iter_files_from_objects', return_value=iter(files)),
            patch('picard.workspace.thread') as mock_thread,
        ):
            self.wks.cluster(object())
            mock_notifier.return_value.flash_busy.assert_called_once_with()
            mock_thread.run_task.assert_called_once()

    def test_cluster_does_not_flash_when_no_files(self):
        with (
            patch('picard.workspace.notifier') as mock_notifier,
            patch('picard.workspace.iter_files_from_objects', return_value=iter(())),
            patch('picard.workspace.thread') as mock_thread,
        ):
            self.wks.cluster(object())
            mock_notifier.return_value.flash_busy.assert_not_called()
            # Empty is still dispatched; the worker simply finds nothing.
            mock_thread.run_task.assert_called_once()

    def test_clustering_finished_applies_in_batches_and_calls_on_complete(self):
        on_complete = MagicMock()
        fc1 = MagicMock()
        fc2 = MagicMock()
        with (
            patch('picard.workspace.view_updates') as mock_vu,
            patch('picard.workspace.thread') as mock_thread,
            patch.object(self.wks, 'apply_file_cluster') as mock_apply,
        ):
            self.wks._clustering_finished(on_complete, result=(fc1, fc2))
            mock_vu.return_value.suspend_while_loading_enter.assert_called_once_with()
            # Application is handed to the batch helper with our apply function.
            mock_thread.process_in_batches.assert_called_once()
            args, kwargs = mock_thread.process_in_batches.call_args
            self.assertEqual([fc1, fc2], args[0])
            self.assertIs(mock_apply, args[1])
            # The finished callback exits the suspension and runs on_complete.
            kwargs['on_complete']()
            mock_vu.return_value.suspend_while_loading_exit.assert_called_once_with()
            on_complete.assert_called_once_with()

    def test_clustering_finished_logs_and_returns_on_error(self):
        on_complete = MagicMock()
        with (
            patch('picard.workspace.view_updates') as mock_vu,
            patch('picard.workspace.thread') as mock_thread,
        ):
            self.wks._clustering_finished(on_complete, error=RuntimeError("boom"))
            mock_vu.return_value.suspend_while_loading_enter.assert_not_called()
            mock_thread.process_in_batches.assert_not_called()
            on_complete.assert_not_called()


class WorkspaceAnalyzeFlashTest(PicardTestCase):
    """analyze() (the AcoustID 'Scan' action) should flash the busy cursor once
    per user action to acknowledge the async work, and only when AcoustID is
    enabled and there is something to analyze.
    """

    def test_analyze_flashes_once_for_batch(self):
        wks = MagicMock(spec=Workspace)
        wks.use_acoustid = True
        file1 = MagicMock(can_analyze=True)
        file2 = MagicMock(can_analyze=True)
        with (
            patch('picard.workspace.notifier') as mock_notifier,
            patch('picard.workspace.services'),
            patch('picard.workspace.iter_files_from_objects', return_value=iter((file1, file2))),
        ):
            Workspace.analyze(wks, object())
            mock_notifier.return_value.flash_busy.assert_called_once_with()

    def test_analyze_does_not_flash_when_acoustid_disabled(self):
        wks = MagicMock(spec=Workspace)
        wks.use_acoustid = False
        with (
            patch('picard.workspace.notifier') as mock_notifier,
            patch('picard.workspace.iter_files_from_objects', return_value=iter((MagicMock(),))),
        ):
            Workspace.analyze(wks, object())
            mock_notifier.return_value.flash_busy.assert_not_called()

    def test_analyze_does_not_flash_when_nothing_analyzable(self):
        wks = MagicMock(spec=Workspace)
        wks.use_acoustid = True
        file = MagicMock(can_analyze=False)
        with (
            patch('picard.workspace.notifier') as mock_notifier,
            patch('picard.workspace.services'),
            patch('picard.workspace.iter_files_from_objects', return_value=iter((file,))),
        ):
            Workspace.analyze(wks, object())
            mock_notifier.return_value.flash_busy.assert_not_called()


class WorkspaceLoadMbidTest(PicardTestCase):
    """load_mbid brings the window to front (via the facade) then loads."""

    def test_load_mbid_album_brings_front_then_loads_album(self):
        wks = Workspace()
        with (
            patch('picard.workspace.view_presentation') as mock_vp,
            patch.object(wks, 'load_album') as mock_load_album,
            patch.object(wks, 'load_nat') as mock_load_nat,
        ):
            wks.load_mbid('album', 'some-mbid')
            mock_vp.return_value.bring_to_front.assert_called_once_with()
            mock_load_album.assert_called_once_with('some-mbid')
            mock_load_nat.assert_not_called()

    def test_load_mbid_nat_loads_nat(self):
        wks = Workspace()
        with (
            patch('picard.workspace.view_presentation') as mock_vp,
            patch.object(wks, 'load_album') as mock_load_album,
            patch.object(wks, 'load_nat') as mock_load_nat,
        ):
            wks.load_mbid('nat', 'rec-mbid')
            mock_vp.return_value.bring_to_front.assert_called_once_with()
            mock_load_nat.assert_called_once_with('rec-mbid')
            mock_load_album.assert_not_called()

    def test_load_mbid_unknown_type_loads_nothing(self):
        wks = Workspace()
        with (
            patch('picard.workspace.view_presentation'),
            patch.object(wks, 'load_album') as mock_load_album,
            patch.object(wks, 'load_nat') as mock_load_nat,
        ):
            wks.load_mbid('bogus', 'x')
            mock_load_album.assert_not_called()
            mock_load_nat.assert_not_called()


class WorkspaceRemoveAlbumIfCompleteTest(PicardTestCase):
    """remove_album_if_complete: a file-post-save processor honouring the
    remove_complete_albums_after_save setting and going through the
    view-presentation facade.
    """

    def _file_with_album(self, album):
        obj = MagicMock()
        obj.parent_item.album = album
        return obj

    def test_removes_when_enabled_complete_and_saved(self):
        self.set_config_values(setting={'remove_complete_albums_after_save': True})
        wks = Workspace()
        album = MagicMock(id='rel-1', is_complete=MagicMock(return_value=True))
        album.get_num_unsaved_files.return_value = 0
        wks.albums['rel-1'] = album
        with patch('picard.workspace.view_presentation') as mock_vp:
            wks.remove_album_if_complete(self._file_with_album(album))
            mock_vp.return_value.remove.assert_called_once_with([album])

    def test_noop_when_setting_disabled(self):
        self.set_config_values(setting={'remove_complete_albums_after_save': False})
        wks = Workspace()
        album = MagicMock(id='rel-1')
        wks.albums['rel-1'] = album
        with patch('picard.workspace.view_presentation') as mock_vp:
            wks.remove_album_if_complete(self._file_with_album(album))
            mock_vp.return_value.remove.assert_not_called()

    def test_noop_when_no_album(self):
        self.set_config_values(setting={'remove_complete_albums_after_save': True})
        wks = Workspace()
        obj = MagicMock()
        obj.parent_item = None
        with patch('picard.workspace.view_presentation') as mock_vp:
            wks.remove_album_if_complete(obj)
            mock_vp.return_value.remove.assert_not_called()

    def test_noop_when_album_not_loaded(self):
        self.set_config_values(setting={'remove_complete_albums_after_save': True})
        wks = Workspace()
        album = MagicMock(id='rel-1')
        # album not in wks.albums
        with patch('picard.workspace.view_presentation') as mock_vp:
            wks.remove_album_if_complete(self._file_with_album(album))
            mock_vp.return_value.remove.assert_not_called()

    def test_noop_when_incomplete_or_unsaved(self):
        self.set_config_values(setting={'remove_complete_albums_after_save': True})
        wks = Workspace()
        album = MagicMock(id='rel-1', is_complete=MagicMock(return_value=True))
        album.get_num_unsaved_files.return_value = 2
        wks.albums['rel-1'] = album
        with patch('picard.workspace.view_presentation') as mock_vp:
            wks.remove_album_if_complete(self._file_with_album(album))
            mock_vp.return_value.remove.assert_not_called()


class WorkspaceOpenFilesTest(PicardTestCase):
    """open_files(): open and register new files, reporting what was skipped."""

    def setUp(self):
        super().setUp()
        self.set_config_values({'ignore_regex': '', 'ignore_hidden_files': True})
        self.registry = MagicMock()
        # Only ".mp3" is "supported"; a fake File remembers its filename.
        self.registry.open.side_effect = lambda name: MagicMock(filename=name) if name.endswith('.mp3') else None
        patcher = patch('picard.workspace.services')
        patcher.start().return_value.format_registry = self.registry
        self.addCleanup(patcher.stop)
        self.wks = Workspace()

    def _path(self, name):
        return os.path.abspath(os.path.join(os.sep, 'music', name))

    def test_opens_and_registers_new_files(self):
        a, b = self._path('b.mp3'), self._path('a.mp3')
        result = self.wks.open_files([a, b])
        self.assertIsInstance(result, OpenedFiles)
        self.assertEqual(set(self.wks.files), {a, b})
        self.assertEqual([f.filename for f in result.opened], sorted([a, b]))
        self.assertEqual((result.ignored, result.already_loaded, result.unsupported), ([], [], []))

    def test_opened_files_are_sorted_by_filename(self):
        names = [self._path(n) for n in ('c.mp3', 'a.mp3', 'b.mp3')]
        result = self.wks.open_files(names)
        self.assertEqual([f.filename for f in result.opened], sorted(names))

    def test_skips_file_already_in_the_working_set(self):
        path = self._path('a.mp3')
        existing = MagicMock(filename=path)
        self.wks.files[path] = existing
        result = self.wks.open_files([path])
        self.assertEqual(result.already_loaded, [existing])
        self.assertEqual(result.opened, [])
        self.registry.open.assert_not_called()

    def test_reports_unsupported_files(self):
        path = self._path('cover.jpg')
        result = self.wks.open_files([path])
        self.assertEqual(result.unsupported, [path])
        self.assertEqual(result.opened, [])
        self.assertNotIn(path, self.wks.files)

    def test_reports_hidden_files(self):
        path = os.path.join(self.mktmpdir(), '.hidden.mp3')
        open(path, 'w').close()
        set_hidden_attribute(path)
        result = self.wks.open_files([path])
        # The path is normalised by open_files (a temporary directory may be a junction).
        self.assertEqual(len(result.ignored), 1)
        self.assertTrue(os.path.samefile(result.ignored[0], path))
        self.registry.open.assert_not_called()

    def test_ignore_regex_is_honoured(self):
        self.set_config_values({'ignore_regex': r'skip'})
        path = self._path('skip_me.mp3')
        result = self.wks.open_files([path])
        self.assertEqual(result.ignored, [path])
        self.assertEqual(self.wks.files, {})

    def test_same_path_twice_is_opened_once(self):
        path = self._path('a.mp3')
        result = self.wks.open_files([path, path])
        self.assertEqual(len(result.opened), 1)
        self.assertEqual(len(result.already_loaded), 1)
        self.assertEqual(self.registry.open.call_count, 1)


class WorkspaceMoveFilesTest(PicardTestCase):
    """move_files(): dispatch on the kind of place the files are moved to."""

    def setUp(self):
        super().setUp()
        patcher = patch('picard.workspace.view_updates')
        self.mock_view_updates = patcher.start()
        self.addCleanup(patcher.stop)
        self.wks = Workspace()
        self.files = [MagicMock(name=f'file{i}') for i in range(3)]

    def test_none_target_moves_nothing(self):
        self.wks.move_files(self.files, None)
        for file in self.files:
            file.move.assert_not_called()

    def test_unsupported_target_moves_nothing(self):
        self.wks.move_files(self.files, object())
        for file in self.files:
            file.move.assert_not_called()

    def test_moves_files_to_cluster(self):
        cluster = MagicMock(spec=Cluster)
        self.wks.move_files(self.files, cluster)
        for file in self.files:
            file.move.assert_called_once_with(cluster)

    def test_moves_files_to_file_parent(self):
        target = MagicMock(spec=File)
        target.parent_item = MagicMock(spec=Cluster)
        self.wks.move_files(self.files, target)
        for file in self.files:
            file.move.assert_called_once_with(target.parent_item)

    def test_track_target_spreads_files_over_following_tracks(self):
        track1, track2 = MagicMock(spec=Track), MagicMock(spec=Track)
        album = MagicMock(spec=Album)
        album.get_next_track.side_effect = {track1: track2, track2: None}.get
        album.unmatched_files = MagicMock(name='unmatched')
        track1.album = album
        self.wks.move_files(self.files, track1)
        self.files[0].move.assert_called_once_with(track1)
        self.files[1].move.assert_called_once_with(track2)
        self.files[2].move.assert_called_once_with(album.unmatched_files)

    def test_track_target_without_multi_tracks_keeps_the_track(self):
        track = MagicMock(spec=Track)
        track.album = MagicMock(spec=Album)
        self.wks.move_files(self.files, track, move_to_multi_tracks=False)
        for file in self.files:
            file.move.assert_called_once_with(track)
        track.album.get_next_track.assert_not_called()

    def test_album_target_matches_files_to_tracks(self):
        album = MagicMock(spec=Album)
        with patch.object(Workspace, 'move_files_to_album') as mock_move:
            self.wks.move_files(self.files, album)
        mock_move.assert_called_once_with(self.files, album=album)

    def test_cluster_list_target_clusters_files(self):
        with patch.object(Workspace, 'cluster') as mock_cluster:
            self.wks.move_files(self.files, MagicMock(spec=ClusterList))
        mock_cluster.assert_called_once_with(self.files)

    def test_suspends_view_updates_while_moving(self):
        self.wks.move_files(self.files, MagicMock(spec=Cluster))
        self.mock_view_updates.return_value.suspend_while_loading.assert_called_once_with()
        self.mock_view_updates.return_value.suspend_selection.assert_called_once_with()


class WorkspaceSaveTest(PicardTestCase):
    def test_saves_every_file_and_returns_them(self):
        file1, file2 = MagicMock(name='file1'), MagicMock(name='file2')
        objects = [object()]
        with patch('picard.workspace.iter_files_from_objects', return_value=iter((file1, file2))) as mock_iter:
            saved = Workspace().save(objects)
        mock_iter.assert_called_once_with(objects, save=True)
        file1.save.assert_called_once_with()
        file2.save.assert_called_once_with()
        self.assertEqual(saved, [file1, file2])

    def test_files_are_saved_as_they_are_found(self):
        file1, file2 = MagicMock(name='file1'), MagicMock(name='file2')
        seen_saved = []

        def found():
            yield file1
            # The first file is already being saved when the second one is found.
            seen_saved.append(file1.save.called)
            yield file2

        with patch('picard.workspace.iter_files_from_objects', return_value=found()):
            Workspace().save([object()])
        self.assertEqual(seen_saved, [True])

    def test_nothing_to_save(self):
        with patch('picard.workspace.iter_files_from_objects', return_value=iter(())):
            self.assertEqual(Workspace().save([]), [])


class WorkspaceScanPathsTest(PicardTestCase):
    def test_goes_into_directories_following_the_settings(self):
        self.set_config_values({'recursively_add_files': True, 'ignore_hidden_files': False})
        with patch('picard.workspace.scan_paths_recursive', return_value=iter(['a', 'b'])) as mock_scan:
            found = list(Workspace().scan_paths(['/music']))
        mock_scan.assert_called_once_with(['/music'], True, False)
        self.assertEqual(found, ['a', 'b'])

    def test_not_recursive_and_ignoring_hidden_files(self):
        self.set_config_values({'recursively_add_files': False, 'ignore_hidden_files': True})
        with patch('picard.workspace.scan_paths_recursive', return_value=iter(())) as mock_scan:
            list(Workspace().scan_paths(['/music']))
        mock_scan.assert_called_once_with(['/music'], False, True)
