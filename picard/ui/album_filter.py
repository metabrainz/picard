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
from itertools import islice
from typing import override

from PyQt6 import (
    QtCore,
    QtWidgets,
)
from PyQt6.QtGui import QAction, QIcon

from picard.config import get_config
from picard.i18n import (
    gettext as _,
)
from picard.util import icontheme

from picard.ui.filter import AlbumStatusState, Filter


@dataclass
class AlbumStatusFilterDescriptor:
    """Descriptor used to create an Action that can be triggered in the UI
    to transition the status filter between its states.

    The states cycle in the following order:
    NOT_APPLICABLE -> TRUE -> FALSE -> NOT_APPLICABLE ->...

    Note that that the filter goes from N/A to TRUE instead of N/A to FALSE
    This is to allow the filter the filters to flow for the modified and complete state
    as follows:
    N/A -> Complete -> Incomplete
    N/A -> Modified -> Unmodified

    Parameters
    ----------
    state : AlbumStatusState
        Enum representing the album status state to filter against.
    icon_provider : Callable
        Functor used to create the icon used for the Tool Button in the UI.
    text : str
        Text to place next to the icon (Not used in this case to save UI space).
    tooltip : str
        Tooltip explaining the current filter state for the album status.
    """

    state: AlbumStatusState
    icon_provider: Callable[[], QIcon]
    text: str
    tooltip: str


# Creates the icons on demand when the callable is invoked
def _modified_icon():
    return QIcon(":/images/match-5.png")


def _modified_na_icon():
    return icontheme.lookup('system-search', icontheme.ICON_SIZE_MENU)


def _unmodified_icon():
    return QIcon(":/images/track-saved.png")


def _complete_icon():
    return icontheme.lookup('media-optical-saved', icontheme.ICON_SIZE_MENU)


def _complete_na_icon():
    return icontheme.lookup('system-search', icontheme.ICON_SIZE_MENU)


def _incomplete_icon():
    return icontheme.lookup('media-optical', icontheme.ICON_SIZE_MENU)


MODIFIED_FILTER_DESCRIPTORS: list[AlbumStatusFilterDescriptor] = [
    AlbumStatusFilterDescriptor(
        AlbumStatusState.NOT_APPLICABLE,
        _modified_na_icon,
        _("Filter Not Active"),
        _("No filtering is performed on album modified state"),
    ),
    # Use the highest match level as the "modified" icon for now
    AlbumStatusFilterDescriptor(
        AlbumStatusState.TRUE, _modified_icon, _("Modified"), _("Filters on modified albums only")
    ),
    AlbumStatusFilterDescriptor(
        AlbumStatusState.FALSE, _unmodified_icon, _("Unmodified"), _("Filters on unmodified albums only")
    ),
]
COMPLETE_FILTER_DESCRIPTORS: list[AlbumStatusFilterDescriptor] = [
    AlbumStatusFilterDescriptor(
        AlbumStatusState.NOT_APPLICABLE,
        _complete_na_icon,
        _("Filter Not Active"),
        _("No filtering is performed on album complete state"),
    ),
    AlbumStatusFilterDescriptor(
        AlbumStatusState.TRUE, _complete_icon, _("Complete"), _("Filters on complete albums only")
    ),
    AlbumStatusFilterDescriptor(
        AlbumStatusState.FALSE, _incomplete_icon, _("Incomplete"), _("Filters on incomplete albums only")
    ),
]


# There is a bug with menu Arrow type state getting reset when the default action is re-assigned
# https://qt-project.atlassian.net/browse/QTBUG-2036
class NoArrawToolButton(QtWidgets.QToolButton):
    """
    Override of the ToolButton class to workaround bug where the menu arrow always appear on Tool Button
    even when the NoArrow style option is set
    """

    @override
    def paintEvent(self, a0):
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionToolButton()
        self.initStyleOption(option)
        option.features = QtWidgets.QStyleOptionToolButton.ToolButtonFeature.None_
        painter.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_ToolButton, option)


@dataclass
class ActionFilterTriggerData:
    """
    Stores data needed to update the status filter buttons
    to the next state
    """

    status_config_key: str
    button: QtWidgets.QToolButton
    triggered_action: QAction
    action_group: list[QAction]
    filter_descs: list[AlbumStatusFilterDescriptor]
    selected_filter_index_prop: property


