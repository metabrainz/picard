# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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
import os.path
from PyQt5 import QtGui

if sys.platform == 'win32':
    _search_paths = []
else:
    _search_paths = [
        os.path.expanduser('~/.icons'),
        os.path.join(os.environ.get('XDG_DATA_DIRS', '/usr/share'), 'icons'),
        '/usr/share/pixmaps',
    ]

_current_theme = None
if 'XDG_CURRENT_DESKTOP' in os.environ:
    desktop = os.environ['XDG_CURRENT_DESKTOP'].lower()
    if desktop in ('gnome', 'unity'):
        _current_theme = (os.popen('gsettings get org.gnome.desktop.interface icon-theme').read().strip()[1:-1]
                          or None)
elif os.environ.get('KDE_FULL_SESSION'):
    _current_theme = (os.popen("kreadconfig --file kdeglobals --group Icons --key Theme --default crystalsvg").read().strip()
                      or None)


ICON_SIZE_MENU = ('16x16',)
ICON_SIZE_TOOLBAR = ('22x22',)
ICON_SIZE_ALL = ('22x22', '16x16')


def lookup(name, size=ICON_SIZE_ALL):
    icon = QtGui.QIcon()
    if _current_theme:
        for path in _search_paths:
            for subdir in ('actions', 'places', 'devices'):
                fullpath = os.path.join(path, _current_theme, size[0], subdir, name)
                if os.path.exists(fullpath + '.png'):
                    icon.addFile(fullpath + '.png')
                    for s in size[1:]:
                        icon.addFile(os.path.join(path, _current_theme, s, subdir, name) + '.png')
                    return icon
    for s in size:
        icon.addFile('/'.join([':', 'images', s, name]) + '.png')
    return icon
