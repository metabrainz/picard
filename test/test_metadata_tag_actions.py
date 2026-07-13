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

from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.extension_points import ExtensionPoint
from picard.extension_points.metadata_tag_actions import (
    ext_point_metadata_tag_actions,
    register_metadata_tag_action,
)
from picard.plugin3.api_impl import MetadataTagAction


class TestMetadataTagActions(PicardTestCase):
    @patch(
        'picard.extension_points.metadata_tag_actions.ext_point_metadata_tag_actions',
        ExtensionPoint(label='test_metadata_tag_actions'),
    )
    def test_register_action(self):
        """Registering an action should make it available via the extension point."""
        from picard.extension_points.metadata_tag_actions import ext_point_metadata_tag_actions

        class MyAction:
            TITLE = "Test Action"

            def callback(self, tag, objects):
                pass

        MyAction.__module__ = 'picard.plugins.testplugin'
        register_metadata_tag_action(MyAction)
        # Without config filtering (no config), all items are yielded
        with patch('picard.extension_points.get_config', return_value=None):
            items = list(ext_point_metadata_tag_actions)
        self.assertEqual(len(items), 1)
        self.assertIs(items[0], MyAction)

    @patch(
        'picard.extension_points.metadata_tag_actions.ext_point_metadata_tag_actions',
        ExtensionPoint(label='test_metadata_tag_actions'),
    )
    def test_register_multiple_actions(self):
        """Multiple actions can be registered."""
        from picard.extension_points.metadata_tag_actions import ext_point_metadata_tag_actions

        class Action1:
            TITLE = "Action 1"

            def callback(self, tag, objects):
                pass

        class Action2:
            TITLE = "Action 2"

            def callback(self, tag, objects):
                pass

        Action1.__module__ = 'picard.plugins.testplugin'
        Action2.__module__ = 'picard.plugins.testplugin'
        register_metadata_tag_action(Action1)
        register_metadata_tag_action(Action2)
        with patch('picard.extension_points.get_config', return_value=None):
            items = list(ext_point_metadata_tag_actions)
        self.assertEqual(len(items), 2)

    def test_action_callback_receives_tag_and_objects(self):
        """Action callback should receive tags list and objects."""
        received = {}

        class MyAction:
            TITLE = "Test"

            def callback(self, tags, objects):
                received['tags'] = tags
                received['objects'] = objects

        action = MyAction()
        objects = {'file1', 'file2'}
        action.callback(['artist', 'albumartist'], objects)
        self.assertEqual(received['tags'], ['artist', 'albumartist'])
        self.assertEqual(received['objects'], objects)

    def test_action_is_visible_default(self):
        """Action without is_visible override should always be visible."""

        class MyAction(MetadataTagAction):
            TITLE = "Test"

            def callback(self, tags, objects):
                pass

        action = MyAction()
        self.assertTrue(action.is_visible(['artist'], set()))
        self.assertTrue(action.is_visible(['~filename'], set()))
        self.assertTrue(action.is_visible(['artist', 'albumartist'], set()))

    def test_action_is_visible_filters(self):
        """Action with is_visible override can filter based on tags and objects."""

        class MyAction(MetadataTagAction):
            TITLE = "Test"

            def callback(self, tags, objects):
                pass

            def is_visible(self, tags, objects):
                return all(not tag.startswith('~') for tag in tags)

        action = MyAction()
        self.assertTrue(action.is_visible(['artist'], set()))
        self.assertTrue(action.is_visible(['artist', 'albumartist'], set()))
        self.assertFalse(action.is_visible(['~filename'], set()))
        self.assertFalse(action.is_visible(['artist', '~filename'], set()))

    def test_action_callable_title(self):
        """TITLE integrates with display_title() for translation support."""

        class MyAction(MetadataTagAction):
            TITLE = "Pin Tag"

            def callback(self, tag, objects):
                pass

        action = MyAction()
        # display_title() should return the TITLE when no api/translation is set
        self.assertEqual(action.display_title(), "Pin Tag")

    def test_extension_point_label(self):
        """Extension point should have the correct label."""
        self.assertEqual(ext_point_metadata_tag_actions.label, 'metadata_tag_actions')
