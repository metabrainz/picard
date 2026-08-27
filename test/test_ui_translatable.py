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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from unittest.mock import patch

import pytest


@pytest.fixture()
def translatable_action(qapp):
    from picard.ui.translatable import TranslatableAction

    return TranslatableAction


@pytest.fixture()
def translatable_menu(qapp):
    from picard.ui.translatable import TranslatableMenu

    return TranslatableMenu


class TestTranslatableAction:
    def test_constructor_stores_source_text(self, translatable_action):
        action = translatable_action("Save")
        assert action._source_text == "Save"

    def test_constructor_translates_text(self, translatable_action):
        with patch('picard.ui.translatable._', side_effect=lambda x: f'[{x}]'):
            action = translatable_action("Save")
        assert action.text() == "[Save]"

    def test_set_text_stores_source(self, translatable_action):
        action = translatable_action()
        with patch('picard.ui.translatable._', side_effect=lambda x: f'[{x}]'):
            action.setText("Open")
        assert action._source_text == "Open"
        assert action.text() == "[Open]"

    def test_set_tool_tip_stores_source(self, translatable_action):
        action = translatable_action()
        with patch('picard.ui.translatable._', side_effect=lambda x: f'[{x}]'):
            action.setToolTip("Save the file")
        assert action._source_tool_tip == "Save the file"
        assert action.toolTip() == "[Save the file]"

    def test_set_status_tip_stores_source(self, translatable_action):
        action = translatable_action()
        with patch('picard.ui.translatable._', side_effect=lambda x: f'[{x}]'):
            action.setStatusTip("Ready")
        assert action._source_status_tip == "Ready"
        assert action.statusTip() == "[Ready]"

    def test_set_icon_text_stores_source(self, translatable_action):
        action = translatable_action()
        with patch('picard.ui.translatable._', side_effect=lambda x: f'[{x}]'):
            action.setIconText("Save...")
        assert action._source_icon_text == "Save..."
        assert action.iconText() == "[Save...]"

    def test_retranslate_ui_updates_all(self, translatable_action):
        action = translatable_action("Save")
        action.setToolTip("Save the file")
        action.setStatusTip("Ready")
        action.setIconText("Save...")

        # Simulate language change
        with patch('picard.ui.translatable._', side_effect=lambda x: f'<{x}>'):
            action.retranslateUi()

        assert action.text() == "<Save>"
        assert action.toolTip() == "<Save the file>"
        assert action.statusTip() == "<Ready>"
        assert action.iconText() == "<Save...>"

    def test_set_text_overwrites_previous_source(self, translatable_action):
        action = translatable_action("A")
        action.setText("B")
        assert action._source_text == "B"

    def test_empty_text_not_translated(self, translatable_action):
        action = translatable_action()
        assert action._source_text == ""
        assert action.text() == ""

    def test_retranslate_ui_skips_empty(self, translatable_action):
        action = translatable_action()
        with patch('picard.ui.translatable._') as mock_gettext:
            action.retranslateUi()
        mock_gettext.assert_not_called()


class TestTranslatableMenu:
    def test_constructor_stores_source_title(self, translatable_menu):
        menu = translatable_menu("File")
        assert menu._source_title == "File"

    def test_constructor_translates_title(self, translatable_menu):
        with patch('picard.ui.translatable._', side_effect=lambda x: f'[{x}]'):
            menu = translatable_menu("File")
        assert menu.title() == "[File]"

    def test_set_title_stores_source(self, translatable_menu):
        menu = translatable_menu()
        with patch('picard.ui.translatable._', side_effect=lambda x: f'[{x}]'):
            menu.setTitle("Edit")
        assert menu._source_title == "Edit"
        assert menu.title() == "[Edit]"

    def test_retranslate_ui_updates_title(self, translatable_menu):
        menu = translatable_menu("File")

        with patch('picard.ui.translatable._', side_effect=lambda x: f'<{x}>'):
            menu.retranslateUi()

        assert menu.title() == "<File>"

    def test_empty_title_not_translated(self, translatable_menu):
        menu = translatable_menu()
        assert menu._source_title == ""
        assert menu.title() == ""

    def test_retranslate_ui_skips_empty(self, translatable_menu):
        menu = translatable_menu()
        with patch('picard.ui.translatable._') as mock_gettext:
            menu.retranslateUi()
        mock_gettext.assert_not_called()
