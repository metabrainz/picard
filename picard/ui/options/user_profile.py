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


from functools import partial

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard import log
from picard.config import (
    Option,
    TextOption,
    get_config,
)
from picard.const import PICARD_URLS
from picard.profile import UserProfile
from picard.util import restore_method

from picard.ui import (
    PicardDialog,
    SingletonDialog,
    confirmation_dialog,
)
from picard.ui.util import StandardButton


class UserProfilesDialog(PicardDialog, SingletonDialog):
    options = [
        Option("persist", "user_profiles", {}),
        TextOption("persist", "selected_user_profile", ""),
    ]
    help_url = PICARD_URLS['doc_user_profiles']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.loading = True

        from picard.ui.ui_user_profiles import Ui_UserProfileEditor
        self.ui = Ui_UserProfileEditor()
        self.ui.setupUi(self)

        self.ui.new_profile_button = QtWidgets.QPushButton(_("&New"))
        self.ui.new_profile_button.setToolTip(_("Create a copy of the selected profile as a new profile"))

        self.ui.delete_profile_button = QtWidgets.QPushButton(_("&Delete"))
        self.ui.delete_profile_button.setToolTip(_("Delete the selected profile"))

        self.ui.apply_changes_button = QtWidgets.QPushButton(_("&Apply"))
        self.ui.apply_changes_button.setToolTip(_("Apply changes to the profile"))

        self.ui.okay_button = QtWidgets.QPushButton(_("&Ok"))
        self.ui.okay_button.setToolTip(_("Use the selected profile"))

        self.ui.buttonbox.addButton(StandardButton(StandardButton.CANCEL), QtWidgets.QDialogButtonBox.RejectRole)
        self.ui.buttonbox.addButton(StandardButton(StandardButton.HELP), QtWidgets.QDialogButtonBox.HelpRole)
        self.ui.buttonbox.addButton(self.ui.apply_changes_button, QtWidgets.QDialogButtonBox.ActionRole)
        self.ui.buttonbox.addButton(self.ui.new_profile_button, QtWidgets.QDialogButtonBox.ActionRole)
        self.ui.buttonbox.addButton(self.ui.delete_profile_button, QtWidgets.QDialogButtonBox.ActionRole)
        self.ui.buttonbox.addButton(self.ui.okay_button, QtWidgets.QDialogButtonBox.AcceptRole)

        self.ui.buttonbox.accepted.connect(self.accept)
        self.ui.buttonbox.rejected.connect(self.reject)
        self.ui.new_profile_button.clicked.connect(self.new_profile)
        self.ui.delete_profile_button.clicked.connect(self.delete_profile)
        self.ui.apply_changes_button.clicked.connect(self.update_combo_box_item)
        self.ui.buttonbox.helpRequested.connect(self.show_help)

        self.ui.user_profiles.currentIndexChanged.connect(partial(self.select_profile, skip_check=False))

        self.selected_index = -1
        self.selected_profile = ''

        self.load()

        self.populate_combobox()

        self.loading = False
        self.restoreWindowState()
        self.finished.connect(self.saveWindowState)

    def has_changed(self):
        """Check if the current profile has pending edits to the title or description that have not been saved.

        Returns:
            bool: True if there are unsaved changes, otherwise false.
        """
        profile_item = self.ui.user_profiles.itemData(self.selected_index)
        return self.ui.profile_title.text().strip() != profile_item['title'] or \
            self.ui.profile_description.toPlainText().strip() != profile_item['description']

    def unsaved_changes_confirmation(self):
        """Check if there are unsaved changes and ask the user to confirm the action resulting in their loss.

        Returns:
            bool: True if no unsaved changes or user confirms the action, otherwise False.
        """
        if not self.loading and self.has_changed() and not confirmation_dialog(
            _("There are unsaved changes to the current profile.  Do you want to continue and lose these changes?"),
            self,
        ):
            self._set_combobox_index(self.selected_index)
            return False
        return True

    def _set_combobox_index(self, idx):
        """Sets the index of the profile selector combo box.

        Args:
            idx (int): New index position
        """
        self.ui.user_profiles.blockSignals(True)
        self.ui.user_profiles.setCurrentIndex(idx)
        self.ui.user_profiles.blockSignals(False)
        self.selected_index = idx

    def set_selected_profile_index(self, idx):
        """Select the profile at the specified combo box index.

        Args:
            idx (int): Index of the profile to select
        """
        self._set_combobox_index(idx)
        self.select_profile(skip_check=True)

    def get_selected_item(self, idx=None):
        """Get the selected item from the profile selection combo box.

        Returns:
            dict: Profile dictionary.
        """
        if idx is None or idx < 0:
            idx = self.ui.user_profiles.currentIndex()
        elif idx >= self.ui.user_profiles.count():
            idx = self.ui.user_profiles.count() - 1
        return self.ui.user_profiles.itemData(idx)

    def select_profile(self, skip_check=False):
        """Load the current profile from the combo box into the editor.

        Args:
            skip_check (bool): Skip the check for unsaved edits.  Defaults to False.
        """
        if self.loading or skip_check or self.unsaved_changes_confirmation():
            profile_item = self.get_selected_item()
            self.ui.profile_title.setText(profile_item['title'])
            self.ui.profile_description.setPlainText(profile_item['description'])
            self.selected_profile = profile_item['id']
            self.selected_index = self.ui.user_profiles.currentIndex()
            self.ui.delete_profile_button.setEnabled(len(self.profiles) > 1)

    def update_combo_box_item(self):
        """Update the title and item data for the currently selected combo box item.
        """
        new_title = self.ui.profile_title.text().strip()
        if not new_title:
            QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Critical,
                _("Error"),
                _("The profile title must not be empty."),
                QtWidgets.QMessageBox.Ok,
                self
            ).exec_()
            return
        self.profiles[self.selected_profile]['title'] = self.ui.profile_title.text().strip()
        self.profiles[self.selected_profile]['description'] = self.ui.profile_description.toPlainText().strip()
        self.populate_combobox()

    def delete_profile(self):
        """Removes the currently selected profile from the selection combo box and profile list.
        """
        if confirmation_dialog(_('Are you sure that you want to delete the profile?'), self):
            # Mark the next item for display after the deletion.
            idx = self.ui.user_profiles.currentIndex() + 1
            # If the last item is being deleted, mark the preceding item for display.
            if idx >= self.ui.user_profiles.count():
                idx -= 2
            self.profiles.pop(self.selected_profile, None)
            profile = self.get_selected_item(idx)
            self.selected_profile = profile['id']
            self.populate_combobox()
            self.select_profile(skip_check=True)

    def populate_combobox(self):
        """Populate the profile selection combo box.
        """
        self.ui.user_profiles.blockSignals(True)
        self.ui.user_profiles.clear()
        idx = 0
        for count, (key, value) in enumerate(sorted(self.profiles.items(), key=lambda item: item[1]['title'])):
            self.ui.user_profiles.addItem(value['title'], value)
            if key == self.selected_profile:
                idx = count
        self.ui.user_profiles.setCurrentIndex(idx)
        self.ui.user_profiles.blockSignals(False)
        return idx

    def load(self):
        """Load the information into the dialog.
        """
        config = get_config()
        self.profiles = config.persist["user_profiles"]
        self.selected_profile = config.persist["selected_user_profile"]
        self.populate_combobox()
        self.select_profile(skip_check=True)

    def new_profile(self):
        """Create a new profile based on the currently selected profile.
        """
        if self.unsaved_changes_confirmation():
            profile = UserProfile(
                title=_("%s (Copy)") % self.ui.profile_title.text().strip(),
                settings_dict=self.profiles[self.selected_profile]['settings']
            )
            new_key = profile['id']
            self.profiles[new_key] = profile.to_dict()
            self.selected_profile = new_key
            self.populate_combobox()
            self.select_profile(skip_check=True)

    def show_help(self):
        """Displays the help url in the user's browser.
        """
        return super().show_help()

    def accept(self):
        """Copy all settings from the currently selected profile to config.setting, saves the updated profiles
        dictionary and updates the selected profile in config.persist.
        """
        self.update_combo_box_item()
        config = get_config()
        config.persist["user_profiles"] = self.profiles
        config.persist["selected_user_profile"] = self.selected_profile
        log.debug('Updating settings to profile %s', self.selected_profile)
        new_profile = UserProfile(
            title=self.ui.profile_title.text().strip(),
            id=self.selected_profile,
            settings_dict=self.profiles[self.selected_profile]['settings'],
        )
        new_profile.settings_to_config()
        self.tagger.window.enable_renaming_action.setChecked(config.setting["rename_files"])
        self.tagger.window.enable_moving_action.setChecked(config.setting["move_files"])
        self.tagger.window.enable_tag_saving_action.setChecked(not config.setting["dont_write_tags"])
        super().accept()

    def closeEvent(self, event):
        """Custom close event handler to check for unsaved changes.
        """
        if self.unsaved_changes_confirmation():
            if self.has_changed():
                self.select_profile(skip_check=True)
            super().closeEvent(event)
        else:
            event.ignore()

    def saveWindowState(self):
        pass

    @restore_method
    def restoreWindowState(self):
        pass
