# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
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


from copy import deepcopy
import uuid

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard.config import (
    IntOption,
    ListOption,
    SettingConfigSection,
    get_config,
)
from picard.const import PICARD_URLS
from picard.profile import UserProfileGroups

from picard.ui import (
    PicardDialog,
    SingletonDialog,
)
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import OptionsPage
from picard.ui.ui_profileeditor import Ui_ProfileEditorDialog
from picard.ui.widgets.profilelistwidget import ProfileListWidgetItem


class ProfileEditorDialog(SingletonDialog, PicardDialog):
    """User Profile Editor Page
    """
    TITLE = N_("User profile editor")
    STYLESHEET_ERROR = OptionsPage.STYLESHEET_ERROR

    help_url = PICARD_URLS["doc_profile_edit"]

    PROFILES_KEY = SettingConfigSection.PROFILES_KEY
    SETTINGS_KEY = SettingConfigSection.SETTINGS_KEY
    POSITION_KEY = "last_selected_profile_pos"
    EXPANDED_KEY = "profile_settings_tree_expanded_list"

    TREEWIDGETITEM_COLUMN = 0

    options = [
        IntOption("persist", POSITION_KEY, 0),
        ListOption("persist", EXPANDED_KEY, [])
    ]

    signal_save = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """User profile editor.
        """
        super().__init__(parent)

        self.main_window = parent

        self.setWindowTitle(_(self.TITLE))
        self.displaying = False
        self.loading = True
        self.ui = Ui_ProfileEditorDialog()
        self.ui.setupUi(self)
        self.setModal(True)

        self.make_buttons()

        self.ui.profile_editor_splitter.setStretchFactor(1, 1)
        self.move_view = MoveableListView(self.ui.profile_list, self.ui.move_up_button,
                                          self.ui.move_down_button)

        self.ui.profile_list.currentItemChanged.connect(self.current_item_changed)
        self.ui.profile_list.itemSelectionChanged.connect(self.item_selection_changed)
        self.ui.settings_tree.itemChanged.connect(self.save_profile)
        self.ui.settings_tree.expanded.connect(self.update_current_expanded_items_list)

        self.current_profile_id = None
        self.expanded_sections = []
        self.building_tree = False

        self.load()
        self.loading = False

    def make_buttons(self):
        """Make buttons and add them to the button bars.
        """
        self.make_it_so_button = QtWidgets.QPushButton(_("Make It So!"))
        self.make_it_so_button.setToolTip(_("Save all profile information to the user settings"))
        self.ui.buttonbox.addButton(self.make_it_so_button, QtWidgets.QDialogButtonBox.AcceptRole)
        self.ui.buttonbox.accepted.connect(self.make_it_so)

        self.new_profile_button = QtWidgets.QPushButton(_('New'))
        self.new_profile_button.setToolTip(_("Create a new profile"))
        self.new_profile_button.clicked.connect(self.new_profile)
        self.ui.profile_list_buttonbox.addButton(self.new_profile_button, QtWidgets.QDialogButtonBox.ActionRole)

        self.copy_profile_button = QtWidgets.QPushButton(_('Copy'))
        self.copy_profile_button.setToolTip(_("Copy to a new profile"))
        self.copy_profile_button.clicked.connect(self.copy_profile)
        self.ui.profile_list_buttonbox.addButton(self.copy_profile_button, QtWidgets.QDialogButtonBox.ActionRole)

        self.delete_profile_button = QtWidgets.QPushButton(_('Delete'))
        self.delete_profile_button.setToolTip(_("Delete the profile"))
        self.delete_profile_button.clicked.connect(self.delete_profile)
        self.ui.profile_list_buttonbox.addButton(self.delete_profile_button, QtWidgets.QDialogButtonBox.ActionRole)

        self.cancel_button = QtWidgets.QPushButton(_('Cancel'))
        self.cancel_button.setToolTip(_("Close the profile editor without saving changes to the profiles"))
        self.ui.buttonbox.addButton(self.cancel_button, QtWidgets.QDialogButtonBox.RejectRole)
        self.ui.buttonbox.rejected.connect(self.close)

        self.ui.buttonbox.addButton(QtWidgets.QDialogButtonBox.Help)
        self.ui.buttonbox.helpRequested.connect(self.show_help)

    def load(self):
        """Load initial configuration.
        """
        config = get_config()
        # Use deepcopy() to avoid changes made locally from being cascaded into `config.profiles`
        # before the user clicks "Make It So!"
        self.profile_settings = deepcopy(config.profiles[self.SETTINGS_KEY])

        for profile in config.profiles[self.PROFILES_KEY]:
            list_item = ProfileListWidgetItem(profile['title'], profile['enabled'], profile['id'])
            self.ui.profile_list.addItem(list_item)

        # Select the last selected profile item
        last_selected_profile_pos = config.persist[self.POSITION_KEY]
        self.expanded_sections = config.persist[self.EXPANDED_KEY]
        last_selected_profile = self.ui.profile_list.item(last_selected_profile_pos)
        settings = None
        if last_selected_profile:
            self.ui.profile_list.setCurrentItem(last_selected_profile)
            last_selected_profile.setSelected(True)
            id = last_selected_profile.profile_id
            self.current_profile_id = id
            settings = self.get_settings_for_profile(id)
        self.make_setting_tree(settings=settings)

    def get_settings_for_profile(self, id):
        """Get the settings for the specified profile ID.  Automatically adds an empty
        settings dictionary if there is no settings dictionary found for the ID.

        Args:
            id (str): ID of the profile

        Returns:
            dict: Profile settings
        """
        # Add empty settings dictionary if no dictionary found for the profile.
        # This happens when a new profile is created.
        if id not in self.profile_settings:
            self.profile_settings[id] = {}
        return self.profile_settings[id]

    def get_current_selected_item(self):
        """Gets the profile item currently selected in the profiles list.

        Returns:
            ProfileListWidgetItem: Currently selected item
        """
        items = self.ui.profile_list.selectedItems()
        if items:
            return items[0]
        return None

    def update_current_expanded_items_list(self):
        if self.building_tree:
            return
        self.expanded_sections = []
        for i in range(self.ui.settings_tree.topLevelItemCount()):
            tl_item = self.ui.settings_tree.topLevelItem(i)
            if tl_item.isExpanded():
                self.expanded_sections.append(tl_item.text(self.TREEWIDGETITEM_COLUMN))

    def profile_selected(self, update_settings=True):
        """Update working profile information for the selected item in the profiles list.

        Args:
            update_settings (bool, optional): Update settings tree. Defaults to True.
        """
        item = self.get_current_selected_item()
        if item:
            id = item.profile_id
            self.current_profile_id = id
            if update_settings:
                settings = self.get_settings_for_profile(id)
                self.make_setting_tree(settings=settings)
        else:
            self.current_profile_id = None
            self.make_setting_tree(settings=None)

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
        for id, group in UserProfileGroups.SETTINGS_GROUPS.items():
            title = group["title"]
            group_settings = group["settings"]
            widget_item = QtWidgets.QTreeWidgetItem([title])
            widget_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsAutoTristate)
            widget_item.setCheckState(self.TREEWIDGETITEM_COLUMN, QtCore.Qt.Unchecked)
            for setting in group_settings:
                child_item = QtWidgets.QTreeWidgetItem([_(setting.title)])
                child_item.setData(0, QtCore.Qt.UserRole, setting.name)
                child_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
                state = QtCore.Qt.Checked if settings and setting.name in settings else QtCore.Qt.Unchecked
                child_item.setCheckState(self.TREEWIDGETITEM_COLUMN, state)
                widget_item.addChild(child_item)
            self.ui.settings_tree.addTopLevelItem(widget_item)
            if title in self.expanded_sections:
                widget_item.setExpanded(True)
        self.building_tree = False

    def current_item_changed(self, new_item, old_item):
        """Update the display when a new item is selected in the profile list.

        Args:
            new_item (ProfileListWidgetItem): Newly selected item
            old_item (ProfileListWidgetItem): Previously selected item
        """
        if self.loading:
            return

        self.save_profile()
        self.set_current_item(new_item)
        self.profile_selected()

    def item_selection_changed(self):
        """Set tree list highlight bar to proper line if selection change canceled.
        """
        item = self.ui.profile_list.currentItem()
        if item:
            item.setSelected(True)

    def set_current_item(self, item):
        """Sets the specified item as the current selection in the profiles list.

        Args:
            item (ProfileListWidgetItem): Item to set as current selection
        """
        self.loading = True
        self.ui.profile_list.setCurrentItem(item)
        self.loading = False

    def save_profile(self):
        """Save changes to the currently selected profile.
        """
        checked_items = set(self.get_checked_items_from_tree())
        settings = set(self.profile_settings[self.current_profile_id].keys())

        # Add new items to settings
        for item in checked_items.difference(settings):
            self.profile_settings[self.current_profile_id][item] = None

        # Remove unchecked items from settings
        for item in settings.difference(checked_items):
            del self.profile_settings[self.current_profile_id][item]

    def copy_profile(self):
        """Make a copy of the currently selected profile.
        """
        item = self.get_current_selected_item()
        id = str(uuid.uuid4())
        settings = deepcopy(self.profile_settings[self.current_profile_id])
        self.profile_settings[id] = settings
        name = _("%s (copy)") % item.name
        self.ui.profile_list.add_profile(name=name, profile_id=id)

    def new_profile(self):
        """Add a new profile with no settings selected.
        """
        self.ui.profile_list.add_profile()

    def delete_profile(self):
        """Delete the current profile.
        """
        self.ui.profile_list.remove_selected_profile()
        self.profile_selected()

    def make_it_so(self):
        """Save any changes to the current profile's settings, save all updated profile
        information to the user settings, and close the profile editor dialog.
        """
        all_profiles = list(self._all_profiles())
        all_profile_ids = set(x['id'] for x in all_profiles)
        keys = set(self.profile_settings.keys())
        for id in keys.difference(all_profile_ids):
            del self.profile_settings[id]

        config = get_config()
        config.profiles[self.PROFILES_KEY] = all_profiles
        config.profiles[self.SETTINGS_KEY] = self.profile_settings

        self.main_window.enable_renaming_action.setChecked(config.setting["rename_files"])
        self.main_window.enable_moving_action.setChecked(config.setting["move_files"])
        self.main_window.enable_tag_saving_action.setChecked(not config.setting["dont_write_tags"])

        self.close()

    def closeEvent(self, event):
        """Custom close event handler to save editor settings.
        """
        config = get_config()
        config.persist[self.POSITION_KEY] = self.ui.profile_list.currentRow()
        config.persist[self.EXPANDED_KEY] = self.expanded_sections
        super().closeEvent(event)

    def _all_profiles(self):
        """Get all profiles from the profiles list in order from top to bottom.

        Yields:
            dict: Profile information in a format for saving to the user settings
        """
        for row in range(self.ui.profile_list.count()):
            item = self.ui.profile_list.item(row)
            yield item.get_dict()

    def set_button_states(self):
        """Set the enabled / disabled states of the buttons.
        """
        state = self.current_profile_id is not None
        self.copy_profile_button.setEnabled(state)
        self.delete_profile_button.setEnabled(state)

    def get_checked_items_from_tree(self):
        """Get the keys for the settings that are checked in the profile settings tree.

        Yields:
            str: Settings key
        """
        for i in range(self.ui.settings_tree.topLevelItemCount()):
            tl_item = self.ui.settings_tree.topLevelItem(i)
            for j in range(tl_item.childCount()):
                item = tl_item.child(j)
                if item.checkState(self.TREEWIDGETITEM_COLUMN) == QtCore.Qt.Checked:
                    yield item.data(self.TREEWIDGETITEM_COLUMN, QtCore.Qt.UserRole)
