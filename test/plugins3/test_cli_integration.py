# -*- coding: utf-8 -*-
#
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import subprocess
import sys
import unittest


class TestCliIntegration(unittest.TestCase):
    """Integration tests that run picard-cli in a subprocess.

    These tests verify the actual startup path works end-to-end,
    without mocking, to catch regressions like PICARD-3300.
    """

    def test_cli_starts_without_crash(self):
        """picard-cli -V must not crash during minimal_init (PICARD-3300)."""
        result = subprocess.run(
            [sys.executable, '-m', 'picard.plugin3.cli', '-V'],
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr.decode())
