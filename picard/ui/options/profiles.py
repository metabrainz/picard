# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2022-2023 Philipp Wolfer
# Copyright (C) 2022-2024 Laurent Monin
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


from copy import deepcopy
import uuid

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard import log
from picard.config import (
    Option,
    OptionError,
    SettingConfigSection,
    get_config,
)
from picard.const import DEFAULT_COPY_TEXT
from picard.i18n import (
    N_,
    gettext as _,
    gettext_constants,
)
from picard.profile import UserProfileGroups
from picard.script import get_file_naming_script_presets
from picard.util import get_base_title

from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_profiles import Ui_ProfileEditorDialog
from picard.ui.util import qlistwidget_items
from picard.ui.widgets.profilelistwidget import ProfileListWidgetItem


class ProfilesOptionsPage(OptionsPage):

    NAME = 'profiles'
    TITLE = N_("Option Profiles")
    PARENT = None
    SORT_ORDER = 10
    ACTIVE = True
    HELP_URL = "/config/options_profiles.html"

    TREEWIDGETITEM_COLUMN = 0

    signal_refresh = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ProfileEditorDialog()
        self.ui.setupUi(self)
        self.make_buttons()

        self.ui.profile_editor_splitter.setStretchFactor(1, 1)
        self.move_view = MoveableListView(self.ui.profile_list, self.ui.move_up_button,
                                          self.ui.move_down_button)

        self.ui.profile_list.itemChanged.connect(self.profile_item_changed)
        self.ui.profile_list.currentItemChanged.connect(self.current_item_changed)
        self.ui.profile_list.itemChanged.connect(self.reload_all_page_settings)
        self.ui.settings_tree.itemChanged.connect(self.set_profile_settings_changed)
        self.ui.settings_tree.itemExpanded.connect(self.update_current_expanded_items_list)
        self.ui.settings_tree.itemCollapsed.connect(self.update_current_expanded_items_list)

        self.current_profile_id = None
        self.expanded_sections = set()
        self.building_tree = False

        self.loading = False
        self.settings_changed = False
        self.ui.settings_tree.installEventFilter(self)

    def eventFilter(self, object, event):
        """Process selected events.
        """
        event_type = event.type()
        if event_type == QtCore.QEvent.Type.FocusOut and object == self.ui.settings_tree:
            if self.settings_changed:
                self.settings_changed = False
                self.update_values_in_profile_options()
                self.reload_all_page_settings()
        return False

    def make_buttons(self):
        """Make buttons and add them to the button bars.
        """
        self.new_profile_button = QtWidgets.QPushButton(_("New"))
        self.new_profile_button.setToolTip(_("Create a new profile"))
        self.new_profile_button.clicked.connect(self.new_profile)
        self.ui.profile_list_buttonbox.addButton(self.new_profile_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

        self.copy_profile_button = QtWidgets.QPushButton(_("Copy"))
        self.copy_profile_button.setToolTip(_("Copy to a new profile"))
        self.copy_profile_button.clicked.connect(self.copy_profile)
        self.ui.profile_list_buttonbox.addButton(self.copy_profile_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

        self.delete_profile_button = QtWidgets.QPushButton(_("Delete"))
        self.delete_profile_button.setToolTip(_("Delete the profile"))
        self.delete_profile_button.clicked.connect(self.delete_profile)
        self.ui.profile_list_buttonbox.addButton(self.delete_profile_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

    def restore_defaults(self):
        """Remove all profiles and profile settings.
        """
        self.ui.profile_list.clear()
        self.profile_settings = {}
        self.profile_selected()
        self.update_config_overrides()
        self.reload_all_page_settings()

    def load(self):
        """Load initial configuration.
        """
        self.loading = True
        config = get_config()
        # Use deepcopy() to avoid changes made locally from being cascaded into `config.profiles`
        # before the user clicks "Make It So!"
        self.profile_settings = deepcopy(config.profiles[SettingConfigSection.SETTINGS_KEY])

        self.ui.profile_list.clear()
        for profile in config.profiles[SettingConfigSection.PROFILES_KEY]:
            list_item = ProfileListWidgetItem(profile['title'], profile['enabled'], profile['id'])
            self.ui.profile_list.addItem(list_item)

        # Select the last selected profile item
        self.expanded_sections = set(config.persist['profile_settings_tree_expanded_list'])
        last_selected_profile_pos = config.persist['last_selected_profile_pos']
        self.make_setting_tree(settings=self._last_settings(last_selected_profile_pos))
        self.update_config_overrides()
        self.loading = False

    def _last_settings(self, last_selected_profile_pos):
        """Select last profile item and returns associated settings or None"""
        last = self.ui.profile_list.item(last_selected_profile_pos)
        if not last:
            return None
        self.ui.profile_list.setCurrentItem(last)
        last.setSelected(True)
        self.current_profile_id = last.profile_id
        return self.get_settings_for_profile(last.profile_id)

    def update_config_overrides(self):
        """Update the profile overrides used in `config.settings` when retrieving or
        saving a setting.
        """
        config = get_config()
        config.setting.set_profiles_override(self._clean_and_get_all_profiles())
        config.setting.set_settings_override(self.profile_settings)

    def get_settings_for_profile(self, profile_id):
        """Get the settings for the specified profile ID.  Automatically adds an empty
        settings dictionary if there is no settings dictionary found for the ID.

        Args:
            profile_id (str): ID of the profile

        Returns:
            dict: Profile settings
        """
        # Add empty settings dictionary if no dictionary found for the profile.
        # This happens when a new profile is created.
        if profile_id not in self.profile_settings:
            self.profile_settings[profile_id] = {}
        return self.profile_settings[profile_id]

    def _all_profiles(self):
        """Get all profiles from the profiles list in order from top to bottom.

        Yields:
            dict: Profile information in a format for saving to the user settings
        """
        for item in qlistwidget_items(self.ui.profile_list):
            yield item.get_dict()

    def make_setting_tree(self, settings=None):
        """Update the profile settings tree based on the settings provided.
        If no settings are provided, displays an empty tree.

        Args:
            settings (dict, optional): Dictionary of settings for the profile. Defaults to None.
        """
        self.set_button_states()
        self.ui.settings_tree.clear()
        self.ui.settings_tree.setHeaderItem(QtWidgets.QTreeWidgetItem())
        self.ui.settings_tree.setHeaderLabels([_("Settings to include in profile")])
        if settings is None:
            return
        self.building_tree = True
        for group in UserProfileGroups.values():
            title = group['title']
            group_settings = group['settings']
            widget_item = QtWidgets.QTreeWidgetItem([title])
            widget_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsAutoTristate)
            widget_item.setCheckState(self.TREEWIDGETITEM_COLUMN, QtCore.Qt.CheckState.Unchecked)
            for setting in group_settings:
                try:
                    opt_title = Option.get_title('setting', setting.name)
                except OptionError as e:
                    log.debug(e)
                    continue
                if opt_title is None:
                    opt_title = setting.name
                    log.debug("Missing title for option: %s", setting.name)
                widget_item.addChild(self._make_child_item(settings, setting.name, opt_title))
            self.ui.settings_tree.addTopLevelItem(widget_item)
            if title in self.expanded_sections:
                widget_item.setExpanded(True)
        self.building_tree = False

    def _make_child_item(self, settings, name, title):
        in_settings = settings and name in settings
        item = QtWidgets.QTreeWidgetItem([_(title)])
        item.setData(0, QtCore.Qt.ItemDataRole.UserRole, name)
        item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
        state = QtCore.Qt.CheckState.Checked if in_settings else QtCore.Qt.CheckState.Unchecked
        item.setCheckState(self.TREEWIDGETITEM_COLUMN, state)
        tooltip = self.make_setting_value_text(name, settings[name] if in_settings else None)
        item.setToolTip(self.TREEWIDGETITEM_COLUMN, tooltip)
        return item

    def _get_naming_script(self, config, value):
        if value in config.setting['file_renaming_scripts']:
            return config.setting['file_renaming_scripts'][value]['title']
        presets = {x['id']: x['title'] for x in get_file_naming_script_presets()}
        if value in presets:
            return presets[value]
        return _("Unknown script")

    def _get_scripts_list(self, scripts):
        enabled_scripts = ['<li>%s</li>' % name for (pos, name, enabled, script) in scripts if enabled]
        if not enabled_scripts:
            return _("No enabled scripts")
        return _("Enabled scripts:") + '<ul>' + "".join(enabled_scripts) + '</ul>'

    def _get_ca_providers_list(self, providers):
        enabled_providers = ['<li>%s</li>' % name for (name, enabled) in providers if enabled]
        if not enabled_providers:
            return _("No enabled providers")
        return _("Enabled providers:") + '<ul>' + "".join(enabled_providers) + '</ul>'

    def make_setting_value_text(self, key, value):
        config = get_config()
        if value is None:
            return _("None")
        if key == 'selected_file_naming_script_id':
            return self._get_naming_script(config, value)
        if key == 'list_of_scripts':
            return self._get_scripts_list(config.setting[key])
        if key == 'ca_providers':
            return self._get_ca_providers_list(config.setting[key])
        if isinstance(value, str):
            return '"%s"' % value
        if type(value) in {bool, int, float}:
            return str(value)
        if type(value) in {set, tuple, list, dict}:
            return _("List of %i items") % len(value)
        return _("Unknown value format")

    def update_current_expanded_items_list(self):
        """Update the list of expanded sections in the settings tree for persistent settings.
        """
        if self.building_tree:
            return
        self.expanded_sections = set()
        for i in range(self.ui.settings_tree.topLevelItemCount()):
            tl_item = self.ui.settings_tree.topLevelItem(i)
            if tl_item.isExpanded():
                self.expanded_sections.add(tl_item.text(self.TREEWIDGETITEM_COLUMN))

    def get_current_selected_item(self):
        """Gets the profile item currently selected in the profiles list.

        Returns:
            ProfileListWidgetItem: Currently selected item
        """
        items = self.ui.profile_list.selectedItems()
        if items:
            return items[0]
        return None

    def profile_selected(self, update_settings=True):
        """Update working profile information for the selected item in the profiles list.

        Args:
            update_settings (bool, optional): Update settings tree. Defaults to True.
        """
        item = self.get_current_selected_item()
        if item:
            profile_id = item.profile_id
            self.current_profile_id = profile_id
            if update_settings:
                settings = self.get_settings_for_profile(profile_id)
                self.make_setting_tree(settings=settings)
        else:
            self.current_profile_id = None
            self.make_setting_tree(settings=None)

    def reload_all_page_settings(self):
        """Trigger a reload of the settings and highlights for all pages containing
        options that can be managed in a profile.
        """
        self.signal_refresh.emit()

    def update_values_in_profile_options(self):
        """Update the current profile's settings dictionary from the settings tree.  Note
        that this update is delayed to avoid losing a profile's option setting value when
        a selected option (with an associated value) is de-selected and then re-selected.
        """
        if not self.current_profile_id:
            return
        checked_items = set(self.get_checked_items_from_tree())
        settings = set(self.profile_settings[self.current_profile_id].keys())

        # Add new items to settings
        for item in checked_items.difference(settings):
            self.profile_settings[self.current_profile_id][item] = None

        # Remove unchecked items from settings
        for item in settings.difference(checked_items):
            del self.profile_settings[self.current_profile_id][item]

    def profile_item_changed(self, item):
        """Check title is not blank and remove leading and trailing spaces.

        Args:
            item (ProfileListWidgetItem): Item that changed
        """
        if not self.loading:
            text = item.text().strip()
            if not text:
                QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Icon.Warning,
                    _("Invalid Title"),
                    _("The profile title cannot be blank."),
                    QtWidgets.QMessageBox.StandardButton.Ok,
                    self
                ).exec()
                item.setText(self.ui.profile_list.unique_profile_name())
            elif text != item.text():
                # Remove leading and trailing spaces from new title.
                item.setText(text)
            self.update_config_overrides()
            self.reload_all_page_settings()

    def current_item_changed(self, new_item, old_item):
        """Update the display when a new item is selected in the profile list.

        Args:
            new_item (ProfileListWidgetItem): Newly selected item
            old_item (ProfileListWidgetItem): Previously selected item
        """
        if self.loading:
            return
        # Set self.loading to avoid looping through the `.currentItemChanged` event.
        self.loading = True
        self.ui.profile_list.setCurrentItem(new_item)
        self.loading = False
        self.profile_selected()

    def get_checked_items_from_tree(self):
        """Get the keys for the settings that are checked in the profile settings tree.

        Yields:
            str: Settings key
        """
        for i in range(self.ui.settings_tree.topLevelItemCount()):
            tl_item = self.ui.settings_tree.topLevelItem(i)
            for j in range(tl_item.childCount()):
                item = tl_item.child(j)
                if item.checkState(self.TREEWIDGETITEM_COLUMN) == QtCore.Qt.CheckState.Checked:
                    yield item.data(self.TREEWIDGETITEM_COLUMN, QtCore.Qt.ItemDataRole.UserRole)

    def set_profile_settings_changed(self):
        """Set flag to trigger option page updates later (when focus is lost from the settings
        tree) to avoid updating after each change to the settings selected for a profile.
        """
        if self.current_profile_id:
            self.settings_changed = True

    def copy_profile(self):
        """Make a copy of the currently selected profile.
        """
        item = self.get_current_selected_item()
        profile_id = str(uuid.uuid4())
        settings = deepcopy(self.profile_settings[self.current_profile_id])
        self.profile_settings[profile_id] = settings
        base_title = "%s %s" % (get_base_title(item.name), gettext_constants(DEFAULT_COPY_TEXT))
        name = self.ui.profile_list.unique_profile_name(base_title)
        self.ui.profile_list.add_profile(name=name, profile_id=profile_id)
        self.update_config_overrides()
        self.reload_all_page_settings()

    def new_profile(self):
        """Add a new profile with no settings selected.
        """
        self.ui.profile_list.add_profile()
        self.update_config_overrides()
        self.reload_all_page_settings()

    def delete_profile(self):
        """Delete the current profile.
        """
        self.ui.profile_list.remove_selected_profile()
        self.profile_selected()
        self.update_config_overrides()
        self.reload_all_page_settings()

    def _clean_and_get_all_profiles(self):
        """Returns the list of profiles, adds any missing profile settings, and removes any "orphan"
        profile settings (i.e. settings dictionaries not associated with an existing profile).

        Returns:
            list: List of profiles suitable for storing in `config.profiles`.
        """
        all_profiles = list(self._all_profiles())
        all_profile_ids = set(x['id'] for x in all_profiles)
        keys = set(self.profile_settings.keys())
        # Add any missing profile settings
        for profile_id in all_profile_ids.difference(keys):
            self.profile_settings[profile_id] = {}
        # Remove any "orphan" profile settings
        for profile_id in keys.difference(all_profile_ids):
            del self.profile_settings[profile_id]
        return all_profiles

    def save(self):
        """Save any changes to the current profile's settings, and save all updated
        profile information to the user settings.
        """
        config = get_config()
        config.profiles[SettingConfigSection.PROFILES_KEY] = self._clean_and_get_all_profiles()
        config.profiles[SettingConfigSection.SETTINGS_KEY] = self.profile_settings
        config.persist['last_selected_profile_pos'] = self.ui.profile_list.currentRow()
        config.persist['profile_settings_tree_expanded_list'] = sorted(self.expanded_sections)

    def set_button_states(self):
        """Set the enabled / disabled states of the buttons.
        """
        state = self.current_profile_id is not None
        self.copy_profile_button.setEnabled(state)
        self.delete_profile_button.setEnabled(state)


register_options_page(ProfilesOptionsPage)
