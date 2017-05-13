# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (c) 2004 Robert Kaye
# Copyright (C) 2007 Lukáš Lalinský
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

import sys
if sys.platform == 'win32':
    from ctypes import windll

from PyQt5.QtCore import QFile, QIODevice

from picard import config
from picard.util import uniqify

try:
    from libdiscid.compat import discid
except ImportError:
    try:
        import discid
    except ImportError:
        discid = None


DEFAULT_DRIVES = []
if discid is not None:
    device = discid.get_default_device()
    if device:
        DEFAULT_DRIVES.append(device)

LINUX_CDROM_INFO = '/proc/sys/dev/cdrom/info'

# if get_cdrom_drives() lists ALL drives available on the machine
if sys.platform == 'win32':
    AUTO_DETECT_DRIVES = True
elif sys.platform == 'linux2' and QFile.exists(LINUX_CDROM_INFO):
    AUTO_DETECT_DRIVES = True
else:
    # There might be more drives we couldn't detect
    # setting uses a text field instead of a drop-down
    AUTO_DETECT_DRIVES = False


def get_cdrom_drives():
    """List available disc drives on the machine
    """
    # add default drive from libdiscid to the list
    drives = list(DEFAULT_DRIVES)

    if sys.platform == 'win32':
        GetLogicalDrives = windll.kernel32.GetLogicalDrives
        GetDriveType = windll.kernel32.GetDriveTypeW
        DRIVE_CDROM = 5
        mask = GetLogicalDrives()
        for i in range(26):
            if mask >> i & 1:
                drive = chr(i + ord("A")) + ":"
                if GetDriveType(drive) == DRIVE_CDROM:
                    drives.append(drive)

    elif sys.platform == 'linux2' and QFile.exists(LINUX_CDROM_INFO):
        # Read info from /proc/sys/dev/cdrom/info
        cdinfo = QFile(LINUX_CDROM_INFO)
        if cdinfo.open(QIODevice.ReadOnly | QIODevice.Text):
            drive_names = []
            drive_audio_caps = []
            line = string_(cdinfo.readLine())
            while line:
                if ":" in line:
                    key, values = line.split(':')
                    if key == 'drive name':
                        drive_names = values.split()
                    elif key == 'Can play audio':
                        drive_audio_caps = [v == '1' for v in values.split()]
                        break  # no need to continue past this line
                line = string_(cdinfo.readLine())
            # Show only drives that are capable of playing audio
            for index, drive in enumerate(drive_names):
                if drive_audio_caps[index]:
                    device = '/dev/%s' % drive
                    symlink_target = QFile.symLinkTarget(device)
                    if symlink_target != '':
                        device = symlink_target
                    drives.append(device)

    else:
        for device in config.setting["cd_lookup_device"].split(","):
            # Need to filter out empty strings,
            # particularly if the device list is empty
            if device.strip() != '':
                drives.append(device.strip())

    # make sure no drive is listed twice (given by multiple sources)
    return sorted(uniqify(drives))
