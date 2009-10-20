# -*- coding: utf-8 -*-
#
# Built in Player for Picard
# Copyright (C) 2007 Gary van der Merwe
# Copyright (C) 2009 Carlin Mangar
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


PLUGIN_NAME = u"Preview Bar"
PLUGIN_AUTHOR = u"Carlin Mangar, Gary van der Merwe"
PLUGIN_DESCRIPTION = "Adds a cool music preview toolbar to Picard. Note however that you need Picard 0.12 and above to use this and you are limited\
                        by the codecs you have installed. On linux this plugin depends on Gstreamer natively, \
                        but there are different backends you can use.;)"
PLUGIN_VERSION = "0.3"
PLUGIN_API_VERSIONS = ["0.12.0"]


from PyQt4 import QtCore
from picard.ui.mainwindow import register_ui_init
from picard.plugins.previewbar.playerbox import PlayerBox
import picard.plugins.previewbar.resources
try:
    from PyQt4.phonon import Phonon
except ImportError, e:
    Phonon = None
    phonon_import_error = e

def create_player_box(mainwindow):
    player_box = PlayerBox(mainwindow)
    mainwindow.addToolBar(player_box)
    player_box.connect(mainwindow, QtCore.SIGNAL("update_selection"),
                       player_box.updateSelection)
    player_box.connect(mainwindow.tagger, QtCore.SIGNAL("file_save"),
                       player_box.file_save)
    player_box.connect(mainwindow.tagger, QtCore.SIGNAL("file_saving_finished"),
                       player_box.AutoPlay)
    player_box.connect(mainwindow.tagger, QtCore.SIGNAL("file_state_changed"),
                       player_box.file_changed)

register_ui_init(create_player_box)

