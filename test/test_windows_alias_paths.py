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

"""Tests using real Windows alias paths for the same file (PICARD-3573).

A file on a network share can be reached via its UNC path (`\\\\server\\share\\...`)
and via a mapped drive letter (`X:\\...`). To get the same situation on a CI
machine without a network, a temporary directory is made available as
 - a drive letter, created with `subst`
 - a UNC path using the administrative share of the local volume (`\\\\localhost\\C$\\...`)
"""

import os
import string
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.const.sys import IS_WIN
from picard.file import File
from picard.metadata import Metadata
from picard.util.filenaming import is_same_file_location


def _free_drive_letter():
    for letter in reversed(string.ascii_uppercase[3:]):  # Z: down to D:
        if not os.path.exists(f'{letter}:\\'):
            return letter
    return None


@unittest.skipUnless(IS_WIN, "Windows test")
class WindowsAliasPathsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = os.path.realpath(tmp.name)
        drive, rest = os.path.splitdrive(self.root)

        # UNC path via administrative share of the volume
        self.unc_root = '\\\\localhost\\' + drive[0] + '$' + rest
        if not os.path.isdir(self.unc_root):
            self.skipTest("Administrative share %r not accessible" % self.unc_root)

        # Drive letter pointing to the same directory
        letter = _free_drive_letter()
        if not letter:
            self.skipTest("No free drive letter available")
        try:
            subprocess.run(['subst', f'{letter}:', self.root], check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError) as why:
            self.skipTest("subst failed: %s" % why)
        self.addCleanup(subprocess.run, ['subst', f'{letter}:', '/d'], check=False, capture_output=True)
        self.drive_root = f'{letter}:\\'

        self.unc_file = os.path.join(self.unc_root, 'song.mp3')
        self.drive_file = os.path.join(self.drive_root, 'song.mp3')
        with open(os.path.join(self.root, 'song.mp3'), 'wb') as f:
            f.write(b'data')

    def test_is_same_file_location(self):
        self.assertNotEqual(self.unc_file, self.drive_file)
        self.assertTrue(is_same_file_location(self.unc_file, self.drive_file))

    def test_is_same_file_location_different_name(self):
        other = os.path.join(self.drive_root, 'other.mp3')
        with open(other, 'wb') as f:
            f.write(b'data')
        self.assertFalse(is_same_file_location(self.unc_file, other))

    def test_rename_does_not_move_alias_path(self):
        file = File(self.unc_file)
        file.make_filename = Mock(return_value=self.drive_file)
        result = file._rename(self.unc_file, Metadata(), {'move_overwrite_existing_files': False})
        self.assertEqual(self.unc_file, result)
        self.assertTrue(os.path.isfile(os.path.join(self.root, 'song.mp3')))
        self.assertEqual(['song.mp3'], os.listdir(self.root))

    def test_is_same_directory(self):
        self.assertTrue(File._is_same_directory(self.unc_root, self.drive_root))
