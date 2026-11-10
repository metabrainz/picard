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

"""`remove`, `trash` and `lookup` engine commands.

These exercise Workspace.remove / trash_files / autotag through the engine.
"""

from unittest.mock import (
    MagicMock,
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase

from picard.cli.engine.candidates import Candidate
from picard.cli.engine.dispatch import dispatch
from picard.cluster import Cluster
from picard.file import File


class _EngineTestBase(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'va_name': 'Various Artists', 'nat_name': 'Standalone Recordings'})

    def _add_unclustered(self, name):
        f = File(name)
        self.wks.files[f.filename] = f
        self.wks.unclustered_files.add_file(f)
        return f


class RemoveCommandTest(_EngineTestBase):
    def test_remove_requires_selector(self):
        result = dispatch(self.session, self.reg, 'remove')
        self.assertFalse(result.ok)

    def test_remove_drops_files_from_working_set(self):
        f = self._add_unclustered('a.flac')
        handle = self.session.handle_for(f)
        result = dispatch(self.session, self.reg, 'remove ' + handle)
        self.assertTrue(result.ok)
        self.assertEqual(1, len(result.items))
        self.assertEqual('removed', result.items[0].status)
        self.assertNotIn(f.filename, self.wks.files)

    def test_remove_does_not_report_candidates_as_removed(self):
        match = MagicMock()
        match.release = {'id': 'rel-1'}
        match.similarity = 0.9
        cluster = Cluster('Album', 'Artist')
        (handle,) = self.session.set_candidates(cluster, [Candidate(match)])
        f = self._add_unclustered('b.flac')
        file_handle = self.session.handle_for(f)

        result = dispatch(self.session, self.reg, f'remove {handle},{file_handle}')
        self.assertTrue(result.ok)
        statuses = {it.handle: it.status for it in result.items}
        self.assertEqual({handle: 'skipped', file_handle: 'removed'}, statuses)
        self.assertNotIn(f.filename, self.wks.files)

    def test_remove_unresolved_handle_is_ok_empty(self):
        result = dispatch(self.session, self.reg, 'remove f999')
        self.assertTrue(result.ok)
        self.assertEqual([], result.items)


class TrashCommandTest(_EngineTestBase):
    def test_trash_requires_selector(self):
        result = dispatch(self.session, self.reg, 'trash')
        self.assertFalse(result.ok)

    def test_trash_delegates_to_workspace_trash_files(self):
        f = self._add_unclustered('a.flac')
        handle = self.session.handle_for(f)
        with patch.object(self.wks, 'trash_files') as mock_trash:
            result = dispatch(self.session, self.reg, 'trash ' + handle)
            self.assertTrue(result.ok)
            self.assertEqual('trashed', result.items[0].status)
            # Exactly the selected file is passed to trash_files.
            (called_files,), _ = mock_trash.call_args
            self.assertEqual([f], list(called_files))
