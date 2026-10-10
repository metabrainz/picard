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

"""Tests for the fpcalc result handling after migration to
ExternalCommandRunner.

These exercise AcoustIDClient's success/error callbacks directly with a
synthetic CommandResult/CommandError, which is deterministic and does not spawn
a process or require a Qt event loop (the runner itself is covered by
test/util/test_externalcommand.py). The key behaviour preserved from the old
QProcess implementation is:

* exit code 0  -> fingerprint delivered AND stored on the file,
* exit code 3  -> fingerprint delivered (usable) but NOT stored (decode errors),
* failure      -> None delivered to the callback.
"""

from collections import namedtuple
from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.acoustid import (
    AcoustIDClient,
    FpcalcExit,
)
from picard.util.externalcommand import (
    CommandError,
    CommandResult,
)


_FPCALC_JSON = '{"duration": 123.9, "fingerprint": "ABCDEF"}'

Task = namedtuple('Task', ('file', 'next_func'))


class FpcalcCallbackTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.acoustid')
        self.client = AcoustIDClient(object())

    def _task(self):
        file = Mock()
        file.set_acoustid_fingerprint = Mock()
        next_func = Mock()
        return Task(file, next_func)

    def _result(self, returncode):
        return CommandResult(
            args=('fpcalc',),
            returncode=returncode,
            stdout=_FPCALC_JSON,
            stderr='decode warning' if returncode == FpcalcExit.DECODING_ERROR else '',
        )

    def test_success_delivers_and_stores_fingerprint(self):
        task = self._task()
        self.client._on_fpcalc_success(task, self._result(FpcalcExit.NOERROR))
        task.next_func.assert_called_once_with(('fingerprint', 'ABCDEF', 123))
        task.file.set_acoustid_fingerprint.assert_called_once_with('ABCDEF', 123)

    def test_decoding_error_delivers_but_does_not_store(self):
        task = self._task()
        self.client._on_fpcalc_success(task, self._result(FpcalcExit.DECODING_ERROR))
        # Fingerprint still delivered to the caller...
        task.next_func.assert_called_once_with(('fingerprint', 'ABCDEF', 123))
        # ...but not stored on the file (would risk submitting a bad fingerprint).
        task.file.set_acoustid_fingerprint.assert_not_called()

    def test_error_delivers_none(self):
        task = self._task()
        error = CommandError('fpcalc failed', args_list=('fpcalc',), returncode=2, stderr='bad')
        self.client._on_fpcalc_error(task, error)
        task.next_func.assert_called_once_with(None)
        task.file.set_acoustid_fingerprint.assert_not_called()

    def test_malformed_output_delivers_none(self):
        task = self._task()
        bad = CommandResult(args=('fpcalc',), returncode=0, stdout='not json', stderr='')
        self.client._on_fpcalc_success(task, bad)
        task.next_func.assert_called_once_with(None)
        task.file.set_acoustid_fingerprint.assert_not_called()
