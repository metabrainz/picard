# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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
from PyQt4 import QtGui


class StandardButton(QtGui.QPushButton):

    OK = 0
    CANCEL = 1
    HELP = 2

    __types = {
        OK: (N_('&Ok'), 'SP_DialogOkButton'),
        CANCEL: (N_('&Cancel'), 'SP_DialogCancelButton'),
        HELP: (N_('&Help'), 'SP_DialogHelpButton'),
    }

    def __init__(self, btntype):
        label = _(self.__types[btntype][0])
        args = [label]
        if sys.platform != 'win32' and sys.platform != 'darwin':
            iconname = self.__types[btntype][1]
            if hasattr(QtGui.QStyle, iconname):
                icon = self.tagger.style().standardIcon(getattr(QtGui.QStyle, iconname))
                args = [icon, label]
        QtGui.QPushButton.__init__(self, *args)

