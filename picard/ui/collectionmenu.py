# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2014-2015, 2018, 2020-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018, 2022-2023 Philipp Wolfer
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


from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.collection import (
    load_user_collections,
    user_collections,
)
from picard.i18n import (
    gettext as _,
    ngettext,
)
from picard.util import strxfrm


class CollectionMenu(QtWidgets.QMenu):

    def __init__(self, albums, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.releases = set(a.id for a in albums)
        self._ignore_update = False
        self._update_collections()

    def _update_collections(self):
        self._ignore_update = True
        self.clear()
        self.actions = []
        for collection in sorted(user_collections.values(),
                                 key=lambda c: (strxfrm(c.name), c.id)):
            action = QtWidgets.QWidgetAction(self)
            action.setDefaultWidget(CollectionMenuItem(self, collection))
            self.addAction(action)
            self.actions.append(action)
        self._ignore_update = False
        self.addSeparator()
        self.refresh_action = self.addAction(_("Refresh List"))
        self.hovered.connect(self.update_highlight)

    def refresh_list(self):
        self.refresh_action.setEnabled(False)
        load_user_collections(self._update_collections)

    def mouseReleaseEvent(self, event):
        # Not using self.refresh_action.triggered because it closes the menu
        if self.actionAt(event.pos()) == self.refresh_action and self.refresh_action.isEnabled():
            self.refresh_list()

    def update_highlight(self, action):
        if self._ignore_update:
            return
        for a in self.actions:
            a.defaultWidget().set_active(a == action)

    def update_active_action_for_widget(self, widget):
        if self._ignore_update:
            return
        for action in self.actions:
            action_widget = action.defaultWidget()
            is_active = action_widget == widget
            if is_active:
                self._ignore_hover = True
                self.setActiveAction(action)
                self._ignore_hover = False
            action_widget.set_active(is_active)


class CollectionMenuItem(QtWidgets.QWidget):

    def __init__(self, menu, collection):
        super().__init__()
        self.menu = menu
        self.active = False
        self._setup_layout(menu, collection)
        self._setup_colors()

    def _setup_layout(self, menu, collection):
        layout = QtWidgets.QVBoxLayout(self)
        style = self.style()
        layout.setContentsMargins(
            style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_LayoutLeftMargin),
            style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_FocusFrameVMargin),
            style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_LayoutRightMargin),
            style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_FocusFrameVMargin))
        self.checkbox = CollectionCheckBox(self, menu, collection)
        layout.addWidget(self.checkbox)

    def _setup_colors(self):
        palette = self.palette()
        self.text_color = palette.text().color()
        self.highlight_color = palette.highlightedText().color()

    def set_active(self, active):
        self.active = active
        palette = self.palette()
        textcolor = self.highlight_color if active else self.text_color
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, textcolor)
        self.checkbox.setPalette(palette)

    def enterEvent(self, e):
        self.menu.update_active_action_for_widget(self)

    def leaveEvent(self, e):
        self.set_active(False)

    def paintEvent(self, e):
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionMenuItem()
        option.initFrom(self)
        option.state = QtWidgets.QStyle.StateFlag.State_None
        if self.isEnabled():
            option.state |= QtWidgets.QStyle.StateFlag.State_Enabled
        if self.active:
            option.state |= QtWidgets.QStyle.StateFlag.State_Selected
        painter.drawControl(QtWidgets.QStyle.ControlElement.CE_MenuItem, option)


class CollectionCheckBox(QtWidgets.QCheckBox):

    def __init__(self, parent, menu, collection):
        self.menu = menu
        self.collection = collection
        super().__init__(self.label(), parent)

        releases = collection.releases & menu.releases
        if len(releases) == len(menu.releases):
            self.setCheckState(QtCore.Qt.CheckState.Checked)
        elif not releases:
            self.setCheckState(QtCore.Qt.CheckState.Unchecked)
        else:
            self.setCheckState(QtCore.Qt.CheckState.PartiallyChecked)

    def nextCheckState(self):
        releases = self.menu.releases
        if releases & self.collection.pending_releases:
            return
        diff = releases - self.collection.releases
        if diff:
            self.collection.add_releases(diff, self.updateText)
            self.setCheckState(QtCore.Qt.CheckState.Checked)
        else:
            self.collection.remove_releases(releases & self.collection.releases, self.updateText)
            self.setCheckState(QtCore.Qt.CheckState.Unchecked)

    def updateText(self):
        self.setText(self.label())

    def label(self):
        c = self.collection
        return ngettext("%(name)s (%(count)i release)", "%(name)s (%(count)i releases)", c.size) % {
            'name': c.name,
            'count': c.size,
        }
