# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Philipp Wolfer
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

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
)

from picard.ui.forms.ui_options_player import Ui_PlayerOptionsPage
from picard.ui.options import OptionsPage
from picard.ui.player import OS_SUPPORTS_NOW_PLAYING


class PlayerOptionsPage(OptionsPage):
    NAME = 'player'
    TITLE = N_("Audio Player")
    PARENT = None
    SORT_ORDER = 85
    ACTIVE = True
    HELP_URL = "/config/options_player.html"

    OPTIONS = (
        ('player_now_playing', ['player_now_playing']),
        ('listenbrainz_enabled', ['listenbrainz_enabled']),
        ('listenbrainz_submit_only_tagged', ['listenbrainz_submit_only_tagged']),
        ('listenbrainz_user', ['listenbrainz_user']),
        ('listenbrainz_token', ['listenbrainz_token']),
    )

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_PlayerOptionsPage()
        self.ui.setupUi(self)

        if not OS_SUPPORTS_NOW_PLAYING:
            self.ui.player_now_playing.hide()

    def load(self):
        config = get_config()
        self.ui.player_now_playing.setChecked(config.setting['player_now_playing'])
        self.ui.listenbrainz_enabled.setChecked(config.setting['listenbrainz_enabled'])
        self.ui.listenbrainz_submit_only_tagged.setChecked(config.setting['listenbrainz_submit_only_tagged'])
        self.ui.listenbrainz_user.setText(config.setting['listenbrainz_user'])
        self.ui.listenbrainz_token.setText(config.setting['listenbrainz_token'])

    def save(self):
        config = get_config()
        config.setting['listenbrainz_enabled'] = self.ui.listenbrainz_enabled.isChecked()
        config.setting['listenbrainz_submit_only_tagged'] = self.ui.listenbrainz_submit_only_tagged.isChecked()
        config.setting['listenbrainz_user'] = self.ui.listenbrainz_user.text()
        config.setting['listenbrainz_token'] = self.ui.listenbrainz_token.text()
        self._update_now_playing_settings(config)

    def _update_now_playing_settings(self, config):
        old_player_now_playing = config.setting['player_now_playing']
        new_player_now_playing = self.ui.player_now_playing.isChecked()
        if old_player_now_playing != new_player_now_playing:
            config.setting['player_now_playing'] = new_player_now_playing
            if now_playing_service := getattr(self.tagger.window, '_player_now_playing', None):
                if new_player_now_playing:
                    now_playing_service.enable()
                else:
                    now_playing_service.disable()


register_options_page(PlayerOptionsPage)
