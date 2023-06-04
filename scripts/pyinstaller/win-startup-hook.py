# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019, 2021, 2023 Philipp Wolfer
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


from ctypes import windll
import os
import os.path
import sys


# On Windows try to attach to the console as early as possible in order
# to get stdout / stderr logged to console. This needs to happen before
# logging gets imported.
# See https://stackoverflow.com/questions/54536/win32-gui-app-that-writes-usage-text-to-stdout-when-invoked-as-app-exe-help
if windll.kernel32.AttachConsole(-1):
    sys.stdout = open('CON', 'w')
    sys.stderr = open('CON', 'w')

# Ensure bundled DLLs are loaded
os.environ['PATH'] = os.pathsep.join((
    os.path.normpath(sys._MEIPASS),
    os.path.normpath(os.path.join(sys._MEIPASS, 'PyQt5\\Qt5\\bin')),
    os.environ['PATH'],
))
