# Picard, the next-generation MusicBrainz tagger
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

"""Regression test for PICARD-3513.

A blocking (CRITICAL) plugin album task gates album finalization. When the task
is completed from the plugin's web-service callback (a non-main thread), nothing
re-attempted finalization, so the album stayed in the loading state forever.
"""

from pathlib import Path
from unittest.mock import Mock, patch

from test.picardtestcase import PicardTestCase
from test.plugins3.helpers import load_plugin_manifest

from picard.album import Album
from picard.album_requests import TaskType
from picard.plugin3.api import PluginApi


def _run_sync(func, *args, **kwargs):
    """Stand-in for thread.to_main that runs the callback synchronously."""
    func(*args, **kwargs)


class CompleteAlbumTaskFinalizeTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.album = Album('123')
        self.api = PluginApi(load_plugin_manifest('example'), Mock(), Mock(), Path(''))

    def _gate_loading(self, task_id):
        """Reproduce the mid-load state left by the release handler when a
        blocking plugin task is still pending."""
        self.album.loaded = False
        self.album._new_metadata = self.album.metadata
        self.album._new_tracks = []
        self.album._tracks_loaded = True  # avoid the _load_tracks network path
        self.album.add_task(task_id, TaskType.CRITICAL, 'blocking plugin task')

    def test_completing_last_critical_task_refinalizes(self):
        self._gate_loading(f'{self.api.plugin_id}_bio')

        # While the task is pending, finalization is gated.
        with patch.object(Album, '_finalize_loading_album') as finalize_album:
            self.album._finalize_loading(error=False)
        finalize_album.assert_not_called()
        self.assertFalse(self.album.loaded)

        # Completing from the plugin API must re-attempt finalization.
        with (
            patch('picard.album.thread.to_main', side_effect=_run_sync),
            patch.object(Album, '_finalize_loading_album') as finalize_album,
        ):
            self.api.complete_album_task(self.album, 'bio')
        finalize_album.assert_called_once()

    def test_completing_non_last_critical_task_stays_gated(self):
        self._gate_loading(f'{self.api.plugin_id}_bio')
        self.album.add_task('release_metadata', TaskType.CRITICAL, 'another blocking task')

        with (
            patch('picard.album.thread.to_main', side_effect=_run_sync),
            patch.object(Album, '_finalize_loading_album') as finalize_album,
        ):
            self.api.complete_album_task(self.album, 'bio')
        finalize_album.assert_not_called()

    def test_completing_task_on_loaded_album_is_noop(self):
        self.album.add_task(f'{self.api.plugin_id}_bio', TaskType.CRITICAL, 'blocking plugin task')
        self.album.loaded = True

        with (
            patch('picard.album.thread.to_main', side_effect=_run_sync),
            patch.object(Album, '_finalize_loading') as finalize,
        ):
            self.api.complete_album_task(self.album, 'bio')
        finalize.assert_not_called()
