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


from collections import namedtuple

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.config import (
    ListOption,
    SettingConfigSection,
    TextOption,
    get_config,
)
from picard.profile import (
    USER_SETTINGS_PROFILE_ID,
    UserProfileGroups,
)
from picard.util import (
    restore_method,
    webbrowser2,
)

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
from picard.ui.theme import theme
from picard.ui.ui_options_attached_profiles import Ui_AttachedProfilesDialog
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

        profile_help = StandardButton(StandardButton.HELP)
        profile_help.setText(_("Profile Help"))
        self.ui.profiles_buttonbox.addButton(profile_help, QtWidgets.QDialogButtonBox.HelpRole)
        self.ui.profiles_buttonbox.helpRequested.connect(self.show_profile_help)

        self.ui.attached_profiles_button = QtWidgets.QPushButton(_("Attached Profiles"))
        self.ui.attached_profiles_button.setToolTip(_("Show which profiles are attached to the options on this page"))
        self.ui.profiles_buttonbox.addButton(self.ui.attached_profiles_button, QtWidgets.QDialogButtonBox.ActionRole)
        self.ui.attached_profiles_button.clicked.connect(self.show_attached_profiles_dialog)

        config = get_config()

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

        self.USER_SETTINGS_TITLE = _("User base settings")

        if config.profiles[SettingConfigSection.PROFILES_KEY]:
            self.ui.profile_frame.show()
            self.ui.save_to_profile.clear()
            self.ui.save_to_profile.addItem(self.USER_SETTINGS_TITLE, USER_SETTINGS_PROFILE_ID)
            index = 0
            for idx, item in enumerate(config.profiles[SettingConfigSection.PROFILES_KEY], start=1):
                self.ui.save_to_profile.addItem(item["title"], item["id"],)
                if not index and item["enabled"]:
                    index = idx
            self.ui.save_to_profile.currentIndexChanged.connect(self.switch_profile)
            self.ui.save_to_profile.setCurrentIndex(index)
        else:
            self.ui.profile_frame.hide()

    def show_profile_help(self):
        """Open the profile documentation in a browser.
        """
        webbrowser2.open('doc_profile_edit')

    def show_attached_profiles_dialog(self):
        window_title = _("Profiles Attached to Options")
        items = self.ui.pages_tree.selectedItems()
        if items:
            page = self.item_to_page[items[0]]
            name = page.NAME
        else:
            name = ''
        if name not in UserProfileGroups.get_setting_groups_list():
            message_box = QtWidgets.QMessageBox(self)
            message_box.setIcon(QtWidgets.QMessageBox.Information)
            message_box.setWindowModality(QtCore.Qt.WindowModal)
            message_box.setWindowTitle(window_title)
            message_box.setText(_("The options on this page are not currently available to be managed using profiles."))
            message_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            return message_box.exec_()

        profile_dialog = AttachedProfilesDialog(parent=self, option_group=name)
        profile_dialog.show()
        profile_dialog.raise_()
        profile_dialog.activateWindow()

    def _get_profile_title_from_id(self, profile_id):
        if profile_id == USER_SETTINGS_PROFILE_ID:
            return self.USER_SETTINGS_TITLE
        config = get_config()
        for item in config.profiles[SettingConfigSection.PROFILES_KEY]:
            if item["id"] == profile_id:
                return item["title"]
        return _('Unknown profile')

    def switch_profile(self, index):
        HighlightColors = namedtuple('HighlightColors', ('fg', 'bg'))
        highlight = "#%s { color: %s; background-color: %s; }"
        if theme.is_dark_theme:
            option_colors = HighlightColors('#FFFFFF', '#000080')
            profile_colors = HighlightColors('#FFFFFF', '#300000')
        else:
            option_colors = HighlightColors('#000000', '#F9F906')
            profile_colors = HighlightColors('#000000', '#FFA500')

        # Highlight profile selector if profile selected.
        if self.ui.save_to_profile.currentIndex():
            self.ui.save_to_profile.setStyleSheet(highlight % ('save_to_profile', profile_colors.fg, profile_colors.bg))
        else:
            self.ui.save_to_profile.setStyleSheet("")

        profile_id = self.ui.save_to_profile.currentData()
        profile_title = self._get_profile_title_from_id(profile_id)
        config = get_config()
        config.setting.set_profile(profile_id)
        settings = config.profiles[SettingConfigSection.SETTINGS_KEY]
        if profile_id in settings:
            profile_settings = settings[profile_id]
        else:
            profile_settings = {}

        for page in self.pages:
            page.load()
            page_name = page.PARENT if page.PARENT in UserProfileGroups.SETTINGS_GROUPS else page.NAME
            if page_name in UserProfileGroups.SETTINGS_GROUPS:
                for opt in UserProfileGroups.SETTINGS_GROUPS[page_name]['settings']:
                    for opt_field in opt.fields:
                        try:
                            obj = getattr(page.ui, opt_field)
                        except AttributeError:
                            continue
                        if opt.name in profile_settings:
                            style = highlight % (opt_field, option_colors.fg, option_colors.bg)
                            tooltip = _("This option is managed by profile: %s") % profile_title
                        else:
                            style = ""
                            tooltip = ""
                        try:
                            obj.setStyleSheet(style)
                            obj.setToolTip(tooltip)
                        except AttributeError:
                            pass

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
        profile_id = self.ui.save_to_profile.currentData()
        if profile_id != USER_SETTINGS_PROFILE_ID:
            profile_name = self._get_profile_title_from_id(profile_id)
            message_box = QtWidgets.QMessageBox(self)
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setWindowModality(QtCore.Qt.WindowModal)
            message_box.setWindowTitle(_("Save to Profile"))
            message_box.setText(_("Changes will only be saved to the profile: \"%s\"\n\nDo you want to continue?") % profile_name)
            message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
            if message_box.exec_() != QtWidgets.QMessageBox.Yes:
                return
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
        self.reset_profile()
        super().accept()

    def reject(self):
        self.reset_profile()
        super().reject()

    @staticmethod
    def reset_profile():
        config = get_config()
        config.setting.set_profile()

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


