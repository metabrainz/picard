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
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase

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


class LookupCommandTest(_EngineTestBase):
    def test_lookup_no_taggable_is_ok_empty(self):
        # A bare unclustered file reports can_autotag False until it has files;
        # force it off to exercise the empty path deterministically.
        self._add_unclustered('a.flac')
        with patch.object(File, 'can_autotag', False):
            result = dispatch(self.session, self.reg, 'lookup f*')
        self.assertTrue(result.ok)
        self.assertEqual([], result.items)

    def test_lookup_calls_autotag_on_taggable(self):
        cluster = Cluster('Album', 'Artist')
        self.wks.clusters.append(cluster)
        with (
            patch.object(Cluster, 'can_autotag', True),
            patch.object(self.wks, 'autotag') as mock_autotag,
        ):
            result = dispatch(self.session, self.reg, 'lookup c*')
            self.assertTrue(result.ok)
            mock_autotag.assert_called_once()
            (called,), _ = mock_autotag.call_args
            self.assertIn(cluster, list(called))
