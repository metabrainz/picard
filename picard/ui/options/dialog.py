# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009 Nikolai Prokoschenko
# Copyright (C) 2008-2009, 2018-2022 Philipp Wolfer
# Copyright (C) 2011 Pavan Chander
# Copyright (C) 2011-2012, 2019 Wieland Hoffmann
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013, 2017-2022 Laurent Monin
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Suhas
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021-2022 Bob Swift
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

from PyQt6 import (
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
from picard.profile import UserProfileGroups
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
    interface_toolbar,
    interface_top_tags,
    maintenance,
    matching,
    metadata,
    network,
    plugins,
    profiles,
    ratings,
    releases,
    renaming,
    renaming_compat,
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
        TextOption('persist', 'options_last_active_page', ''),
        ListOption('persist', 'options_pages_tree_state', []),
    ]

    suspend_signals = False

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
                item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            self.add_pages(page.NAME, default_page, item)
            if page.NAME == default_page:
                self.default_item = item
            items.append(item)
        if not self.default_item and not parent:
            self.default_item = items[0]

    def __init__(self, default_page=None, parent=None):
        super().__init__(parent)
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        from picard.ui.ui_options import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.reset_all_button = QtWidgets.QPushButton(_("&Restore all Defaults"))
        self.ui.reset_all_button.setToolTip(_("Reset all of Picard's settings"))
        self.ui.reset_button = QtWidgets.QPushButton(_("Restore &Defaults"))
        self.ui.reset_button.setToolTip(_("Reset all settings for current option page"))

        ok = StandardButton(StandardButton.OK)
        ok.setText(_("Make It So!"))
        self.ui.buttonbox.addButton(ok, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.CANCEL), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.HELP), QtWidgets.QDialogButtonBox.ButtonRole.HelpRole)
        self.ui.buttonbox.addButton(self.ui.reset_all_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        self.ui.buttonbox.addButton(self.ui.reset_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

        self.ui.buttonbox.accepted.connect(self.accept)
        self.ui.buttonbox.rejected.connect(self.reject)
        self.ui.reset_all_button.clicked.connect(self.confirm_reset_all)
        self.ui.reset_button.clicked.connect(self.confirm_reset)
        self.ui.buttonbox.helpRequested.connect(self.show_help)

        self.ui.attached_profiles_button = QtWidgets.QPushButton(_("Attached Profiles"))
        self.ui.attached_profiles_button.setToolTip(_("Show which profiles are attached to the options on this page"))
        self.ui.buttonbox.addButton(self.ui.attached_profiles_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        self.ui.attached_profiles_button.clicked.connect(self.show_attached_profiles_dialog)

        config = get_config()

        self.pages = []
        for Page in page_classes:
            try:
                page = Page(self.ui.pages_stack)
                page.set_dialog(self)
                self.pages.append(page)
            except Exception:
                log.exception("Failed initializing options page %r", Page)
        self.item_to_page = {}
        self.page_to_item = {}
        self.default_item = None
        if not default_page:
            default_page = config.persist['options_last_active_page']
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

        self.load_all_pages()
        self.ui.pages_tree.setCurrentItem(self.default_item)

        self.profile_page = self.get_page('profiles')
        self.profile_page.signal_refresh.connect(self.update_from_profile_changes)

        self.maintenance_page = self.get_page('maintenance')
        self.maintenance_page.signal_reload.connect(self.load_all_pages)

        self.first_enter = True
        self.installEventFilter(self)

        self.highlight_enabled_profile_options()
        current_page = self.item_to_page[self.ui.pages_tree.currentItem()]
        self.set_profiles_button_and_highlight(current_page)

    def load_all_pages(self):
        for page in self.pages:
            try:
                page.load()
            except Exception:
                log.exception("Failed loading options page %r", page)
                self.disable_page(page.NAME)

    def page_has_profile_options(self, page):
        try:
            name = page.PARENT if page.PARENT in UserProfileGroups.SETTINGS_GROUPS else page.NAME
        except AttributeError:
            return False
        return name in UserProfileGroups.get_setting_groups_list()

    def show_attached_profiles_dialog(self):
        window_title = _("Profiles Attached to Options")
        items = self.ui.pages_tree.selectedItems()
        if not items:
            return
        page = self.item_to_page[items[0]]
        if not self.page_has_profile_options(page):
            message_box = QtWidgets.QMessageBox(self)
            message_box.setIcon(QtWidgets.QMessageBox.Icon.Information)
            message_box.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            message_box.setWindowTitle(window_title)
            message_box.setText(_("The options on this page are not currently available to be managed using profiles."))
            message_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            return message_box.exec()

        option_group = page.PARENT if page.PARENT in UserProfileGroups.SETTINGS_GROUPS else page.NAME
        override_profiles = self.profile_page._clean_and_get_all_profiles()
        override_settings = self.profile_page.profile_settings
        profile_dialog = AttachedProfilesDialog(
            parent=self,
            option_group=option_group,
            override_profiles=override_profiles,
            override_settings=override_settings
        )
        profile_dialog.show()
        profile_dialog.raise_()
        profile_dialog.activateWindow()

    def _get_profile_title_from_id(self, profile_id):
        config = get_config()
        for item in config.profiles[SettingConfigSection.PROFILES_KEY]:
            if item['id'] == profile_id:
                return item['title']
        return _('Unknown profile')

    def update_from_profile_changes(self):
        if not self.suspend_signals:
            self.highlight_enabled_profile_options(load_settings=True)

    def get_working_profile_data(self):
        profile_page = self.get_page('profiles')
        working_profiles = profile_page._clean_and_get_all_profiles()
        if working_profiles is None:
            working_profiles = []
        working_settings = profile_page.profile_settings
        return working_profiles, working_settings

    def highlight_enabled_profile_options(self, load_settings=False):
        working_profiles, working_settings = self.get_working_profile_data()

        HighlightColors = namedtuple('HighlightColors', ('fg', 'bg'))
        HIGHLIGHT_FMT = "#%s { color: %s; background-color: %s; }"
        if theme.is_dark_theme:
            option_colors = HighlightColors('#FFFFFF', '#000080')
        else:
            option_colors = HighlightColors('#000000', '#F9F906')

        for page in self.pages:
            page_name = page.PARENT if page.PARENT in UserProfileGroups.SETTINGS_GROUPS else page.NAME
            if page_name in UserProfileGroups.SETTINGS_GROUPS:
                if load_settings:
                    page.load()
                for opt in UserProfileGroups.SETTINGS_GROUPS[page_name]['settings']:
                    for opt_field in opt.fields:
                        style = HIGHLIGHT_FMT % (opt_field, option_colors.fg, option_colors.bg)
                        try:
                            obj = getattr(page.ui, opt_field)
                        except AttributeError:
                            continue
                        self._check_and_highlight_option(obj, opt.name, working_profiles, working_settings, style)

    def _check_and_highlight_option(self, obj, option_name, working_profiles, working_settings, style):
        obj.setStyleSheet(None)
        obj.setToolTip(None)
        for item in working_profiles:
            if item['enabled']:
                profile_id = item['id']
                profile_title = item['title']
                if profile_id in working_settings:
                    profile_settings = working_settings[profile_id]
                else:
                    profile_settings = {}
                if option_name in profile_settings:
                    tooltip = _("This option will be saved to profile: %s") % profile_title
                    try:
                        obj.setStyleSheet(style)
                        obj.setToolTip(tooltip)
                    except AttributeError:
                        pass
                    break

    def eventFilter(self, object, event):
        """Process selected events.
        """
        evtype = event.type()
        if evtype == QtCore.QEvent.Type.Enter:
            if self.first_enter:
                self.first_enter = False
                if self.tagger and self.tagger.window.script_editor_dialog is not None:
                    self.get_page('filerenaming').show_script_editing_page()
                    self.activateWindow()
        return False

    def get_page(self, name):
        return self.item_to_page[self.page_to_item[name]]

    def page_has_attached_profiles(self, page, enabled_profiles_only=False):
        if not self.page_has_profile_options(page):
            return False
        working_profiles, working_settings = self.get_working_profile_data()
        page_name = page.PARENT if page.PARENT in UserProfileGroups.SETTINGS_GROUPS else page.NAME
        for opt in UserProfileGroups.SETTINGS_GROUPS[page_name]['settings']:
            for item in working_profiles:
                if enabled_profiles_only and not item["enabled"]:
                    continue
                profile_id = item['id']
                if opt.name in working_settings[profile_id]:
                    return True
        return False

    def set_profiles_button_and_highlight(self, page):
        if self.page_has_attached_profiles(page):
            self.ui.attached_profiles_button.setDisabled(False)
        else:
            self.ui.attached_profiles_button.setDisabled(True)
        self.ui.pages_stack.setCurrentWidget(page)

    def switch_page(self):
        items = self.ui.pages_tree.selectedItems()
        if items:
            config = get_config()
            page = self.item_to_page[items[0]]
            config.persist['options_last_active_page'] = page.NAME
            self.set_profiles_button_and_highlight(page)

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
                log.exception("Failed checking options page %r", page)
                self._show_page_error(page, e)
                return
        self.profile_page.save()
        for page in self.pages:
            try:
                if page != self.profile_page:
                    page.save()
            except Exception as e:
                log.exception("Failed saving options page %r", page)
                self._show_page_error(page, e)
                return
        super().accept()

    def _show_page_error(self, page, error):
        if not isinstance(error, OptionsCheckError):
            error = OptionsCheckError(_("Unexpected error"), str(error))
        self.ui.pages_tree.setCurrentItem(self.page_to_item[page.NAME])
        page.display_error(error)

    def saveWindowState(self):
        expanded_pages = []
        for page, item in self.page_to_item.items():
            index = self.ui.pages_tree.indexFromItem(item)
            is_expanded = self.ui.pages_tree.isExpanded(index)
            expanded_pages.append((page, is_expanded))
        config = get_config()
        config.persist['options_pages_tree_state'] = expanded_pages
        config.setting.set_profiles_override()
        config.setting.set_settings_override()

    @restore_method
    def restoreWindowState(self):
        config = get_config()
        pages_tree_state = config.persist['options_pages_tree_state']
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
        self.suspend_signals = True
        for page in self.pages:
            try:
                page.restore_defaults()
            except Exception as e:
                log.error("Failed restoring all defaults for page %r: %s", page, e)
        self.highlight_enabled_profile_options(load_settings=False)
        self.suspend_signals = False

    def restore_page_defaults(self):
        self.ui.pages_stack.currentWidget().restore_defaults()
        self.highlight_enabled_profile_options(load_settings=False)

    def confirm_reset(self):
        msg = _("You are about to reset your options for this page.")
        self._show_dialog(msg, self.restore_page_defaults)

    def confirm_reset_all(self):
        msg = _("Warning! This will reset all of your settings.")
        self._show_dialog(msg, self.restore_all_defaults)

    def _show_dialog(self, msg, function):
        message_box = QtWidgets.QMessageBox(self)
        message_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        message_box.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        message_box.setWindowTitle(_("Confirm Reset"))
        message_box.setText(_("Are you sure?") + "\n\n" + msg)
        message_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if message_box.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            function()


class AttachedProfilesDialog(PicardDialog):
    NAME = 'attachedprofiles'
    TITLE = N_("Attached Profiles")

    def __init__(self, parent=None, option_group=None, override_profiles=None, override_settings=None):
        super().__init__(parent=parent)
        self.option_group = option_group
        self.ui = Ui_AttachedProfilesDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.addButton(StandardButton(StandardButton.CLOSE), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        self.ui.buttonBox.rejected.connect(self.close_window)

        config = get_config()
        if override_profiles is None or override_settings is None:
            self.profiles = config.profiles[SettingConfigSection.PROFILES_KEY]
            self.settings = config.profiles[SettingConfigSection.SETTINGS_KEY]
        else:
            self.profiles = override_profiles
            self.settings = override_settings

        self.populate_table()

        self.ui.buttonBox.setFocus()
        self.setModal(True)

    def populate_table(self):
        model = QtGui.QStandardItemModel()
        model.setColumnCount(2)
        header_names = [_("Option"), _("Attached Profiles")]
        model.setHorizontalHeaderLabels(header_names)

        group = UserProfileGroups.SETTINGS_GROUPS[self.option_group]
        group_title = group['title']
        group_options = group['settings']

        window_title = _("Profiles Attached to Options in %s Section") % group_title
        self.setWindowTitle(window_title)

        for name, title, object_name in group_options:
            option_item = QtGui.QStandardItem(_(title))
            option_item.setEditable(False)
            row = [option_item]
            attached = []
            for profile in self.profiles:
                if name in self.settings[profile['id']]:
                    attached.append("{0}{1}".format(profile['title'], _(" [Enabled]") if profile['enabled'] else "",))
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
