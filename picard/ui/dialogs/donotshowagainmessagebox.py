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


from PyQt6 import QtWidgets

from picard.config import get_config
from picard.i18n import (
    N_,
    gettext as _,
)


# Messages the user can hide, as {key: untranslated title}. Filled by
# register_message_box(), used to let the user show them again in the options.
_MESSAGE_BOXES: dict[str, str] = {}


def register_message_box(key: str, title: str) -> None:
    """Declare a message the user can hide with a "do not show again" checkbox.

    `title` must be marked for translation with N_() and translated when displayed.
    """
    _MESSAGE_BOXES[key] = title


def get_message_boxes() -> dict[str, str]:
    """Return the registered messages as {key: untranslated title}."""
    return dict(_MESSAGE_BOXES)


def is_message_hidden(key: str) -> bool:
    """Return True if the user asked not to see the message identified by `key`."""
    return key in get_config().persist['hidden_message_boxes']


def set_message_hidden(key: str, hidden: bool) -> None:
    """Remember whether the message identified by `key` should be hidden."""
    config = get_config()
    keys = set(config.persist['hidden_message_boxes'])
    if hidden:
        keys.add(key)
    else:
        keys.discard(key)
    config.persist['hidden_message_boxes'] = sorted(keys)


def create_do_not_show_again_checkbox(key: str) -> QtWidgets.QCheckBox:
    """Return a "Do not show this message again" checkbox, unchecked by default.

    The message identified by `key` is hidden (or shown again) as soon as the
    checkbox is toggled, whatever happens to the dialog it is in afterwards.
    """
    checkbox = QtWidgets.QCheckBox(_("Do not show this message again."))
    checkbox.toggled.connect(lambda checked: set_message_hidden(key, checked))
    return checkbox


class DoNotShowAgainMessageBox(QtWidgets.QMessageBox):
    """Message box with a "Do not show this message again" checkbox.

    Subclasses define a unique `KEY` and a `TITLE` marked with N_(). Check
    `is_hidden()` before showing the message. The checkbox is recorded in the
    `hidden_message_boxes` persisted option as soon as it is toggled.
    """

    KEY: str = ''
    TITLE: str = N_("Message")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.KEY:
            register_message_box(cls.KEY, cls.TITLE)

    @classmethod
    def is_hidden(cls) -> bool:
        return is_message_hidden(cls.KEY)

    def __init__(
        self,
        parent,
        text: str,
        icon: QtWidgets.QMessageBox.Icon = QtWidgets.QMessageBox.Icon.Information,
        buttons: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.StandardButton.Ok,
        default_button: QtWidgets.QMessageBox.StandardButton | None = None,
    ):
        super().__init__(parent)
        self.setIcon(icon)
        self.setWindowTitle(_(self.TITLE))
        self.setText(text)
        self.setStandardButtons(buttons)
        if default_button is not None:
            self.setDefaultButton(default_button)

        # Keep a reference, setCheckBox() doesn't take the ownership on the Python side
        self._checkbox = create_do_not_show_again_checkbox(self.KEY)
        self.setCheckBox(self._checkbox)
