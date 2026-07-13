# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

from picard.plugin import ExtensionPoint


ext_point_metadata_tag_actions = ExtensionPoint(label='metadata_tag_actions')


def register_metadata_tag_action(action: type) -> None:
    """Register a context menu action for metadata tags.

    The action class must define:
        - TITLE: str - The menu item label
        - callback(self, tags, objects): Called when the action is triggered

    The action class may optionally define:
        - is_visible(self, tags, objects) -> bool: Controls visibility in the
          context menu. If not defined, the action is always visible.

    Args:
        action: The action class to register.
    """
    ext_point_metadata_tag_actions.register(action.__module__, action)
