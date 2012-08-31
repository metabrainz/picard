# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2007 Lukáš Lalinský
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
from picard.config import Option
from picard.plugin import ExtensionPoint
from picard.util import webbrowser2
from picard.ui.util import StandardButton
from picard.ui.options import (
    about,
    advanced,
    cdlookup,
    cover,
    general,
    interface,
    folksonomy,
    ratings,
    matching,
    metadata,
    releases,
    renaming,
    plugins,
    proxy,
    scripting,
    tags,
    fingerprinting,
    OptionsCheckError,
    _pages as page_classes
)


class OptionsDialog(QtGui.QDialog):

    options = [
        Option("persist", "options_position", QtCore.QPoint(), QtCore.QVariant.toPoint),
        Option("persist", "options_size", QtCore.QSize(560, 400), QtCore.QVariant.toSize),
        Option("persist", "options_splitter", QtCore.QByteArray(), QtCore.QVariant.toByteArray),
    ]

    def add_pages(self, parent, default_page, parent_item):
        pages = [(p.SORT_ORDER, p.NAME, p) for p in self.pages if p.PARENT == parent]
        items = []
        for foo, bar, page in sorted(pages):
            item = QtGui.QTreeWidgetItem(parent_item)
            item.setText(0, _(page.TITLE))
            if page.ACTIVE:
                self.item_to_page[item] = page
                self.page_to_item[page.NAME] = item
                self.ui.pages_stack.addWidget(page)
            else:
                item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.add_pages(page.NAME, default_page, item)
            if page.NAME == default_page:
                self.default_item = item
            items.append(item)
        if not self.default_item and not parent:
            self.default_item = items[0]

    def __init__(self, default_page=None, parent=None):
        QtGui.QDialog.__init__(self, parent)

        from picard.ui.ui_options import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.buttonbox.addButton(StandardButton(StandardButton.OK), QtGui.QDialogButtonBox.AcceptRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.CANCEL), QtGui.QDialogButtonBox.RejectRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.HELP), QtGui.QDialogButtonBox.HelpRole)
        self.ui.buttonbox.accepted.connect(self.accept)
        self.ui.buttonbox.rejected.connect(self.reject)
        self.ui.buttonbox.helpRequested.connect(self.help)

        self.pages = []
        for Page in page_classes:
            page = Page(self.ui.pages_stack)
            self.pages.append(page)
        self.item_to_page = {}
        self.page_to_item = {}
        self.default_item = None
        self.add_pages(None, default_page, self.ui.pages_tree)

        self.ui.pages_tree.setHeaderLabels([""])
        self.ui.pages_tree.header().hide()
        self.ui.pages_tree.itemSelectionChanged.connect(self.switch_page)

        self.restoreWindowState()

        for page in self.pages:
            page.load()
        self.ui.pages_tree.setCurrentItem(self.default_item)

    def switch_page(self):
        items = self.ui.pages_tree.selectedItems()
        if items:
            page = self.item_to_page[items[0]]
            self.ui.pages_stack.setCurrentWidget(page)

    def help(self):
        webbrowser2.open('http://musicbrainz.org/doc/Picard_Documentation/Options')

    def accept(self):
        for page in self.pages:
            try:
                page.check()
            except OptionsCheckError, e:
                self.ui.pages_tree.setCurrentItem(self.page_to_item[page.NAME])
                page.display_error(e)
                return
        for page in self.pages:
            page.save()
        self.saveWindowState()
        QtGui.QDialog.accept(self)

    def closeEvent(self, event):
        self.saveWindowState()
        event.accept()

    def saveWindowState(self):
        pos = self.pos()
        if not pos.isNull():
            self.config.persist["options_position"] = pos
        self.config.persist["options_size"] = self.size()
        self.config.persist["options_splitter"] = self.ui.splitter.saveState()

    def restoreWindowState(self):
        pos = self.config.persist["options_position"]
        if pos.x() > 0 and pos.y() > 0:
            self.move(pos)
        self.resize(self.config.persist["options_size"])
        self.ui.splitter.restoreState(self.config.persist["options_splitter"])
