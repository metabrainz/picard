# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
# Copyright (C) 2025 Francisco Lisboa
# Copyright (C) 2025 João Sousa
# Copyright (C) 2025-2026 Laurent Monin
# Copyright (C) 2025-2026 Philipp Wolfer
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
from dataclasses import dataclass
from functools import partial

from PyQt6 import (
    QtCore,
    QtWidgets,
)
from PyQt6.QtGui import QAction, QIcon

from picard.config import get_config
from picard.i18n import gettext as _
from picard.util import icontheme

from picard.ui.filter import Filter, StatusFilters


@dataclass
class AlbumStatusFilterDescriptor:
    """Descriptor used to create a checkbox storing the status filter state

    Parameters
    ----------
    icon_provider : Callable
        Functor used to create the icon used for the Tool Button in the UI.
    text : str
        Text to place next to the icon (Not used in this case to save UI space).
    tooltip : str
        Tooltip explaining the current filter state for the album status.
    """

    icon_provider: Callable[[], QIcon]
    text: str
    tooltip: str


# Creates the icons on demand when the callable is invoked
def _modified_icon():
    return QIcon(":/images/match-5.png")


def _unmodified_icon():
    return QIcon(":/images/track-saved.png")


def _complete_icon():
    return icontheme.lookup('media-optical-saved', icontheme.ICON_SIZE_MENU)


def _incomplete_icon():
    return icontheme.lookup('media-optical', icontheme.ICON_SIZE_MENU)


STATUS_FILTER_DESCRIPTORS: dict[str, AlbumStatusFilterDescriptor] = {
    'modified': AlbumStatusFilterDescriptor(_modified_icon, _("Modified"), _("Filters on modified albums")),
    'unmodified': AlbumStatusFilterDescriptor(_unmodified_icon, _("Unmodified"), _("Filters on unmodified albums")),
    'complete': AlbumStatusFilterDescriptor(_complete_icon, _("Complete"), _("Filters on complete albums")),
    'incomplete': AlbumStatusFilterDescriptor(_incomplete_icon, _("Incomplete"), _("Filters on incomplete albums")),
}


# There is a bug where the menu Arrow typecannot be removed from a QToolButton
# https://qt-project.atlassian.net/browse/QTBUG-2036
class NoArrawToolButton(QtWidgets.QToolButton):
    """
    Override of the ToolButton class to workaround bug where the menu arrow always appear on Tool Button
    even when the NoArrow style option is set
    """

    def paintEvent(self, a0):
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionToolButton()
        self.initStyleOption(option)
        option.features = QtWidgets.QStyleOptionToolButton.ToolButtonFeature.None_
        painter.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_ToolButton, option)


class AlbumFilter(Filter):
    """
    AlbumTreeView filter  which overrides the base Filter class.
    It adds in two additional buttons that allows filtering on album modification state,
    as well as album complete state.

    """

    _saved_status_key: str
    _status_button: QtWidgets.QToolButton
    status_filters: StatusFilters
    _status_actions: dict[str, QAction]

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = None
        for child_widget in self.children():
            if isinstance(child_widget, QtWidgets.QHBoxLayout):
                layout = child_widget
                break

        if not layout:
            raise Exception(
                "Album Filter is requires layout member in order to add complete and modified filter buttons"
            )

        self.initializing = True

        self._saved_status_key = "filters_status_AlbumTreeView"
        self._status_button = NoArrawToolButton(self)
        self._status_button.setAutoRaise(False)
        self._status_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self._status_button.setArrowType(QtCore.Qt.ArrowType.NoArrow)
        self._status_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self._status_button.setText(_('Status'))
        toolTip = _('Drop-down containing Album status filters(modified/unmodified, complete/incomplete)')
        self._status_button.setToolTip(toolTip)
        self._status_button.setStatusTip(toolTip)

        self.status_filters = self._get_saved_status_filters()
        # Find the layout child to add the modified and complete buttons to

        self._status_actions = {}
        menu = QtWidgets.QMenu()
        menu.setTitle(_("Status Filters"))
        menu.setTearOffEnabled(True)

        for state, desc in STATUS_FILTER_DESCRIPTORS.items():
            self._status_actions[state] = QAction(desc.text)
            self._status_actions[state].setToolTip(desc.tooltip)
            self._status_actions[state].setIcon(desc.icon_provider())
            self._status_actions[state].setCheckable(True)
            match state:
                case 'modified':
                    self._status_actions[state].setChecked(self.status_filters.modified)
                case 'unmodified':
                    self._status_actions[state].setChecked(self.status_filters.unmodified)
                case 'complete':
                    self._status_actions[state].setChecked(self.status_filters.complete)
                case 'incomplete':
                    self._status_actions[state].setChecked(self.status_filters.incomplete)

            _unused = self._status_actions[state].toggled.connect(partial(self._status_checkbox_toggled, state))
        menu.addActions(self._status_actions.values())

        self._status_button.setMenu(menu)

        # Locate base Filter class filter button in order to insert status button before it
        filter_button_idx = layout.indexOf(self.filter_button)
        filter_button_idx = filter_button_idx if filter_button_idx != -1 else 0

        layout.insertWidget(filter_button_idx, self._status_button)

        self.initializing = False

    def _query_changed(self, text):
        """
        Emits the filterChanged signal, with the addition of the AlbumStatusState
        for the modified and complete filter buttons
        """
        self.filterChanged.emit(text, self.selected_filters, self.status_filters)

    def clear(self):
        super().clear()
        self.status_filters = self._get_saved_status_filters()
        for state, checkbox in self._status_actions.items():
            match state:
                case 'modified':
                    checkbox.setChecked(self.status_filters.modified)
                case 'unmodified':
                    checkbox.setChecked(self.status_filters.unmodified)
                case 'complete':
                    checkbox.setChecked(self.status_filters.complete)
                case 'incomplete':
                    checkbox.setChecked(self.status_filters.incomplete)

    def _get_saved_status_filters(self) -> StatusFilters:
        config = get_config()
        return StatusFilters.from_dict(config.persist[self._saved_status_key])

    def _status_checkbox_toggled(self, status_key, checked: bool):
        setattr(self.status_filters, status_key, checked)
        config = get_config()
        config.persist[self._saved_status_key] = self.status_filters.to_dict()
        self._query_changed(self.filter_query_box.text())


def create_filter_for_tree_view(parent, *args, **kwargs) -> Filter:
    """Create an appropriate class based on the type of the parent Tree View

    For AlbumTreeView types, this returns an AlbumFilter
    """
    match type(parent).__name__:
        case 'AlbumTreeView':
            return AlbumFilter(
                parent,
                *args,
                **kwargs,
            )
        case _:
            return Filter(
                parent,
                *args,
                **kwargs,
            )