class AttachedProfilesDialog(PicardDialog):
    NAME = 'attachedprofiles'
    TITLE = N_('Attached Profiles')

    def __init__(self, parent=None, option_group=None):
        super().__init__(parent=parent)
        self.option_group = option_group
        self.ui = Ui_AttachedProfilesDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.addButton(StandardButton(StandardButton.CLOSE), QtWidgets.QDialogButtonBox.RejectRole)
        self.ui.buttonBox.rejected.connect(self.close_window)

        self.populate_table()

        self.ui.buttonBox.setFocus()
        self.setModal(True)

    def populate_table(self):
        model = QtGui.QStandardItemModel()
        model.setColumnCount(2)
        header_names = [_("Option Setting"), _("Attached Profiles")]
        model.setHorizontalHeaderLabels(header_names)

        config = get_config()
        profiles = config.profiles[SettingConfigSection.PROFILES_KEY]
        settings = config.profiles[SettingConfigSection.SETTINGS_KEY]

        group = UserProfileGroups.SETTINGS_GROUPS[self.option_group]
        group_title = group["title"]
        group_options = group["settings"]

        window_title = _("Profiles Attached to Options in %s Section") % group_title
        self.setWindowTitle(window_title)

        for name, title in group_options:
            option_item = QtGui.QStandardItem(_(title))
            option_item.setEditable(False)
            row = [option_item]
            attached = []
            for profile in profiles:
                if name in settings[profile["id"]]:
                    attached.append("{0}{1}".format(profile["title"], _(" [Enabled]") if profile["enabled"] else "",))
            attached_profiles = "\n".join(attached) if attached else _("None")
            profile_item = QtGui.QStandardItem(attached_profiles)
            profile_item.setEditable(False)
            row.append(profile_item)
            model.appendRow(row)

        self.ui.options_list.setModel(model)
        self.ui.options_list.resizeColumnsToContents()
        self.ui.options_list.resizeRowsToContents()
        self.ui.options_list.horizontalHeader().setStretchLastSection(True)

    def close_window(self):
        """Close the script metadata editor window.
        """
        self.close()
