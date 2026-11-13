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

"""Commands report a timeout while waiting for background work.

``run_until_idle`` returns False when the work did not finish in time. The
commands used to ignore that, so e.g. a save that was still running was
reported as ``saved``. They now say the result may be incomplete.
"""

from unittest.mock import (
    MagicMock,
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase
from test.cli.engine.test_disc_command import _run_task_inline

from picard.album import Album
from picard.cli.engine.dispatch import dispatch
from picard.cli.engine.session import LocalEngineSession
from picard.cluster import Cluster
import picard.disc
from picard.disc.presentation import disc_presentation
from picard.file import File


_MBID = '1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d'


class _TimeoutTestBase(EngineCommandTestCase):
    drained = False

    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'query_limit': 25})
        self.tagger.mb_api = MagicMock()
        # The application whose idle wait says whether the work finished in time.
        app = MagicMock()
        app.run_until_idle.return_value = self.drained
        self.session = LocalEngineSession(app)


class TimedOutCommandsTest(_TimeoutTestBase):
    drained = False

    def test_album_load_pending_when_release_not_loaded_in_time(self):
        album = Album(_MBID)
        with patch.object(self.wks, 'load_album', return_value=album):
            result = dispatch(self.session, self.reg, f'album load {_MBID}')
        self.assertTrue(result.ok)
        self.assertEqual('pending', result.items[0].status)
        self.assertIn('timed out', result.message)

    def test_save_reports_files_still_saving_as_pending(self):
        f = File('a.flac')
        self.wks.files[f.filename] = f
        self.wks.unclustered_files.add_file(f)
        handle = self.session.handle_for(f)

        def start_save(*args, **kwargs):
            f.state = File.State.PENDING

        with patch.object(File, 'save', start_save):
            result = dispatch(self.session, self.reg, f'save {handle}')
        self.assertEqual(['pending'], [it.status for it in result.items])
        self.assertIn('timed out', result.message)

    def test_cluster_lookup_without_reply_is_timeout_not_no_matches(self):
        self.wks.clusters.append(Cluster('Album', 'Artist'))
        # The search request is sent but never answered.
        self.tagger.mb_api.find_releases.return_value = MagicMock()
        result = dispatch(self.session, self.reg, 'cluster lookup')
        self.assertEqual('timeout', result.items[0].status)
        self.assertIn('timed out', result.message)

    def test_disc_lookup_without_reply_is_timeout_not_no_match(self):
        def fake_read_log(self_disc, path):
            self_disc.id = 'disc-xyz'

        with (
            patch.object(picard.disc, 'discid', MagicMock()),
            patch.object(picard.disc.Disc, 'read_log', fake_read_log),
            patch.object(picard.disc.Disc, 'lookup', lambda self_disc: None),
            patch('picard.disc.thread.run_task', side_effect=_run_task_inline),
        ):
            disc_presentation().reset_last_loaded()
            result = dispatch(self.session, self.reg, 'disc read-log some.log')
        self.assertEqual('timeout', result.items[0].status)
        self.assertIn('timed out', result.message)


class DrainedCommandsTest(_TimeoutTestBase):
    drained = True

    def test_no_timeout_message_when_work_finished(self):
        album = Album(_MBID)
        with patch.object(self.wks, 'load_album', return_value=album):
            result = dispatch(self.session, self.reg, f'album load {_MBID}')
        self.assertEqual('loaded', result.items[0].status)
        self.assertEqual('', result.message)
