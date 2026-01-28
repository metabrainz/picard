# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013 Michael Wiencek
# Copyright (C) 2014-2015, 2018, 2020-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018, 2022-2024 Philipp Wolfer
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
    sort_key,
)

from picard.ui.widgets.checkboxmenuitem import CheckboxMenuItem


class CollectionMenu(QtWidgets.QMenu):
    def __init__(self, albums, title, parent=None):
        super().__init__(title, parent=parent)
        self.releases = set(a.id for a in albums)
        self._ignore_update = False
        self._ignore_hover = False
        self._update_collections()

    def _update_collections(self):
        self._ignore_update = True
        self.clear()
        self.actions = []
        for collection in sorted(user_collections.values(), key=lambda c: (sort_key(c.name), c.id)):
            action = QtWidgets.QWidgetAction(self)
            action.setDefaultWidget(CollectionMenuItem(self, action, collection))
            self.addAction(action)
            self.actions.append(action)
        self._ignore_update = False
        self.addSeparator()
        self.refresh_action = self.addAction(_("Refresh List"))

    def _refresh_list(self):
        self.refresh_action.setEnabled(False)
        load_user_collections(self._update_collections)

    def mouseReleaseEvent(self, event):
        # Not using self.refresh_action.triggered because it closes the menu
        if self.actionAt(event.pos()) == self.refresh_action and self.refresh_action.isEnabled():
            self._refresh_list()


class CollectionMenuItem(CheckboxMenuItem):
    def __init__(self, menu, action, collection, parent=None):
        self._collection = collection
        super().__init__(menu, action, "", parent=parent)
        self._setup_layout(menu, collection)
        # The CollectionCheckBox handles everything. Don't set the action to checkable
        # to avoid double rendering of the checkbox element.
        action.setCheckable(False)

    def _setup_layout(self, menu, collection):
        # Use a checkbox widget for rendering the menu item content. This is needed
        # for supporting the tristate checkbox behavior when selecting multiple releases.
        layout = QtWidgets.QVBoxLayout(self)
        style = self.style()
        lmargin = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_LayoutLeftMargin)
        rmargin = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_LayoutRightMargin)
        layout.setContentsMargins(lmargin, 0, rmargin, 0)
        self._checkbox = CollectionCheckBox(menu, collection)
        layout.addWidget(self._checkbox)

    def _create_checkbox_widget(self, text: str):
        return CollectionCheckBox(self._menu, self._collection, parent=self)

    def set_active(self, active: bool):
        super().set_active(active)
        palette = self.palette()
        if active:
            textcolor = palette.highlightedText().color()
        else:
            textcolor = palette.text().color()
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, textcolor)
        self._checkbox.setPalette(palette)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() in {QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Space}:
            self._checkbox.nextCheckState()
            event.accept()
        else:
            super().keyPressEvent(event)


class CollectionCheckBox(QtWidgets.QCheckBox):
    def __init__(self, menu, collection, parent=None):
        self.menu = menu
        self.collection = collection
        super().__init__(self._label(), parent=parent)

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
            self.collection.add_releases(diff, self._update_text)
            self.setCheckState(QtCore.Qt.CheckState.Checked)
        else:
            self.collection.remove_releases(releases & self.collection.releases, self._update_text)
            self.setCheckState(QtCore.Qt.CheckState.Unchecked)

    def _update_text(self):
        self.setText(self._label())

    def _label(self):
        c = self.collection
        return ngettext("%(name)s (%(count)i release)", "%(name)s (%(count)i releases)", c.size) % {
            'name': c.name,
            'count': c.size,
        }
