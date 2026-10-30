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


from types import SimpleNamespace
from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.view_sync import (
    ViewSync,
    set_view_sync_sink,
    view_sync,
)


class ViewSyncTest(PicardTestCase):
    def test_no_sink_is_noop(self):
        vs = ViewSync()
        self.assertFalse(vs.has_sink)
        # Must not raise with no sink installed (headless behaviour).
        vs.refresh_metadata_box()
        vs.update_cover_art()

    def test_refresh_metadata_box_forwards_to_sink(self):
        sink = MagicMock()
        vs = ViewSync()
        vs.set_sink(sink)
        self.assertTrue(vs.has_sink)
        vs.refresh_metadata_box()
        sink.refresh_metadatabox.assert_called_once_with()

    def test_update_cover_art_forwards_to_sink(self):
        cover_art_box = MagicMock()
        sink = SimpleNamespace(refresh_metadatabox=MagicMock(), cover_art_box=cover_art_box)
        vs = ViewSync()
        vs.set_sink(sink)
        vs.update_cover_art()
        cover_art_box.update_metadata.assert_called_once_with()

    def test_clearing_sink_reverts_to_noop(self):
        sink = MagicMock()
        vs = ViewSync()
        vs.set_sink(sink)
        vs.set_sink(None)
        self.assertFalse(vs.has_sink)
        vs.refresh_metadata_box()
        sink.refresh_metadatabox.assert_not_called()

    def test_process_wide_accessor_is_stable(self):
        self.assertIs(view_sync(), view_sync())
        self.assertIsInstance(view_sync(), ViewSync)

    def test_set_view_sync_sink_installs_and_clears(self):
        sink = MagicMock()
        self.addCleanup(set_view_sync_sink, None)
        set_view_sync_sink(sink)
        view_sync().refresh_metadata_box()
        sink.refresh_metadatabox.assert_called_once_with()
        set_view_sync_sink(None)
        self.assertFalse(view_sync().has_sink)
