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

"""End-to-end tests for the `picard-cli tag` subcommand.

Run as a subprocess: the command builds a HeadlessTagger (a QCoreApplication),
and only one Qt application may exist per process, so it cannot run in-process
alongside the suite's QApplication.
"""

import os
import subprocess
import sys

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)


def _run_cli(*args, config_file):
    """Invoke `python -m picard.cli <args>` with an isolated config file."""
    return subprocess.run(
        [sys.executable, '-m', 'picard.cli', '-c', config_file, *args],
        capture_output=True,
        text=True,
        # Decode as UTF-8 regardless of the platform's default locale. The CLI
        # output contains non-ASCII characters (e.g. the "✗" error marker), and
        # on macOS CI the default codec is ASCII, which would raise
        # UnicodeDecodeError without this.
        encoding='utf-8',
        timeout=120,
    )


class TagReadCliTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        # Isolated, writable config file so the command never touches the
        # developer's real configuration.
        self.config_file = os.path.join(self.mktmpdir(), 'config.ini')

    def test_read_flac_prints_tags(self):
        flac = get_test_data_path('test.flac')
        result = _run_cli('tag', 'read', flac, config_file=self.config_file)
        self.assertEqual(
            0,
            result.returncode,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        # test.flac has a 'title' tag of 'test'.
        self.assertIn('title: test', result.stdout)
        self.assertIn(os.path.basename(flac), result.stdout)

    def test_read_missing_file_reports_error_and_nonzero_exit(self):
        missing = os.path.join(self.mktmpdir(), 'does-not-exist.flac')
        result = _run_cli('tag', 'read', missing, config_file=self.config_file)
        self.assertEqual(1, result.returncode)
        self.assertIn('Could not read', result.stderr)

    def test_read_multiple_files_continues_after_failure(self):
        flac = get_test_data_path('test.flac')
        missing = os.path.join(self.mktmpdir(), 'nope.flac')
        result = _run_cli('tag', 'read', missing, flac, config_file=self.config_file)
        # One failure -> non-zero exit, but the valid file is still read.
        self.assertEqual(1, result.returncode)
        self.assertIn('title: test', result.stdout)
        self.assertIn('Could not read', result.stderr)
