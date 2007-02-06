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

try:
    import win32file
except ImportError:
    def get_cdrom_drives():
        from picard.tagger import Tagger
        tagger = Tagger.instance()
        return [d.strip() for d in tagger.config.setting["cd_lookup_device"].split(",")]
else:
    def get_cdrom_drives():
        drives = []
        mask = win32file.GetLogicalDrives()
        for i in range(26):
            if mask >> i & 1:
                drive = unicode(chr(i + ord("A"))) + u":\\"
                if win32file.GetDriveType(drive) == win32file.DRIVE_CDROM:
                    drives.append(drive)
        return drives
