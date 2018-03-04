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

from PyQt5 import QtCore, QtWidgets
from picard import config
from picard.util import webbrowser2, restore_method
from picard.ui import PicardDialog, HashableTreeWidgetItem
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
    network,
    scripting,
    tags,
    fingerprinting,
    OptionsCheckError,
    _pages as page_classes
)


class OptionsDialog(PicardDialog):

    defaultsize = QtCore.QSize(560, 400)
    autorestore = False

    options = [
        config.Option("persist", "options_splitter", QtCore.QByteArray()),
    ]

    def add_pages(self, parent, default_page, parent_item):
        pages = [(p.SORT_ORDER, p.NAME, p) for p in self.pages if p.PARENT == parent]
        items = []
        for foo, bar, page in sorted(pages):
            item = HashableTreeWidgetItem(parent_item)
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
        super().__init__(parent)

        from picard.ui.ui_options import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.reset_all_button = QtWidgets.QPushButton(_("&Restore all Defaults"))
        self.ui.reset_all_button.setToolTip(_("Reset all of Picard's settings"))
        self.ui.reset_button = QtWidgets.QPushButton(_("Restore &Defaults"))
        self.ui.reset_button.setToolTip(_("Reset all settings for current option page"))

        ok = StandardButton(StandardButton.OK)
        ok.setText(_("Make It So!"))
        self.ui.buttonbox.addButton(ok, QtWidgets.QDialogButtonBox.AcceptRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.CANCEL), QtWidgets.QDialogButtonBox.RejectRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.HELP), QtWidgets.QDialogButtonBox.HelpRole)
        self.ui.buttonbox.addButton(self.ui.reset_all_button, QtWidgets.QDialogButtonBox.ActionRole)
        self.ui.buttonbox.addButton(self.ui.reset_button, QtWidgets.QDialogButtonBox.ActionRole)

        self.ui.buttonbox.accepted.connect(self.accept)
        self.ui.buttonbox.rejected.connect(self.reject)
        self.ui.reset_all_button.clicked.connect(self.confirm_reset_all)
        self.ui.reset_button.clicked.connect(self.confirm_reset)
        self.ui.buttonbox.helpRequested.connect(self.help)

        self.pages = []
        for Page in page_classes:
            page = Page(self.ui.pages_stack)
            self.pages.append(page)
        self.item_to_page = {}
        self.page_to_item = {}
        self.default_item = None
        self.add_pages(None, default_page, self.ui.pages_tree)

        # work-around to set optimal option pane width
        self.ui.pages_tree.expandAll()
        max_page_name = self.ui.pages_tree.sizeHintForColumn(0) + 2*self.ui.pages_tree.frameWidth()
        self.ui.pages_tree.collapseAll()
        self.ui.splitter.setSizes([max_page_name,
                                   self.geometry().width() - max_page_name])

        self.ui.pages_tree.setHeaderLabels([""])
        self.ui.pages_tree.header().hide()
        self.ui.pages_tree.itemSelectionChanged.connect(self.switch_page)

        self.restoreWindowState()
        self.finished.connect(self.saveWindowState)

        for page in self.pages:
            page.load()
        self.ui.pages_tree.setCurrentItem(self.default_item)

    def switch_page(self):
        items = self.ui.pages_tree.selectedItems()
        if items:
            page = self.item_to_page[items[0]]
            self.ui.pages_stack.setCurrentWidget(page)

    def help(self):
        webbrowser2.goto('doc_options')

    def accept(self):
        for page in self.pages:
            try:
                page.check()
            except OptionsCheckError as e:
                self.ui.pages_tree.setCurrentItem(self.page_to_item[page.NAME])
                page.display_error(e)
                return
        for page in self.pages:
            page.save()
        super().accept()

    def saveWindowState(self):
        config.persist["options_splitter"] = self.ui.splitter.saveState()

    @restore_method
    def restoreWindowState(self):
        self.restore_geometry()
        self.ui.splitter.restoreState(config.persist["options_splitter"])

    def restore_all_defaults(self):
        for page in self.pages:
            page.restore_defaults()

    def restore_page_defaults(self):
        self.ui.pages_stack.currentWidget().restore_defaults()

    def confirm_reset(self):
        msg = _("You are about to reset your options for this page.")
        self._show_dialog(msg, self.restore_page_defaults)

    def confirm_reset_all(self):
        msg = _("Warning! This will reset all of your settings.")
        self._show_dialog(msg, self.restore_all_defaults)

    def _show_dialog(self, msg, function):
        message_box = QtWidgets.QMessageBox()
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        message_box.setWindowModality(QtCore.Qt.WindowModal)
        message_box.setWindowTitle(_("Confirm Reset"))
        message_box.setText(_("Are you sure?") + "\n\n" + msg)
        message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if message_box.exec_() == QtWidgets.QMessageBox.Yes:
            function()
