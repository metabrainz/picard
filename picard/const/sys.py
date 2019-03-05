# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Laurent Monin
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

IS_WIN = sys.platform == 'win32'
IS_LINUX = sys.platform == 'linux'
IS_MACOS = sys.platform == 'darwin'

# These variables are set by pyinstaller if running from a packaged build
# See http://pyinstaller.readthedocs.io/en/stable/runtime-information.html
IS_FROZEN = getattr(sys, 'frozen', False)
FROZEN_TEMP_PATH = getattr(sys, '_MEIPASS', '')
