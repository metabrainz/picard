# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012 Lukáš Lalinský
# Copyright (C) 2007 Robert Kaye
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008-2011, 2014-2015, 2018-2024 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011 Tim Blechmann
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Your Name
# Copyright (C) 2012-2013 Wieland Hoffmann
# Copyright (C) 2013-2014, 2016, 2018-2024 Laurent Monin
# Copyright (C) 2013-2014, 2017, 2020 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Louis Sautier
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2023 certuna
# Copyright (C) 2024 Suryansh Shakya
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


from PyQt6 import (
    QtCore,
    QtGui,
)

from picard.plugin import ExtensionPoint
from picard.util.display_title_base import HasDisplayTitle


class BaseAction(QtGui.QAction, HasDisplayTitle):
    TITLE = "Unknown"
    MENU = []

    def __init__(self, api=None, parent=None):
        super().__init__(self.display_title(), parent=parent)
        self.tagger = QtCore.QCoreApplication.instance()
        self.triggered.connect(self.__callback)

    def __callback(self):
        objs = self.tagger.window.selected_objects
        try:
            self.callback(objs)
        except Exception:
            from picard import log

            plugin_id = getattr(self.api, 'plugin_id', 'unknown')
            log.error("Error in action %s (plugin: %s):", self.display_title(), plugin_id, exc_info=True)

    def callback(self, objs):
        raise NotImplementedError


ext_point_album_actions = ExtensionPoint(label='album_actions')
ext_point_cluster_actions = ExtensionPoint(label='cluster_actions')
ext_point_clusterlist_actions = ExtensionPoint(label='clusterlist_actions')
ext_point_file_actions = ExtensionPoint(label='file_actions')
ext_point_track_actions = ExtensionPoint(label='track_actions')


def register_album_action(action):
    ext_point_album_actions.register(action.__module__, action)


def register_cluster_action(action):
    ext_point_cluster_actions.register(action.__module__, action)


def register_clusterlist_action(action):
    ext_point_clusterlist_actions.register(action.__module__, action)


def register_file_action(action):
    ext_point_file_actions.register(action.__module__, action)


def register_track_action(action):
    ext_point_track_actions.register(action.__module__, action)
