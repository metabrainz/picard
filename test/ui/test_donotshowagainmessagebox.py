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
from picard.ui.dialogs.donotshowagainmessagebox import (
    DoNotShowAgainMessageBox,
    create_do_not_show_again_checkbox,
    get_message_boxes,
    is_message_hidden,
    register_message_box,
    set_message_hidden,
)


@pytest.fixture(autouse=True)
def fake_config(monkeypatch, qapp):
    """Make the module use the fake config installed by conftest.py (also provides QApplication)."""
    monkeypatch.setattr(dnsa, 'get_config', lambda: picard_config.config)
    monkeypatch.setattr(dnsa, '_MESSAGE_BOXES', {})
    return picard_config.config


@pytest.fixture
def sample_message_box():
    # Defined here, not at module level, to register it in the patched registry only
    class SampleMessageBox(DoNotShowAgainMessageBox):
        KEY = 'sample'
        TITLE = 'Sample'

    return SampleMessageBox


def test_message_is_not_hidden_by_default():
    assert not is_message_hidden('key')


def test_set_message_hidden(fake_config):
    set_message_hidden('b', True)
    set_message_hidden('a', True)
    set_message_hidden('b', True)
    assert fake_config.persist['hidden_message_boxes'] == ['a', 'b']
    assert is_message_hidden('a')

    set_message_hidden('a', False)
    set_message_hidden('unknown', False)
    assert fake_config.persist['hidden_message_boxes'] == ['b']
    assert not is_message_hidden('a')


def test_register_message_box():
    register_message_box('key', 'Title')
    messages = get_message_boxes()
    assert messages == {'key': 'Title'}
    # the returned dict is a copy
    messages.clear()
    assert get_message_boxes() == {'key': 'Title'}


def test_checkbox_is_unchecked_and_updates_the_option_when_toggled():
    checkbox = create_do_not_show_again_checkbox('key')
    assert checkbox.text() == "Do not show this message again."
    assert not checkbox.isChecked()
    assert not is_message_hidden('key')

    checkbox.setChecked(True)
    assert is_message_hidden('key')

    checkbox.setChecked(False)
    assert not is_message_hidden('key')


def test_subclass_with_key_is_registered():
    class OtherMessageBox(DoNotShowAgainMessageBox):
        KEY = 'other'
        TITLE = 'Other'

    assert get_message_boxes() == {'other': 'Other'}


def test_subclass_without_key_is_not_registered():
    class NoKeyMessageBox(DoNotShowAgainMessageBox):
        pass

    assert get_message_boxes() == {}


def test_message_box_checkbox_stays_valid_and_updates_the_option(sample_message_box):
    # The checkbox must outlive its creation: setCheckBox() does not keep the
    # Python object alive, accessing a deleted checkbox crashes.
    box = sample_message_box(None, 'text')
    checkbox = box.checkBox()
    assert checkbox.text() == "Do not show this message again."
    assert not sample_message_box.is_hidden()

    checkbox.setChecked(True)
    assert sample_message_box.is_hidden()
    assert is_message_hidden('sample')
