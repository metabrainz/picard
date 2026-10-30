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


from test.picardtestcase import PicardTestCase

from picard.cluster import (
    ClusterList,
    UnclusteredFiles,
)
from picard.workspace import (
    Workspace,
    set_workspace_provider,
    workspace,
)


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
