# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2023 Philipp Wolfer
# Copyright (C) 2020 Julius Michaelis
# Copyright (C) 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2021 Gabriel Ferreira
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from picard import log
from picard.const.sys import (
    IS_HAIKU,
    IS_MACOS,
    IS_WIN,
)


DesktopStatusIndicator = None


class ProgressStatus:
    def __init__(self, files=0, albums=0, pending_files=0, pending_requests=0, progress=0):
        self.files = files
        self.albums = albums
        self.pending_files = pending_files
        self.pending_requests = pending_requests
        self.progress = progress


class AbstractProgressStatusIndicator:
    def __init__(self):
        self._max_pending = 0
        self._last_pending = 0

    def update(self, progress_status):
        if not self.is_available:
            return

        total_pending = progress_status.pending_files + progress_status.pending_requests
        if total_pending == self._last_pending:
            return  # No changes, avoid update

        previous_done = self._max_pending - self._last_pending
        self._max_pending = max(self._max_pending, previous_done + total_pending)
        self._last_pending = total_pending

        if total_pending == 0 or self._max_pending <= 1:  # No need to show progress for single item
            self._max_pending = 0
            self.hide_progress()
            return

        self.set_progress(progress_status.progress)

    @property
    def is_available(self):
        return True

    def hide_progress(self):
        raise NotImplementedError

    def set_progress(self, progress: float):
        raise NotImplementedError


if IS_WIN:
    try:
        from .windows import WindowsTaskbarStatusIndicator

        DesktopStatusIndicator = WindowsTaskbarStatusIndicator

    except Exception as err:
        log.warning('Failed importing Windows status indicator: %r', err)

elif not (IS_WIN or IS_MACOS or IS_HAIKU):
    try:
        from .unity import UnityLauncherEntryStatusIndicator

        DesktopStatusIndicator = UnityLauncherEntryStatusIndicator

    except Exception as err:
        log.warning('Failed importing DBus status indicator: %r', err)
