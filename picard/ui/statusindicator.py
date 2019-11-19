# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Philipp Wolfer
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

from picard.const.sys import IS_WIN


DesktopStatusIndicator = None

if IS_WIN:
    from PyQt5.QtWinExtras import QWinTaskbarButton

    class WindowsTaskbarStatusIndicator:
        def __init__(self, window):
            self.max_pending = 0
            taskbar_button = QWinTaskbarButton(window)
            taskbar_button.setWindow(window)
            self.progress = taskbar_button.progress()

        def update(self, files=0, albums=0, pending_files=0, pending_requests=0):
            if not self.progress:
                return

            total_pending = pending_files + pending_requests

            if total_pending > self.max_pending:
                self.max_pending = total_pending

            if total_pending == 0 or self.max_pending <= 1:  # No need to show progress for single item
                self.max_pending = 0
                self.progress.hide()
                return

            completion = 1 - (total_pending / self.max_pending)
            self.progress.setValue(int(completion * 100))
            self.progress.show()

    DesktopStatusIndicator = WindowsTaskbarStatusIndicator
