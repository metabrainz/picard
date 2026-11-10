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


"""Shared base for the tests that run engine commands against the real workspace."""

from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.cli.engine.builtins import register_builtins
from picard.cli.engine.commands import EngineCommandRegistry
from picard.cli.engine.dispatch import dispatch
from picard.cli.engine.session import LocalEngineSession
from picard.workspace import workspace


class EngineCommandTestCase(PicardTestCase):
    """A registry with the built-in commands and a session over the workspace.

    The session's application is a mock, so waiting for background work returns
    at once and loads and placements are seen synchronously. Work that is split
    in batches to keep a frontend responsive is not, if a batch is cut short by
    its time budget on a slow machine; the budget is made long enough for a
    batch to take it all.
    """

    def setUp(self):
        super().setUp()
        patcher = patch('picard.util.thread._BATCH_TIME_BUDGET', 600.0)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.patch_tagger_instance('picard.item')
        # Moving a file reaches these services; the mock tagger is the services
        # provider in tests.
        self.tagger.acoustid_manager = MagicMock()
        self.tagger.isrc_submit_manager = MagicMock()
        self.tagger.acoustid_client = MagicMock()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.session = LocalEngineSession(MagicMock())
        self.wks = workspace()

    def run_command(self, line):
        return dispatch(self.session, self.reg, line)
