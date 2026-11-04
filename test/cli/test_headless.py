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

"""Tests for the headless application object.

HeadlessTagger is a QCoreApplication subclass, and only one Qt application may
exist per process. The shared test suite already runs under a QApplication
(pytest-qt / the qapp fixture), so HeadlessTagger cannot be instantiated in
the same process. These tests therefore exercise it in a fresh subprocess.
"""

import subprocess
import sys

from test.picardtestcase import PicardTestCase


# Program run in a clean subprocess: build a HeadlessTagger and assert the
# services are wired, the services provider is installed, ProxyToMainEvent is
# dispatched, and cleanup runs. Prints OK lines the parent test checks for.
_SUBPROCESS_PROGRAM = """
import sys
from PyQt6 import QtCore

QtCore.QCoreApplication.setApplicationName('MusicBrainz-Picard-headless-test')
QtCore.QCoreApplication.setOrganizationName('MusicBrainz-headless-test')

from picard.cli.headless import HeadlessTagger
from picard.services import services
from picard.util import thread
from picard.workspace import workspace

app = HeadlessTagger(sys.argv, config_file=None)

# All services are present and identical to the view resolved via services().
for name in (
    'format_registry', 'mb_api', 'webservice',
    'acoustid_client', 'acoustid_manager', 'isrc_submit_manager',
):
    assert getattr(services(), name) is getattr(app, name), name
print('SERVICES_OK')

# The default formats are registered.
assert services().format_registry.supported_extensions(), 'no formats registered'
print('FORMATS_OK')

# ProxyToMainEvent (how thread-pool callbacks return to the main thread) runs.
hits = []
app.event(thread.ProxyToMainEvent(lambda: hits.append(1)))
assert hits == [1], hits
print('EVENT_OK')

# Save bookkeeping surface exists and flush is a no-op with no dirty parents.
assert app.stopping is False
assert app.files == {}
assert workspace()._saving_files_count == 0
workspace().flush_saving_image_parents()
print('BOOKKEEPING_OK')

app.run_cleanup()
print('CLEANUP_OK')
"""


_LAZY_PROGRAM = """
import sys
from PyQt6 import QtCore

QtCore.QCoreApplication.setApplicationName('MusicBrainz-Picard-headless-test')
QtCore.QCoreApplication.setOrganizationName('MusicBrainz-headless-test')

from picard.cli.headless import HeadlessTagger

app = HeadlessTagger(sys.argv, config_file=None)

# Nothing is built at construction time.
assert app._webservice is None
assert app._mb_api is None
assert app._format_registry is None
assert app._acoustid_client is None
assert app._acoustid_manager is None
assert app._isrc_submit_manager is None
print('LAZY_UNBUILT_OK')

# Touching the format registry must NOT build the web service / acoustid.
app.format_registry
assert app._format_registry is not None
assert app._webservice is None, 'format_registry must not build the web service'
assert app._acoustid_client is None
print('LAZY_ISOLATED_OK')

# Draining the (idle) event loop must not build the web service either.
app.run_until_idle(timeout=5)
assert app._webservice is None, 'run_until_idle must not build the web service'
print('LAZY_IDLE_OK')

# mb_api pulls in the web service; caching returns the same instances.
assert app.mb_api is app.mb_api
assert app._webservice is not None
print('LAZY_BUILD_OK')

app.run_cleanup()
"""


_DRIVER_PROGRAM = """
import sys
from PyQt6 import QtCore

QtCore.QCoreApplication.setApplicationName('MusicBrainz-Picard-headless-test')
QtCore.QCoreApplication.setOrganizationName('MusicBrainz-headless-test')

from picard.cli.headless import HeadlessTagger
from picard.util import thread

app = HeadlessTagger(sys.argv, config_file=None)

# Schedule a background task whose completion callback runs on the main thread
# via ProxyToMainEvent. run_until_idle() must pump the event loop so the task
# runs, drains, and the callback fires.
state = {'ran': False, 'result': None}

def work():
    return 21 * 2

def done(result=None, error=None):
    state['ran'] = True
    state['result'] = result

thread.run_task(work, done, thread_pool=app.thread_pool)

drained = app.run_until_idle(timeout=30)
assert drained, 'run_until_idle timed out'
assert state['ran'], 'completion callback did not run'
assert state['result'] == 42, state['result']
print('DRIVER_OK')

# With no work queued, run_until_idle returns promptly.
assert app.run_until_idle(timeout=5) is True
print('IDLE_OK')

app.run_cleanup()
"""


