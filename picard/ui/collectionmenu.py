# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2018 Philipp Wolfer
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

import locale

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.collection import (
    load_user_collections,
    user_collections,
)


class CollectionMenu(QtWidgets.QMenu):

    def __init__(self, albums, *args):
        super().__init__(*args)
        self.ids = set(a.id for a in albums)
        self._ignore_update = False
        self.update_collections()

    def update_collections(self):
        self._ignore_update = True
        self.clear()
        self.actions = []
        for id_, collection in sorted(user_collections.items(),
                                      key=lambda k_v:
                                      (locale.strxfrm(str(k_v[1])), k_v[0])):
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
        load_user_collections(self.update_collections)

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
            style.pixelMetric(QtWidgets.QStyle.PM_LayoutLeftMargin),
            style.pixelMetric(QtWidgets.QStyle.PM_FocusFrameVMargin),
            style.pixelMetric(QtWidgets.QStyle.PM_LayoutRightMargin),
            style.pixelMetric(QtWidgets.QStyle.PM_FocusFrameVMargin))
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
        palette.setColor(QtGui.QPalette.WindowText, textcolor)
        self.checkbox.setPalette(palette)

    def enterEvent(self, e):
        self.menu.update_active_action_for_widget(self)

    def leaveEvent(self, e):
        self.set_active(False)

    def paintEvent(self, e):
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionMenuItem()
        option.initFrom(self)
        option.state = QtWidgets.QStyle.State_None
        if self.isEnabled():
            option.state |= QtWidgets.QStyle.State_Enabled
        if self.active:
            option.state |= QtWidgets.QStyle.State_Selected
        painter.drawControl(QtWidgets.QStyle.CE_MenuItem, option)


class CollectionCheckBox(QtWidgets.QCheckBox):

    def __init__(self, parent, menu, collection):
        self.menu = menu
        self.collection = collection
        super().__init__(self.label(), parent)

        releases = collection.releases & menu.ids
        if len(releases) == len(menu.ids):
            self.setCheckState(QtCore.Qt.Checked)
        elif not releases:
            self.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.setCheckState(QtCore.Qt.PartiallyChecked)

    def nextCheckState(self):
        ids = self.menu.ids
        if ids & self.collection.pending:
            return
        diff = ids - self.collection.releases
        if diff:
            self.collection.add_releases(diff, self.updateText)
            self.setCheckState(QtCore.Qt.Checked)
        else:
            self.collection.remove_releases(ids & self.collection.releases, self.updateText)
            self.setCheckState(QtCore.Qt.Unchecked)

    def updateText(self):
        self.setText(self.label())

    def label(self):
        c = self.collection
        return ngettext("%s (%i release)", "%s (%i releases)", c.size) % (c.name, c.size)
