# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2013 Michael Wiencek
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

from PyQt4 import QtCore, QtGui
from picard.collection import user_collections, load_user_collections


class CollectionMenu(QtGui.QMenu):

    def __init__(self, albums, *args):
        QtGui.QMenu.__init__(self, *args)
        self.ids = set(a.id for a in albums)
        self.actions_by_id = {}
        self.separator = self.addSeparator()
        self.refresh_action = self.addAction(_("Refresh List"))
        self.update_collections()

    def update_collections(self):
        for id, collection in user_collections.iteritems():
            action = self.actions_by_id.get(collection.id)
            if action:
                action.defaultWidget().updateText()
            else:
                action = QtGui.QWidgetAction(self)
                action.setDefaultWidget(CollectionCheckBox(self, collection))
                self.insertAction(self.separator, action)
                self.actions_by_id[collection.id] = action

        for id, action in self.actions_by_id.items():
            if id not in user_collections:
                self.removeAction(action)
                del self.actions_by_id[id]

    def refresh_list(self):
        self.refresh_action.setEnabled(False)
        load_user_collections(self.update_collections)

    def mouseReleaseEvent(self, event):
        # Not using self.refresh_action.triggered because it closes the menu
        if self.actionAt(event.pos()) == self.refresh_action and self.refresh_action.isEnabled():
            self.refresh_list()


class CollectionCheckBox(QtGui.QCheckBox):

    def __init__(self, menu, collection):
        self.menu = menu
        self.collection = collection
        QtGui.QCheckBox.__init__(self, self.label())

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
        return ungettext("%s (%i release)", "%s (%i releases)", c.size) % (c.name, c.size)