_POST_SAVE_PROGRAM = """
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from PyQt6 import QtCore

QtCore.QCoreApplication.setApplicationName('MusicBrainz-Picard-headless-test')
QtCore.QCoreApplication.setOrganizationName('MusicBrainz-headless-test')

from picard.cli.headless import HeadlessTagger
from picard.config import get_config
from picard.file import run_file_post_save_processors
from picard.workspace import workspace

# Isolated config so the test neither reads nor persists shared settings.
config_dir = tempfile.TemporaryDirectory()
app = HeadlessTagger(sys.argv, config_file=str(Path(config_dir.name) / 'picard.ini'))

album = SimpleNamespace(
    id='rel-1',
    is_complete=lambda: True,
    get_num_unsaved_files=lambda: 0,
)
file = SimpleNamespace(parent_item=SimpleNamespace(album=album))
wks = workspace()
wks.albums['rel-1'] = album
removed = []
wks.remove = removed.append

# Setting off (the default): a complete, fully saved album is kept.
run_file_post_save_processors(file)
assert removed == [], removed
print('KEPT_OK')

# Setting on: the post-save processor removes it straight from the workspace.
get_config().setting['remove_complete_albums_after_save'] = True
run_file_post_save_processors(file)
assert removed == [[album]], removed
print('REMOVED_OK')

app.run_cleanup()
config_dir.cleanup()
"""


_QT_MESSAGE_PROGRAM = """
import sys
from PyQt6 import QtCore

QtCore.QCoreApplication.setApplicationName('MusicBrainz-Picard-headless-test')
QtCore.QCoreApplication.setOrganizationName('MusicBrainz-headless-test')

from picard.cli.headless import HeadlessTagger

app = HeadlessTagger(sys.argv, config_file=None)

# A known-benign Qt-internal warning is dropped, any other one is kept.
QtCore.qWarning('QIODevice::read (QSslSocket): device not open')
QtCore.qWarning('some other Qt warning')

app.run_cleanup()
"""


class HeadlessTaggerSubprocessTest(PicardTestCase):
    def test_qt_messages_go_through_the_message_handler(self):
        result = subprocess.run(
            [sys.executable, '-c', _QT_MESSAGE_PROGRAM],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120,
        )
        self.assertEqual(
            0,
            result.returncode,
            msg=f"subprocess failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        output = result.stdout + result.stderr
        self.assertNotIn('device not open', output)
        self.assertIn('some other Qt warning', output)

    def test_remove_complete_albums_after_save_works_headless(self):
        result = subprocess.run(
            [sys.executable, '-c', _POST_SAVE_PROGRAM],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120,
        )
        self.assertEqual(
            0,
            result.returncode,
            msg=f"subprocess failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        for marker in ('KEPT_OK', 'REMOVED_OK'):
            self.assertIn(marker, result.stdout)

    def test_headless_tagger_boots_and_wires_services(self):
        result = subprocess.run(
            [sys.executable, '-c', _SUBPROCESS_PROGRAM],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120,
        )
        self.assertEqual(
            0,
            result.returncode,
            msg=f"subprocess failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        for marker in ('SERVICES_OK', 'FORMATS_OK', 'EVENT_OK', 'BOOKKEEPING_OK', 'CLEANUP_OK'):
            self.assertIn(marker, result.stdout)

    def test_run_until_idle_drives_background_task_to_completion(self):
        result = subprocess.run(
            [sys.executable, '-c', _DRIVER_PROGRAM],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120,
        )
        self.assertEqual(
            0,
            result.returncode,
            msg=f"subprocess failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        for marker in ('DRIVER_OK', 'IDLE_OK'):
            self.assertIn(marker, result.stdout)

    def test_services_are_built_lazily(self):
        result = subprocess.run(
            [sys.executable, '-c', _LAZY_PROGRAM],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120,
        )
        self.assertEqual(
            0,
            result.returncode,
            msg=f"subprocess failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        for marker in ('LAZY_UNBUILT_OK', 'LAZY_ISOLATED_OK', 'LAZY_IDLE_OK', 'LAZY_BUILD_OK'):
            self.assertIn(marker, result.stdout)
