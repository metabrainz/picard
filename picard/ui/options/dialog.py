# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009 Nikolai Prokoschenko
# Copyright (C) 2008-2009, 2018-2021 Philipp Wolfer
# Copyright (C) 2011 Pavan Chander
# Copyright (C) 2011-2012, 2019 Wieland Hoffmann
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013, 2017-2021 Laurent Monin
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Suhas
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2021 Bob Swift
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


from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard import log
from picard.config import (
    ListOption,
    TextOption,
    get_config,
)
from picard.util import restore_method

from picard.ui import (
    HashableTreeWidgetItem,
    PicardDialog,
    SingletonDialog,
)
from picard.ui.options import (  # noqa: F401 # pylint: disable=unused-import
    OptionsCheckError,
    _pages as page_classes,
    advanced,
    cdlookup,
    cover,
    fingerprinting,
    general,
    genres,
    interface,
    interface_colors,
    interface_top_tags,
    matching,
    metadata,
    network,
    plugins,
    ratings,
    releases,
    renaming,
    scripting,
    tags,
    tags_compatibility_aac,
    tags_compatibility_ac3,
    tags_compatibility_id3,
    tags_compatibility_wave,
)
from picard.ui.util import StandardButton


class OptionsDialog(PicardDialog, SingletonDialog):

    options = [
        TextOption("persist", "options_last_active_page", ""),
        ListOption("persist", "options_pages_tree_state", []),
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
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

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
        self.ui.buttonbox.helpRequested.connect(self.show_help)

        self.pages = []
        for Page in page_classes:
            try:
                page = Page(self.ui.pages_stack)
                self.pages.append(page)
            except Exception:
                log.exception('Failed initializing options page %r', page)
        self.item_to_page = {}
        self.page_to_item = {}
        self.default_item = None
        if not default_page:
            config = get_config()
            default_page = config.persist["options_last_active_page"]
        self.add_pages(None, default_page, self.ui.pages_tree)

        # work-around to set optimal option pane width
        self.ui.pages_tree.expandAll()
        max_page_name = self.ui.pages_tree.sizeHintForColumn(0) + 2*self.ui.pages_tree.frameWidth()
        self.ui.dialog_splitter.setSizes([max_page_name, self.geometry().width() - max_page_name])

        self.ui.pages_tree.setHeaderLabels([""])
        self.ui.pages_tree.header().hide()
        self.ui.pages_tree.itemSelectionChanged.connect(self.switch_page)

        self.restoreWindowState()
        self.finished.connect(self.saveWindowState)

        for page in self.pages:
            try:
                page.load()
            except Exception:
                log.exception('Failed loading options page %r', page)
                self.disable_page(page.NAME)
        self.ui.pages_tree.setCurrentItem(self.default_item)

    def switch_page(self):
        items = self.ui.pages_tree.selectedItems()
        if items:
            config = get_config()
            page = self.item_to_page[items[0]]
            config.persist["options_last_active_page"] = page.NAME
            self.ui.pages_stack.setCurrentWidget(page)

    def disable_page(self, name):
        item = self.page_to_item[name]
        item.setDisabled(True)

    @property
    def help_url(self):
        current_page = self.ui.pages_stack.currentWidget()
        url = current_page.HELP_URL
        # If URL is empty, use the first non empty parent help URL.
        while current_page.PARENT and not url:
            current_page = self.item_to_page[self.page_to_item[current_page.PARENT]]
            url = current_page.HELP_URL
        if not url:
            url = 'doc_options'  # key in PICARD_URLS
        return url

    def accept(self):
        for page in self.pages:
            try:
                page.check()
            except OptionsCheckError as e:
                self._show_page_error(page, e)
                return
            except Exception as e:
                log.exception('Failed checking options page %r', page)
                self._show_page_error(page, e)
                return
        for page in self.pages:
            try:
                page.save()
            except Exception as e:
                log.exception('Failed saving options page %r', page)
                self._show_page_error(page, e)
                return
        config = get_config()
        selected_user_profile = config.persist["selected_user_profile"]
        profiles = config.persist["user_profiles"]
        if selected_user_profile in profiles:
            profiles[selected_user_profile]['settings'] = config.setting.as_dict()
            config.persist["user_profiles"] = profiles
        else:
            log.error('Unable to update user profile "%s"', selected_user_profile)
        super().accept()

    def _show_page_error(self, page, error):
        if not isinstance(error, OptionsCheckError):
            error = OptionsCheckError(_('Unexpected error'), str(error))
        self.ui.pages_tree.setCurrentItem(self.page_to_item[page.NAME])
        page.display_error(error)

    def saveWindowState(self):
        expanded_pages = []
        for page, item in self.page_to_item.items():
            index = self.ui.pages_tree.indexFromItem(item)
            is_expanded = self.ui.pages_tree.isExpanded(index)
            expanded_pages.append((page, is_expanded))
        config = get_config()
        config.persist["options_pages_tree_state"] = expanded_pages

    @restore_method
    def restoreWindowState(self):
        config = get_config()
        pages_tree_state = config.persist["options_pages_tree_state"]
        if not pages_tree_state:
            self.ui.pages_tree.expandAll()
        else:
            for page, is_expanded in pages_tree_state:
                try:
                    item = self.page_to_item[page]
                except KeyError:
                    continue
                item.setExpanded(is_expanded)

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
        message_box = QtWidgets.QMessageBox(self)
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        message_box.setWindowModality(QtCore.Qt.WindowModal)
        message_box.setWindowTitle(_("Confirm Reset"))
        message_box.setText(_("Are you sure?") + "\n\n" + msg)
        message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if message_box.exec_() == QtWidgets.QMessageBox.Yes:
            function()
