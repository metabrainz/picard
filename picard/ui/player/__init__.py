# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Timur Enikeev
# Copyright (C) 2019-2023, 2026 Philipp Wolfer
# Copyright (C) 2019-2025 Laurent Monin
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
from PyQt6.QtCore import QObject

from picard import log
from picard.config import get_config
from picard.const.sys import (
    IS_HAIKU,
    IS_MACOS,
    IS_WIN,
)


try:
    from PyQt6 import QtMultimedia  # noqa: F401
except ImportError as e:
    qt_multimedia_available = False
    qt_multimedia_errmsg = e.msg
else:
    qt_multimedia_available = True
    qt_multimedia_errmsg = None


from typing import TYPE_CHECKING


if TYPE_CHECKING:
    # Import conditionally to avoid runtime errors if QtMultimedia is unavailable
    from .player import Player


OS_SUPPORTS_NOW_PLAYING = not (IS_MACOS or IS_WIN or IS_HAIKU) and qt_multimedia_available


def get_player(parent: QObject | None = None) -> 'Player | None':
    if qt_multimedia_available:
        log.debug("Internal player: QtMultimedia available, initializing QMediaPlayer")
        from .player import Player

        return Player(parent)
    else:
        log.warning("Internal player: unavailable, %s", qt_multimedia_errmsg)
        return None


def get_now_playing_service(player: 'Player') -> object | None:
    """Return an implementation for integrating with the system's "now playing" functionality.
    Returns None, if not available.
    """
    if not OS_SUPPORTS_NOW_PLAYING or not get_config().setting['player_now_playing']:
        return None

    try:
        from picard.ui.player.mpris import register_mpris

        return register_mpris(player)
    except Exception as err:
        log.warning('Failed to initialize now playing integration: %r', err)
        return None
