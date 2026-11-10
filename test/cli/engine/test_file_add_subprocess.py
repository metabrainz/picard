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

"""End-to-end test for the `file add` + `ls` engine commands.

Runs in a subprocess: the engine builds a HeadlessTagger (a QCoreApplication),
and only one Qt application may exist per process while the suite already runs
under a QApplication. See test/cli/test_headless.py for the same pattern.
"""

import os
import subprocess
import sys

from test.picardtestcase import PicardTestCase


_TEST_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'test.mp3')

# Build a headless session, add a real audio file, then ls — asserting the file
# was loaded (minted an f-handle) and appears in the listing. Prints markers.
_PROGRAM = """
import json
import sys

from picard.cli.headless import HeadlessTagger
from picard.cli.engine.builtins import register_builtins
from picard.cli.engine.commands import EngineCommandRegistry
from picard.cli.engine.dispatch import dispatch
from picard.cli.engine.session import LocalEngineSession

test_file = sys.argv[1]
app = HeadlessTagger([])
try:
    registry = EngineCommandRegistry()
    register_builtins(registry)
    session = LocalEngineSession(app)

    add = dispatch(session, registry, 'file add ' + repr(test_file))
    if add.ok and len(add.mints) == 1 and add.mints[0].startswith('f'):
        print('ADD_OK', add.mints[0])

    # The added file must be enumerable and listed by ls with the same handle.
    listing = dispatch(session, registry, 'ls')
    handles = [it.handle for it in listing.items]
    if add.mints[0] in handles:
        print('LS_OK')

    # ls f* resolves to exactly the added file.
    only_files = dispatch(session, registry, 'ls f*')
    if [it.handle for it in only_files.items] == add.mints:
        print('LS_SELECTOR_OK')

    # Result is JSON-serializable.
    json.dumps(add.to_dict())
    print('SERIALIZABLE_OK')
finally:
    app.run_cleanup()
"""


# Add a (copied) file then save it; asserts the save reports success. Uses a
# temp copy because saving writes tags to disk.
_SAVE_PROGRAM = """
import shutil
import sys
import tempfile

from picard.cli.headless import HeadlessTagger
from picard.cli.engine.builtins import register_builtins
from picard.cli.engine.commands import EngineCommandRegistry
from picard.cli.engine.dispatch import dispatch
from picard.cli.engine.session import LocalEngineSession

src = sys.argv[1]
tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
tmp.close()
shutil.copy(src, tmp.name)

app = HeadlessTagger([])
try:
    registry = EngineCommandRegistry()
    register_builtins(registry)
    session = LocalEngineSession(app)

    add = dispatch(session, registry, 'file add ' + repr(tmp.name))
    if add.ok and add.mints:
        print('ADD_OK')

    result = dispatch(session, registry, 'save f*')
    if result.ok and result.items and all(it.status == 'saved' for it in result.items):
        print('SAVE_OK', len(result.items))
finally:
    app.run_cleanup()
    import os
    os.unlink(tmp.name)
"""


class FileAddSubprocessTest(PicardTestCase):
    def test_file_add_then_ls(self):
        result = subprocess.run(
            [sys.executable, '-c', _PROGRAM, os.path.abspath(_TEST_FILE)],
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
        for marker in ('ADD_OK', 'LS_OK', 'LS_SELECTOR_OK', 'SERIALIZABLE_OK'):
            self.assertIn(marker, result.stdout)

    def test_add_then_save(self):
        result = subprocess.run(
            [sys.executable, '-c', _SAVE_PROGRAM, os.path.abspath(_TEST_FILE)],
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
        self.assertIn('ADD_OK', result.stdout)
        self.assertIn('SAVE_OK', result.stdout)
