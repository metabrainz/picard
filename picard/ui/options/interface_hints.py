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


from collections.abc import Callable
from typing import (
    ClassVar,
    NamedTuple,
)

from PyQt6 import QtWidgets

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
)

# Importing these modules registers the messages they can hide.
from picard.ui.dialogs import installconfirm  # noqa: F401 # pylint: disable=unused-import
from picard.ui.dialogs.donotshowagainmessagebox import (
    get_message_boxes,
    is_message_hidden,
    set_message_hidden,
)
from picard.ui.newuserdialog import NewUserDialog  # noqa: F401 # pylint: disable=unused-import
from picard.ui.options import (
    OptionsPage,
    PageOptionConfigs,
)
from picard.ui.savewarningdialog import SaveWarningDialog  # noqa: F401 # pylint: disable=unused-import


class _Entry(NamedTuple):
    """Something Picard can show, with the way to read and change that state."""

    label: str
    is_shown: Callable[[], bool]
    set_shown: Callable[[bool], None]
    tooltip: str = ''


def _tutorial_is_shown() -> bool:
    # The tutorial starts from the beginning: enabled and no step shown yet.
    persist = get_config().persist
    return not persist['tutorial_disabled'] and not persist['tutorial_steps_shown']


def _tutorial_set_shown(shown: bool) -> None:
    persist = get_config().persist
    if shown:
        persist['tutorial_steps_shown'] = []
    persist['tutorial_disabled'] = not shown


def _wizard_is_shown() -> bool:
    return not get_config().persist['setup_wizard_completed']


def _wizard_set_shown(shown: bool) -> None:
    get_config().persist['setup_wizard_completed'] = not shown


class InterfaceHintsOptionsPage(OptionsPage):
    NAME = 'interface_hints'
    TITLE = N_("Hints")
    PARENT = 'interface'
    SORT_ORDER = 70
    ACTIVE = True

    OPTIONS: ClassVar[PageOptionConfigs] = {}

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout(self)
        group = QtWidgets.QGroupBox(_("Show the following"))
        group_layout = QtWidgets.QVBoxLayout(group)
        group_layout.addWidget(
            QtWidgets.QLabel(
                _(
                    "Messages hidden with their \"Do not show this message again\" checkbox, "
                    "the tutorial tips and the setup wizard. Check an item to show it."
                )
            )
        )

        self._entries: dict[str, _Entry] = {}
        for key, title in sorted(get_message_boxes().items(), key=lambda item: _(item[1]).casefold()):
            self._entries[key] = _Entry(
                _(title),
                lambda key=key: not is_message_hidden(key),
                lambda shown, key=key: set_message_hidden(key, not shown),
            )
        self._entries['tutorial'] = _Entry(
            _("Tutorial tips"),
            _tutorial_is_shown,
            _tutorial_set_shown,
            _("Check to start the tutorial again from the beginning."),
        )
        self._entries['setup_wizard'] = _Entry(
            _("Show the setup wizard at startup"),
            _wizard_is_shown,
            _wizard_set_shown,
            _("Cancelling or finishing the setup wizard turns this off."),
        )

        self._checkboxes = {}
        self._loaded: dict[str, bool] = {}
        for key, entry in self._entries.items():
            checkbox = QtWidgets.QCheckBox(entry.label)
            checkbox.setToolTip(entry.tooltip)
            self._checkboxes[key] = checkbox
            group_layout.addWidget(checkbox)

        layout.addWidget(group)
        layout.addStretch()

    def load(self):
        self._loaded = {}
        self._refresh()

    def showEvent(self, event):
        # The state can change while the options are open (e.g. a message hidden from
        # the plugin installation dialog), so show the current one, unless it was edited here.
        self._refresh()
        super().showEvent(event)

    def _refresh(self):
        for key, checkbox in self._checkboxes.items():
            if key not in self._loaded or checkbox.isChecked() == self._loaded[key]:
                shown = self._entries[key].is_shown()
                checkbox.setChecked(shown)
                self._loaded[key] = shown

    def save(self):
        # Only write the items edited here, others may have been changed meanwhile.
        for key, checkbox in self._checkboxes.items():
            if checkbox.isChecked() != self._loaded.get(key):
                self._entries[key].set_shown(checkbox.isChecked())
        self._loaded = {}
        self._refresh()

    def restore_defaults(self):
        for checkbox in self._checkboxes.values():
            checkbox.setChecked(True)


register_options_page(InterfaceHintsOptionsPage)
