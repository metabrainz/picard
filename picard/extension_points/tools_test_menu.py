# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
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

from PyQt6.QtCore import QObject, pyqtSignal

from picard.plugin import ExtensionPoint


class Signaler(QObject):
    test_menu_updated = pyqtSignal()


signaler = Signaler()
ext_point_test_menu_items = ExtensionPoint(label='test_menu_items')


def register_test_menu_action(action, api=None):
    if api is not None:
        action._plugin_api = api
    ext_point_test_menu_items.register(action.__module__, action)
    signaler.test_menu_updated.emit()
