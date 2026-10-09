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
        Label shown next to the icon for the status filter's menu action.
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


# There is a bug where the menu arrow type cannot be removed from a QToolButton
# https://qt-project.atlassian.net/browse/QTBUG-2036
class NoArrowToolButton(QtWidgets.QToolButton):
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
    _status_checkboxes: dict[str, QtWidgets.QCheckBox]
    _clear_all_action: QAction
    _syncing_status: bool

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = None
        for child_widget in self.children():
            if isinstance(child_widget, QtWidgets.QHBoxLayout):
                layout = child_widget
                break

        if not layout:
            raise RuntimeError(
                "AlbumFilter requires a QHBoxLayout member in order to add the complete and modified filter buttons"
            )

        self.initializing = True

        self._syncing_status = False
        self._saved_status_key = "filters_status_AlbumTreeView"
        self._status_button = NoArrowToolButton(self)
        self._status_button.setAutoRaise(False)
        self._status_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self._status_button.setArrowType(QtCore.Qt.ArrowType.NoArrow)
        self._status_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self._status_button.setText(_('Status'))
        tooltip = _('Drop-down containing Album status filters(modified/unmodified, complete/incomplete)')
        self._status_button.setToolTip(tooltip)
        self._status_button.setStatusTip(tooltip)

        self.status_filters = self._get_saved_status_filters()
        # Find the layout child to add the modified and complete buttons to

        self._status_checkboxes = {}
        menu = QtWidgets.QMenu()
        menu.setTitle(_("Status Filters"))
        menu.setTearOffEnabled(True)

        for state, desc in STATUS_FILTER_DESCRIPTORS.items():
            # A QCheckBox in a QWidgetAction shows the native check indicator,
            # the colored status icon and the label together, so the enabled
            # state is unambiguous and toggling keeps the menu open. A plain
            # checkable QAction renders its icon in the check column, hiding the
            # checkmark (see PICARD-189 review).
            checkbox = QtWidgets.QCheckBox(desc.text)
            checkbox.setToolTip(desc.tooltip)
            checkbox.setIcon(desc.icon_provider())
            checkbox.setContentsMargins(6, 2, 6, 2)
            # Each STATUS_FILTER_DESCRIPTORS key matches a StatusFilters field name.
            checkbox.setChecked(getattr(self.status_filters, state))
            checkbox.toggled.connect(partial(self._status_checkbox_toggled, state))

            widget_action = QtWidgets.QWidgetAction(menu)
            widget_action.setDefaultWidget(checkbox)
            menu.addAction(widget_action)
            self._status_checkboxes[state] = checkbox

        menu.addSeparator()
        self._clear_all_action = QAction(_("Clear all"), self)
        self._clear_all_action.setToolTip(_("Enable all status filters (show everything)"))
        self._clear_all_action.triggered.connect(self._clear_all_status_filters)
        menu.addAction(self._clear_all_action)

        self._status_button.setMenu(menu)
        self._update_status_button_label()

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
        self._sync_status_checkboxes()
        self._update_status_button_label()

    def _sync_status_checkboxes(self):
        """Reflect self.status_filters on the menu items without re-triggering handlers."""
        self._syncing_status = True
        try:
            for state, checkbox in self._status_checkboxes.items():
                # Each key in _status_checkboxes matches a StatusFilters field name.
                checkbox.setChecked(getattr(self.status_filters, state))
        finally:
            self._syncing_status = False

    def _get_saved_status_filters(self) -> StatusFilters:
        config = get_config()
        return StatusFilters.from_dict(config.persist[self._saved_status_key])

    def _save_status_filters(self):
        config = get_config()
        config.persist[self._saved_status_key] = self.status_filters.to_dict()

    def _status_checkbox_toggled(self, status_key, checked: bool):
        if self._syncing_status:
            # Ignore toggles caused by programmatic sync (clear / clear-all).
            return
        setattr(self.status_filters, status_key, checked)
        self._save_status_filters()
        self._update_status_button_label()
        self._query_changed(self.filter_query_box.text())

    def _clear_all_status_filters(self):
        """Reset every status filter to active (i.e. show everything)."""
        if self.status_filters.all_active():
            return
        self.status_filters = StatusFilters()
        self._save_status_filters()
        self._sync_status_checkboxes()
        self._update_status_button_label()
        self._query_changed(self.filter_query_box.text())

    def _update_status_button_label(self):
        self._status_button.setText(self.make_status_button_text(self.status_filters))

    @staticmethod
    def make_status_button_text(status_filters: StatusFilters) -> str:
        """Return the Status button label, showing the active/total count.

        When all filters are active (no filtering) the plain label is shown;
        otherwise the count makes it obvious that a status filter is in effect.
        """
        if status_filters.all_active():
            return _('Status')
        states = status_filters.to_dict().values()
        active = sum(1 for enabled in states if enabled)
        return _('Status (%(active)d/%(total)d)') % {'active': active, 'total': len(status_filters.to_dict())}


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