class AlbumFilter(Filter):
    """
    AlbumTreeView filter  which overrides the base Filter class.
    It adds in two additional buttons that allows filtering on album modification state,
    as well as album complete state.

    """

    _saved_modified_key: str
    _saved_complete_key: str
    _modified_button: QtWidgets.QToolButton
    _complete_button: QtWidgets.QToolButton
    _selected_modified_desc_index: int
    _selected_complete_desc_index: int
    _modified_actions: list[QAction]
    _complete_actions: list[QAction]

    def __init__(self, parent=None):
        super().__init__(parent)

        self.initializing = True

        self._saved_modified_key = "filters_modified_AlbumTreeView"
        self._saved_complete_key = "filters_complete_AlbumTreeView"
        self._modified_button = NoArrawToolButton(self)
        self._complete_button = NoArrawToolButton(self)
        for button in [self._modified_button, self._complete_button]:
            button.setAutoRaise(True)
            button.setArrowType(QtCore.Qt.ArrowType.NoArrow)

        self._selected_modified_desc_index = 0
        self._selected_complete_desc_index = 0
        self._modified_actions = []
        self._complete_actions = []

        self._create_action_groups()
        self._reset_default_action_on_status_button()

        self.initializing = False

    @override
    def _query_changed(self, text):
        """
        Emits the filterChanged signal, with the addition of the AlbumStatusState
        for the modified and complete filter buttons
        """
        self.filterChanged.emit(
            text,
            self.selected_filters,
            MODIFIED_FILTER_DESCRIPTORS[self.selected_modified_desc_index].state,
            COMPLETE_FILTER_DESCRIPTORS[self.selected_complete_desc_index].state,
        )

    @override
    def clear(self):
        super().clear()
        self._reset_default_action_on_status_button()

    @property
    def selected_modified_desc_index(self) -> int:
        return self._selected_modified_desc_index

    @selected_modified_desc_index.setter
    def selected_modified_desc_index(self, index: int):
        self._selected_modified_desc_index = index

    @property
    def selected_complete_desc_index(self) -> int:
        return self._selected_complete_desc_index

    @selected_complete_desc_index.setter
    def selected_complete_desc_index(self, index: int):
        self._selected_complete_desc_index = index

    def _get_saved_modified_filter_desc(self) -> AlbumStatusFilterDescriptor:
        config = get_config()
        temp = config.persist[self._saved_modified_key]
        if temp is not None:
            temp = AlbumStatusState(temp)
            for modified_filter_desc in MODIFIED_FILTER_DESCRIPTORS:
                if temp == modified_filter_desc.state:
                    return modified_filter_desc
        return MODIFIED_FILTER_DESCRIPTORS[0]

    def _get_saved_complete_filter_desc(self) -> AlbumStatusFilterDescriptor:
        config = get_config()
        temp = config.persist[self._saved_complete_key]
        if temp is not None:
            temp = AlbumStatusState(temp)
            for complete_filter_desc in COMPLETE_FILTER_DESCRIPTORS:
                if temp == complete_filter_desc.state:
                    return complete_filter_desc
        return COMPLETE_FILTER_DESCRIPTORS[0]

    def _status_button_trigger(self, filter_data: ActionFilterTriggerData, _checked: bool):
        try:
            trigged_action_idx = filter_data.action_group.index(filter_data.triggered_action)
        except ValueError:
            # Set to last index, so that the tool button cycles to the first action (N/A)
            trigged_action_idx = len(filter_data.action_group) - 1

        next_action_idx = (trigged_action_idx + 1) % len(filter_data.action_group)
        if filter_data.selected_filter_index_prop.fset:
            filter_data.selected_filter_index_prop.fset(self, next_action_idx)
        self._set_status_button_action(filter_data.button, filter_data.action_group[next_action_idx])

        # Get the selected status state based on the relative next action index from the beginning of the filter state list
        selected_filter_state = next(islice(filter_data.filter_descs, next_action_idx, None))
        config = get_config()
        config.persist[filter_data.status_config_key] = selected_filter_state.state
        self._query_changed(self.filter_query_box.text())

    def _create_action_groups(self):
        # Find the layout child to add the modified and complete buttons to
        layout = None
        for child_widget in self.children():
            if isinstance(child_widget, QtWidgets.QHBoxLayout):
                layout = child_widget
                break

        if not layout:
            raise Exception(
                "Album Filter is requires layout member in order to add complete and modified filter buttons"
            )

        self._modified_actions = []
        self._complete_actions = []

        for config_key, action_group, tool_button, filter_states, selected_filter_index_prop in [
            (
                self._saved_modified_key,
                self._modified_actions,
                self._modified_button,
                MODIFIED_FILTER_DESCRIPTORS,
                __class__.selected_modified_desc_index,
            ),
            (
                self._saved_complete_key,
                self._complete_actions,
                self._complete_button,
                COMPLETE_FILTER_DESCRIPTORS,
                __class__.selected_complete_desc_index,
            ),
        ]:
            for filter_state in filter_states:
                action_group.append(QAction())
                action_group[-1].setIcon(filter_state.icon_provider())
                action_group[-1].setIconText(filter_state.text)
                action_group[-1].setToolTip(filter_state.tooltip)
                action_group[-1].setStatusTip(filter_state.tooltip)
                _ = action_group[-1].triggered.connect(
                    partial(
                        self._status_button_trigger,
                        ActionFilterTriggerData(
                            config_key,
                            tool_button,
                            action_group[-1],
                            action_group,
                            filter_states,
                            selected_filter_index_prop,
                        ),
                    )
                )
                layout.addWidget(tool_button)

    def _reset_default_action_on_status_button(self):
        self._selected_modified_desc_index = 0
        self._selected_complete_desc_index = 0
        for selected_status_desc, filter_state_descs, selected_filter_index_prop, action_group, tool_button in [
            (
                self._get_saved_modified_filter_desc(),
                MODIFIED_FILTER_DESCRIPTORS,
                __class__.selected_modified_desc_index,
                self._modified_actions,
                self._modified_button,
            ),
            (
                self._get_saved_complete_filter_desc(),
                COMPLETE_FILTER_DESCRIPTORS,
                __class__.selected_complete_desc_index,
                self._complete_actions,
                self._complete_button,
            ),
        ]:
            try:
                selected_idx = [filter_state_desc.state for filter_state_desc in filter_state_descs].index(
                    selected_status_desc.state
                )
            except ValueError:
                # Defaults to the 0th index(N/A value) in the descriptor list
                selected_idx = 0
            if selected_filter_index_prop.fset:
                selected_filter_index_prop.fset(
                    self,
                    selected_idx,
                )
            self._set_status_button_action(tool_button, action_group[selected_idx])

    def _set_status_button_action(self, button: QtWidgets.QToolButton, action: QAction):
        button.setDefaultAction(action)


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
