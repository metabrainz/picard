# -*- coding: utf-8 -*-
#
# Built in Player for Picard
# Copyright (C) 2007 Gary van der Merwe
# Copyright (C) 2013 Laurent Monin
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


PLUGIN_NAME = u"Mini Media Player"
PLUGIN_AUTHOR = u"Gary van der Merwe, Laurent Monin"
PLUGIN_DESCRIPTION = "Play sound files from Picard using Phonon"
PLUGIN_VERSION = "0.3"
PLUGIN_API_VERSIONS = ["1.2.0"]


from PyQt4 import QtCore
from picard.ui.mainwindow import register_ui_init
from picard.plugins.player.playerbox import PlayerBox
import picard.plugins.player.resources


def create_player_box(mainwindow):
    player_box = PlayerBox(mainwindow)
    mainwindow.addToolBar(player_box)
    mainwindow.selectionUpdated.connect(player_box.updateSelection)
    mainwindow.tagger.tagger_stats_changed.connect(player_box.file_state_changed)

register_ui_init(create_player_box)
