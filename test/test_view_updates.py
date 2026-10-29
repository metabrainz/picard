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


from types import SimpleNamespace

from test.picardtestcase import PicardTestCase

from picard.util import IgnoreUpdatesContext
from picard.view_updates import (
    ViewUpdates,
    set_view_updates_sink,
    view_updates,
)


class ViewUpdatesTest(PicardTestCase):
    def test_no_sink_is_noop_context(self):
        vu = ViewUpdates()
        self.assertFalse(vu.has_sink)
        # The context must be usable and a no-op; the body still runs.
        ran = False
        with vu.suspend_metadata_box():
            ran = True
        self.assertTrue(ran)

    def test_delegates_to_sink_metadata_box(self):
        ignore_updates = IgnoreUpdatesContext()
        sink = SimpleNamespace(metadata_box=SimpleNamespace(ignore_updates=ignore_updates))
        vu = ViewUpdates()
        vu.set_sink(sink)
        self.assertTrue(vu.has_sink)
        # Inside the context the sink's ignore_updates must be active.
        self.assertFalse(bool(ignore_updates))
        with vu.suspend_metadata_box():
            self.assertTrue(bool(ignore_updates))
        self.assertFalse(bool(ignore_updates))

    def test_clearing_sink_reverts_to_noop(self):
        ignore_updates = IgnoreUpdatesContext()
        sink = SimpleNamespace(metadata_box=SimpleNamespace(ignore_updates=ignore_updates))
        vu = ViewUpdates()
        vu.set_sink(sink)
        vu.set_sink(None)
        self.assertFalse(vu.has_sink)
        with vu.suspend_metadata_box():
            # Sink detached: its context must not be entered.
            self.assertFalse(bool(ignore_updates))

    def test_process_wide_accessor_is_stable(self):
        self.assertIs(view_updates(), view_updates())
        self.assertIsInstance(view_updates(), ViewUpdates)

    def test_set_view_updates_sink_installs_and_clears(self):
        ignore_updates = IgnoreUpdatesContext()
        sink = SimpleNamespace(metadata_box=SimpleNamespace(ignore_updates=ignore_updates))
        self.addCleanup(set_view_updates_sink, None)
        set_view_updates_sink(sink)
        with view_updates().suspend_metadata_box():
            self.assertTrue(bool(ignore_updates))
        set_view_updates_sink(None)
        self.assertFalse(view_updates().has_sink)
