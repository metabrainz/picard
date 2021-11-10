# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Philipp Wolfer
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


import io
from typing import Iterable
import unittest

from test.picardtestcase import PicardTestCase

from picard.const.sys import IS_WIN
from picard.util import cdrom


MOCK_CDROM_INFO = """CD-ROM information, Id: cdrom.c 3.20 2003/12/17

drive name:		sr1	sr0
drive speed:		24	24
drive # of slots:	1	1
Can close tray:		0	1
Can open tray:		1	1
Can lock tray:		1	1
Can change speed:	1	1
Can select disk:	0	0
Can read multisession:	1	1
Can read MCN:		1	1
Reports media changed:	1	1
Can play audio:		1	0
Can write CD-R:		1	1
Can write CD-RW:	1	1
Can read DVD:		1	1
Can write DVD-R:	1	1
Can write DVD-RAM:	1	1
Can read MRW:		1	1
Can write MRW:		1	1
Can write RAM:		1	1
"""

MOCK_CDROM_INFO_EMPTY = """CD-ROM information, Id: cdrom.c 3.20 2003/12/17

drive name:
drive speed:
drive # of slots:
Can close tray:
Can open tray:
Can lock tray:
Can change speed:
Can select disk:
Can read multisession:
Can read MCN:
Reports media changed:
Can play audio:
Can write CD-R:
Can write CD-RW:
Can read DVD:
Can write DVD-R:
Can write DVD-RAM:
Can read MRW:
Can write MRW:
Can write RAM:
"""


class LinuxParseCdromInfoTest(PicardTestCase):

    def test_drives(self):
        with io.StringIO(MOCK_CDROM_INFO) as f:
            drives = list(cdrom._parse_linux_cdrom_info(f))
            self.assertEqual([('sr1', True), ('sr0', False)], drives)

    def test_empty(self):
        with io.StringIO(MOCK_CDROM_INFO_EMPTY) as f:
            drives = list(cdrom._parse_linux_cdrom_info(f))
            self.assertEqual([], drives)

    def test_empty_string(self):
        with io.StringIO("") as f:
            drives = list(cdrom._parse_linux_cdrom_info(f))
            self.assertEqual([], drives)


class GetCdromDrivesTest(PicardTestCase):

    def test_get_cdrom_drives(self):
        self.set_config_values({"cd_lookup_device": "/dev/cdrom"})
        self.assertIsInstance(cdrom.get_cdrom_drives(), Iterable)


@unittest.skipUnless(IS_WIN, "windows test")
class WindowsGetCdromDrivesTest(PicardTestCase):

    def test_autodetect(self):
        self.assertTrue(cdrom.AUTO_DETECT_DRIVES)

    def test_iter_drives(self):
        drives = cdrom._iter_drives()
        self.assertIsInstance(drives, Iterable)
        # This should not raise
        list(drives)
