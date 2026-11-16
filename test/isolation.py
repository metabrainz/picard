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

"""Keep the tests away from the files of the user.

Importing this module points the environment to a temporary directory. It is
imported first by ``test/__init__.py``, which runs before ``test/conftest.py``
and imports Picard (and all the test modules): anything resolving a path
while it is imported must already see the temporary directory.
"""

import atexit
import os
from pathlib import Path
import shutil
import sys
import tempfile


def isolate_user_environment() -> Path:
    """Point everything that locates the files of the user to a temporary directory.

    Tests must never read or write the real configuration, plugins or
    music folder of whoever runs them. The in-process tests use a fake config,
    but a subprocess (or anything resolving a path through Qt) inherits the
    environment, so it is the environment that has to be isolated.

    This runs when this module is imported, before Picard is: every
    pytest-xdist worker imports it too, and gets a directory of its own.
    """
    root = Path(tempfile.mkdtemp(prefix='picard-test-'))
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    variables = {
        'PICARD_CONFIG_DIR': root / 'picard-config',
        'PICARD_CACHE_DIR': root / 'picard-cache',
        'PICARD_PLUGIN_DIR': root / 'picard-plugins',
    }
    if sys.platform.startswith('linux'):
        # Qt honours these on Linux only (Windows and macOS ask the system for
        # the folders of the user), so the Picard variables above are what
        # protects the other platforms.
        home = root / 'home'
        home.mkdir()
        variables.update(
            {
                'HOME': home,
                'XDG_CONFIG_HOME': home / '.config',
                'XDG_DATA_HOME': home / '.local' / 'share',
                'XDG_CACHE_HOME': home / '.cache',
                'XDG_STATE_HOME': home / '.local' / 'state',
            }
        )
    for name, path in variables.items():
        os.environ[name] = str(path)
    return root


USER_ENVIRONMENT_ROOT = isolate_user_environment()
