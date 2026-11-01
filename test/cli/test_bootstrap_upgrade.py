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

"""Regression test for PICARD-3446: headless CLI bootstrap must migrate config.

The headless application (HeadlessTagger) must run config upgrades
non-interactively, so an old config file used via picard-cli is migrated rather
than silently left stale (and must never block on an upgrade dialog).

HeadlessTagger is a QCoreApplication subclass, so it runs in a subprocess (only
one Qt application may exist per process, and the suite already runs under a
QApplication).
"""

import os
import subprocess
import sys

from test.picardtestcase import PicardTestCase


# Build a HeadlessTagger against a config file whose stored version is old, then
# print the version after migration. PICARD-3446: the version must be bumped to
# the current one, proving run_config_upgrades ran (non-interactively).
_PROGRAM = """
import sys
from PyQt6 import QtCore

QtCore.QCoreApplication.setApplicationName('MusicBrainz-Picard-headless-test')
QtCore.QCoreApplication.setOrganizationName('MusicBrainz-headless-test')

from picard import PICARD_VERSION
from picard.cli.headless import HeadlessTagger
from picard.config import get_config

config_file = sys.argv[1]
app = HeadlessTagger([], config_file=config_file)
version = get_config().application['version']
print('VERSION=' + str(version))
print('CURRENT=' + str(PICARD_VERSION))
app.run_cleanup()
"""


class HeadlessConfigUpgradeTest(PicardTestCase):
    def test_headless_tagger_migrates_old_config_non_interactively(self):
        config_file = os.path.join(self.mktmpdir(), 'old-config.ini')
        # A plausible old release version; well below the current one, so the
        # upgrade hooks must run and bump the stored version.
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write('[application]\nversion=1.0.0\n')

        result = subprocess.run(
            [sys.executable, '-c', _PROGRAM, config_file],
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

        version = current = None
        for line in result.stdout.splitlines():
            if line.startswith('VERSION='):
                version = line[len('VERSION=') :]
            elif line.startswith('CURRENT='):
                current = line[len('CURRENT=') :]

        self.assertIsNotNone(version)
        self.assertIsNotNone(current)
        # Migration ran: the stale 1.0.0 version was bumped to the current one.
        self.assertNotEqual('1.0.0', version)
        self.assertEqual(current, version)
