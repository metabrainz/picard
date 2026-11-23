# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Bob Swift
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

from unittest.mock import MagicMock

from picard import config as picard_config

import pytest

import picard.ui.dialogs.donotshowagainmessagebox as dnsa
import picard.ui.options.plugins as plugins_module
from picard.ui.options.plugins import Plugins3OptionsPage


@pytest.fixture(autouse=True)
def fake_config(monkeypatch, qapp):
    """Make the modules use the fake config installed by conftest.py (also provides QApplication)."""
    monkeypatch.setattr(dnsa, 'get_config', lambda: picard_config.config)


@pytest.fixture
def notes_dialog(monkeypatch):
    notes = MagicMock()
    notes.is_hidden.return_value = False
    monkeypatch.setattr(plugins_module, 'PluginNotesDialog', notes)
    return notes


@pytest.fixture
def single_shot(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(plugins_module.QtCore.QTimer, 'singleShot', mock)
    return mock


@pytest.fixture
def page(monkeypatch):
    tagger = MagicMock()
    tagger.get_plugins_available.return_value = (False, 'testing')
    tagger.get_plugin_manager.return_value = None
    monkeypatch.setattr('picard.ui.options.tagger_instance', lambda: tagger)
    page = Plugins3OptionsPage()
    yield page
    page.deleteLater()


def test_notes_shown_once_when_page_is_displayed(page, notes_dialog, single_shot):
    page.show()
    delay, show_notes = single_shot.call_args.args
    assert delay == 200
    notes_dialog.assert_not_called()

    show_notes()
    show_notes()

    notes_dialog.assert_called_once_with(page.window())
    notes_dialog.return_value.show.assert_called_once_with()
    page.hide()
    page.show()
    assert single_shot.call_count == 1


def test_notes_not_shown_if_page_is_hidden_before_timer_fires(page, notes_dialog, single_shot):
    page.show()
    show_notes = single_shot.call_args.args[1]
    page.hide()

    show_notes()

    notes_dialog.assert_not_called()


def test_notes_not_scheduled_when_hidden_by_user(page, notes_dialog, single_shot):
    notes_dialog.is_hidden.return_value = True

    page.show()

    single_shot.assert_not_called()
