# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2008 Will
# Copyright (C) 2008, 2018-2021 Philipp Wolfer
# Copyright (C) 2009 david
# Copyright (C) 2013 Johannes Dewender
# Copyright (C) 2013 Sebastian Ramacher
# Copyright (C) 2013, 2018-2021, 2023-2024 Laurent Monin
# Copyright (C) 2013-2014 Michael Wiencek
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2022 Bob Swift
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


import os.path

from picard import log
from picard.config import get_config
from picard.const.sys import (
    IS_LINUX,
    IS_WIN,
)


try:
    from libdiscid.compat import discid
except ImportError:
    try:
        import discid
    except (ImportError, OSError):
        discid = None


DISCID_NOT_LOADED_MESSAGE = "CDROM: discid library not found - Lookup CD functionality disabled"
LINUX_CDROM_INFO = '/proc/sys/dev/cdrom/info'


def get_default_cdrom_drives():
    default_drives = []
    if discid is not None:
        device = discid.get_default_device()
        if device:
            default_drives.append(device)
    return default_drives


def _generic_iter_drives():
    config = get_config()
    yield from (
        device.strip() for device
        in config.setting['cd_lookup_device'].split(',')
        if device and not device.isspace()
    )


def _parse_linux_cdrom_info(f):
    drive_names = []
    drive_audio_caps = []
    DRIVE_NAME = 'drive name:'
    CAN_PLAY_AUDIO = 'Can play audio:'
    for line in f:
        if line.startswith(DRIVE_NAME):
            drive_names = line[len(DRIVE_NAME):].split()
            break
    if drive_names:
        for line in f:
            if line.startswith(CAN_PLAY_AUDIO):
                drive_audio_caps = [v == '1' for v in line[len(CAN_PLAY_AUDIO):].split()]
                break
    yield from zip(drive_names, drive_audio_caps)


if IS_WIN:
    from ctypes import windll

    AUTO_DETECT_DRIVES = True
    DRIVE_TYPE_CDROM = 5

    def _iter_drives():
        GetLogicalDrives = windll.kernel32.GetLogicalDrives
        GetDriveType = windll.kernel32.GetDriveTypeW
        mask = GetLogicalDrives()
        for i in range(26):
            if mask >> i & 1:
                drive = chr(i + ord('A')) + ':'
                if GetDriveType(drive) == DRIVE_TYPE_CDROM:
                    yield drive

elif IS_LINUX and os.path.isfile(LINUX_CDROM_INFO):
    AUTO_DETECT_DRIVES = True

    def _iter_drives():
        # Read info from /proc/sys/dev/cdrom/info
        with open(LINUX_CDROM_INFO, 'r') as f:
            # Show only drives that are capable of playing audio
            yield from (
                os.path.realpath('/dev/%s' % drive)
                for drive, can_play_audio in _parse_linux_cdrom_info(f)
                if can_play_audio
            )

else:
    # There might be more drives we couldn't detect
    # setting uses a text field instead of a drop-down
    AUTO_DETECT_DRIVES = False
    _iter_drives = _generic_iter_drives


def get_cdrom_drives():
    """List available disc drives on the machine
    """
    # add default drive from libdiscid to the list
    from picard.const.defaults import DEFAULT_DRIVES
    drives = set(DEFAULT_DRIVES)
    try:
        drives |= set(_iter_drives())
    except OSError as error:
        log.error(error)
    return sorted(drives)
