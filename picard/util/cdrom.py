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
from PyQt4.QtCore import (QFile, QRegExp)

LINUX_CDROM_INFO = '/proc/sys/dev/cdrom/info' 

if sys.platform == 'win32':
    AUTO_DETECT_DRIVES = True
    from ctypes import windll
    GetLogicalDrives = windll.kernel32.GetLogicalDrives
    GetDriveType = windll.kernel32.GetDriveTypeA
    DRIVE_CDROM = 5

    def get_cdrom_drives():
        drives = []
        mask = GetLogicalDrives()
        for i in range(26):
            if mask >> i & 1:
                drive = chr(i + ord("A")) + ":\\"
                if GetDriveType(drive) == DRIVE_CDROM:
                    drives.append(drive)
        return drives

elif sys.platform == 'linux2' and QFile.exists(LINUX_CDROM_INFO):
    AUTO_DETECT_DRIVES = True
    from PyQt4.QtCore import QIODevice, QString
    
    # Read info from /proc/sys/dev/cdrom/info
    def get_cdrom_drives():
        drives = []
        cdinfo = QFile(LINUX_CDROM_INFO)
        if cdinfo.open(QIODevice.ReadOnly | QIODevice.Text):
            drive_names = []
            drive_audio_caps = []
            line = cdinfo.readLine()
            while not line.isEmpty():
                if line.indexOf(':') != -1:
                    key, values = line.split(':')
                    if key == 'drive name':
                        drive_names = QString(values).trimmed().split(QRegExp("\\s+"), QString.SkipEmptyParts)
                    elif key == 'Can play audio':
                        drive_audio_caps = [v == '1' for v in
                                            QString(values).trimmed().split(QRegExp("\\s+"), QString.SkipEmptyParts)]
                line = cdinfo.readLine()
            # Show only drives that are capable of playing audio
            for drive in drive_names:
                if drive_audio_caps[drive_names.indexOf(drive)]:
                    device = u'/dev/%s' % drive
                    symlink_target = QFile.symLinkTarget(device)
                    if symlink_target != '':
                        device = symlink_target
                    drives.append(device)
        return sorted(drives)

else:
    AUTO_DETECT_DRIVES = False

    def get_cdrom_drives():
        from picard.tagger import Tagger
        tagger = Tagger.instance()
        # Need to filter out empty strings, particularly if the device list is empty
        return filter(lambda string: (string != u''),
                      [d.strip() for d in tagger.config.setting["cd_lookup_device"].split(",")])
