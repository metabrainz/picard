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


from picard import config as picard_config

import pytest

import picard.ui.dialogs.donotshowagainmessagebox as dnsa
import picard.ui.options.interface_hints as hints
from picard.ui.options.interface_hints import InterfaceHintsOptionsPage


@pytest.fixture(autouse=True)
def fake_config(monkeypatch, qapp):
    """Make the modules use the fake config installed by conftest.py (also provides QApplication)."""
    monkeypatch.setattr(dnsa, 'get_config', lambda: picard_config.config)
    monkeypatch.setattr(hints, 'get_config', lambda: picard_config.config)
    return picard_config.config


@pytest.fixture
def page(patch_tagger_instance):
    patch_tagger_instance('picard.ui.options')
    return InterfaceHintsOptionsPage()


def shown(page):
    return {key: checkbox.isChecked() for key, checkbox in page._checkboxes.items()}


def test_lists_registered_messages_tutorial_and_wizard(page):
    assert set(page._checkboxes) == {
        'new_user',
        'save_warning',
        'plugin_install_warning',
        'tutorial',
        'setup_wizard',
    }


def test_load_shows_everything_by_default(page):
    page.load()
    assert all(shown(page).values())


def test_load_reflects_hidden_messages_tutorial_and_wizard(page, fake_config):
    dnsa.set_message_hidden('save_warning', True)
    fake_config.persist['tutorial_steps_shown'] = ['step']
    fake_config.persist['setup_wizard_completed'] = True
    page.load()
    state = shown(page)
    assert not state['save_warning']
    assert not state['tutorial']
    assert not state['setup_wizard']
    assert state['new_user']


def test_save_updates_messages_tutorial_and_wizard(page, fake_config):
    fake_config.persist['tutorial_steps_shown'] = ['step']
    fake_config.persist['setup_wizard_completed'] = True
    page.load()

    page._checkboxes['new_user'].setChecked(False)
    page._checkboxes['tutorial'].setChecked(True)
    page._checkboxes['setup_wizard'].setChecked(True)
    page.save()

    assert dnsa.is_message_hidden('new_user')
    assert fake_config.persist['tutorial_steps_shown'] == []
    assert fake_config.persist['tutorial_disabled'] is False
    assert fake_config.persist['setup_wizard_completed'] is False


def test_unchecking_tutorial_disables_it(page, fake_config):
    page.load()
    page._checkboxes['tutorial'].setChecked(False)
    page.save()
    assert fake_config.persist['tutorial_disabled'] is True


def test_save_keeps_messages_hidden_elsewhere_meanwhile(page):
    page.load()
    # Hidden from a dialog while the options are open
    dnsa.set_message_hidden('plugin_install_warning', True)
    page.save()
    assert dnsa.is_message_hidden('plugin_install_warning')


def test_page_shows_state_changed_elsewhere_unless_edited_here(page):
    page.load()
    page._checkboxes['new_user'].setChecked(False)
    dnsa.set_message_hidden('plugin_install_warning', True)
    dnsa.set_message_hidden('save_warning', True)

    page._refresh()

    state = shown(page)
    assert not state['plugin_install_warning']
    assert not state['save_warning']
    assert not state['new_user']  # edited here, kept
    assert not dnsa.is_message_hidden('new_user')  # not saved yet


def test_restore_defaults_checks_everything(page):
    page.load()
    for checkbox in page._checkboxes.values():
        checkbox.setChecked(False)
    page.restore_defaults()
    assert all(shown(page).values())
