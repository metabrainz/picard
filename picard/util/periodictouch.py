# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 Philipp Wolfer
# Copyright (C) 2022-2024 Laurent Monin
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


from pathlib import Path

from PySide6.QtCore import QTimer

from picard import log


TOUCH_FILES_DELAY_SECONDS = 4 * 3600

_touch_timer = QTimer()
_files_to_touch = set()


def register_file(filepath):
    if _touch_timer.isActive():
        _files_to_touch.add(filepath)


def unregister_file(filepath):
    if _touch_timer.isActive():
        _files_to_touch.discard(filepath)


def enable_timer():
    log.debug("Setup timer for touching files every %i seconds", TOUCH_FILES_DELAY_SECONDS)
    _touch_timer.timeout.connect(_touch_files)
    _touch_timer.start(TOUCH_FILES_DELAY_SECONDS * 1000)


def _touch_files():
    log.debug("Touching %i files", len(_files_to_touch))
    for filepath in _files_to_touch.copy():
        path = Path(filepath)
        if path.exists():
            try:
                path.touch()
            except OSError:
                log.error("error touching file `%s`", filepath, exc_info=True)
        else:
            unregister_file(filepath)
