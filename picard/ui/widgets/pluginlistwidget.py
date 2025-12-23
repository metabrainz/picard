# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
# Copyright (C) 2025 Philipp Wolfer
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

from PyQt6 import QtCore, QtGui, QtWidgets

from picard import log
from picard.config import get_config
from picard.i18n import gettext as _
from picard.plugin3.asyncops.manager import AsyncPluginManager
from picard.plugin3.plugin import PluginState
from picard.plugin3.ref_item import RefItem
from picard.util import temporary_disconnect

from picard.ui.dialogs.installconfirm import InstallConfirmDialog
from picard.ui.dialogs.plugininfo import PluginInfoDialog
from picard.ui.widgets.refselector import RefSelectorWidget


# Column positions
COLUMN_ENABLED = 0
COLUMN_PLUGIN = 1
COLUMN_VERSION = 2
COLUMN_UPDATE = 3


class PluginListWidget(QtWidgets.QTreeWidget):
    """Widget for displaying and managing plugins."""

    plugin_selection_changed = QtCore.pyqtSignal(object)  # Emits selected plugin or None
    plugin_state_changed = QtCore.pyqtSignal(object, str)  # Emits plugin and action
    update_selected_plugins = QtCore.pyqtSignal(list)  # Emits list of plugins to update

    def __init__(self, parent=None):
        super().__init__(parent)
        self._toggling_plugins = set()  # Track plugins being toggled
        self._failed_enables = set()  # Track plugins that failed to enable
        self._updating_plugins = set()  # Track plugins being updated
        self.setup_ui()

    def setup_ui(self):
        """Setup the tree widget."""
        self.setHeaderLabels([_("Enabled"), _("Plugin"), _("Version"), ""])
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        # Set column sizing
        header = self.header()
        header.setSectionResizeMode(COLUMN_ENABLED, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COLUMN_PLUGIN, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COLUMN_VERSION, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COLUMN_UPDATE, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)

        # Create header with update button
        self._setup_header_widget()

        # Connect selection changes
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.itemClicked.connect(self._on_item_clicked)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Cache tagger instance for performance
        self.tagger = QtCore.QCoreApplication.instance()
        self.plugin_manager = self.tagger.get_plugin_manager()
        if not self.plugin_manager:
            raise RuntimeError("Plugin manager not available")

        # Connect to plugin manager signals
        self.plugin_manager.plugin_ref_switched.connect(self._on_plugin_ref_switched)

        # Guard to prevent double refresh during operations
        self._refreshing = False

        # Updates dict from options page (plugin_id -> UpdateCheck)
        self._updates = {}

        # Don't load cached update status during initialization to avoid any network activity
        # It will be loaded when actually needed during populate_plugins()

    def _setup_header_widget(self):
        """Setup header widget with update button."""
        # Create update button that will be positioned over the header
        self.update_button = QtWidgets.QPushButton(_("Update"), self)
        self.update_button.setMaximumHeight(20)
        self.update_button.setEnabled(False)  # Disabled by default
        self.update_button.setToolTip(_("Update selected plugins to their latest versions"))
        self.update_button.clicked.connect(self._update_selected_plugins)

        # Position the button over the update column header
        self._position_update_button()  # FIXME: hacky

    def populate_plugins(self, plugins):
        """Populate the widget with plugins."""
        self.clear()

        installed_plugins_uuids = set()
        for plugin in plugins:
            if plugin.uuid is not None:
                installed_plugins_uuids.add(plugin.uuid)

            item = QtWidgets.QTreeWidgetItem()

            # Column 0: Checkbox only (no text), centered
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                COLUMN_ENABLED,
                QtCore.Qt.CheckState.Checked if self._is_plugin_enabled(plugin) else QtCore.Qt.CheckState.Unchecked,
            )
            item.setTextAlignment(COLUMN_ENABLED, QtCore.Qt.AlignmentFlag.AlignCenter)

            # Column 1: Plugin name
            item.setText(COLUMN_PLUGIN, plugin.name())

            # Add tooltip with description if available
            try:
                description = plugin.manifest.description_i18n()
                if description:
                    item.setToolTip(COLUMN_PLUGIN, description)
            except (AttributeError, Exception):
                pass

            # Column 2: Version (without update suffix)
            item.setText(COLUMN_VERSION, self._get_clean_version_display(plugin))

            # Column 3: Update checkbox and new version
            self._setup_update_column(item, plugin)

            # Store plugin reference
            item.setData(COLUMN_ENABLED, QtCore.Qt.ItemDataRole.UserRole, plugin)

            self.addTopLevelItem(item)

        # Update header button visibility
        self._update_header_button()

        # Update do not update list to match installed plugins list
        installed_plugins_ids = {plugin.plugin_id for plugin in plugins}
        self._resync_do_not_update(installed_plugins_ids)

    def _resync_do_not_update(self, plugin_id_set):
        """Resync do not update persist list with installed plugins list"""
        # A plugin could have been removed by another mean, so this ensures we removed old entries
        config = get_config()
        do_not_update = set(config.persist['plugins3_do_not_update'])
        resynced_do_not_update = do_not_update.intersection(plugin_id_set)
        config.persist['plugins3_do_not_update'] = list(resynced_do_not_update)

    def _is_plugin_enabled(self, plugin):
        """Check if plugin is enabled."""
        return plugin.state == PluginState.ENABLED

    def _get_plugin_remote_url(self, plugin):
        """Get plugin remote URL from metadata."""
        return self.plugin_manager.get_plugin_remote_url(plugin)

    def _get_clean_version_display(self, plugin):
        """Get display text for plugin version without update suffix."""
        return self.plugin_manager.get_plugin_version_display(plugin)

    def _set_update_checkbox_tooltip(self, item, is_checked):
        """Set tooltip for update checkbox based on its state."""
        if is_checked:
            item.setToolTip(COLUMN_UPDATE, _("This plugin is included in updates"))
        else:
            item.setToolTip(COLUMN_UPDATE, _("This plugin is excluded from updates"))

    def _setup_update_column(self, item, plugin):
        """Setup update column with checkbox and new version."""
        if plugin.plugin_id in self._updating_plugins:
            # Show in progress for updating plugins
            item.setText(COLUMN_UPDATE, _("In Progress..."))
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsUserCheckable)
        elif self._has_update_available(plugin):
            # Get new version info from cache first to avoid expensive calls during updates
            try:
                new_version = self._get_new_version(plugin)
                item.setText(COLUMN_UPDATE, new_version)
            except Exception:
                item.setText(COLUMN_UPDATE, _("Available"))

            # Add checkbox for update selection
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)

            # Check if user has previously unchecked this plugin
            config = get_config()
            do_not_update = config.persist['plugins3_do_not_update']

            if plugin.plugin_id in do_not_update:
                item.setCheckState(COLUMN_UPDATE, QtCore.Qt.CheckState.Unchecked)
                self._set_update_checkbox_tooltip(item, False)
            else:
                item.setCheckState(COLUMN_UPDATE, QtCore.Qt.CheckState.Checked)
                self._set_update_checkbox_tooltip(item, True)
        else:
            # No update available - no text, no checkbox
            item.setText(COLUMN_UPDATE, "                   ")  # hacky
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsUserCheckable)

    def _format_update_version(self, update):
        """Format update version info for display (matching git info format)."""
        # Use the new RefItem directly from UpdateResult
        new_ref_item = getattr(update, 'new_ref_item', None)
        if new_ref_item:
            return new_ref_item.format() or _("Available")

        # Fallback for old UpdateResult format (backward compatibility)
        ref = getattr(update, 'new_ref', None) or getattr(update, 'old_ref', 'main')
        commit = getattr(update, 'new_commit', None)

        # Create RefItem object for formatting - we need to guess the ref type
        if ref:
            # Try to determine ref type from name pattern
            if ref.startswith('v') or '.' in ref:
                ref_type = RefItem.Type.TAG
            else:
                ref_type = RefItem.Type.BRANCH
        else:
            # Just a commit hash
            ref = commit
            ref_type = RefItem.Type.COMMIT

        ref_item = RefItem(shortname=ref, ref_type=ref_type, commit=commit)
        return ref_item.format() or _("Available")

    def _get_new_version(self, plugin):
        """Get the new version available for update."""
        update = self._updates.get(plugin.plugin_id)
        if update:
            return self._format_update_version(update)
        return _("Available")

    def _update_header_button(self):
        """Update header button state based on checked items."""
        checked_count = self._count_checked_updates()
        self.update_button.setEnabled(checked_count > 0)
        if checked_count > 0:
            self.update_button.setText(_("Update ({})").format(checked_count))
        else:
            self.update_button.setText(_("Update"))

    def _count_checked_updates(self):
        """Count items with checked update checkboxes."""
        count = 0
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if (
                item.flags() & QtCore.Qt.ItemFlag.ItemIsUserCheckable
                and item.checkState(COLUMN_UPDATE) == QtCore.Qt.CheckState.Checked
            ):
                count += 1
        return count

    def _update_selected_plugins(self):
        """Emit signal to update selected plugins."""
        plugins_to_update = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if (
                item.flags() & QtCore.Qt.ItemFlag.ItemIsUserCheckable
                and item.checkState(COLUMN_UPDATE) == QtCore.Qt.CheckState.Checked
            ):
                plugin = item.data(COLUMN_ENABLED, QtCore.Qt.ItemDataRole.UserRole)
                if plugin:
                    plugins_to_update.append(plugin)

        if plugins_to_update:
            self.update_selected_plugins.emit(plugins_to_update)

    def mark_plugin_updating(self, plugin):
        """Mark a plugin as being updated."""
        self._updating_plugins.add(plugin.plugin_id)
        self._refresh_plugin_display(plugin)

    def mark_plugin_update_complete(self, plugin):
        """Mark a plugin update as complete."""
        self._updating_plugins.discard(plugin.plugin_id)
        # Clear caches for updated plugin - it should no longer have updates available
        self._refresh_plugin_display(plugin)

    def _refresh_plugin_display(self, plugin):
        """Refresh display for a specific plugin."""
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            item_plugin = item.data(COLUMN_ENABLED, QtCore.Qt.ItemDataRole.UserRole)
            if item_plugin and item_plugin.plugin_id == plugin.plugin_id:
                self._setup_update_column(item, plugin)
                self._update_header_button()
                break

    def _position_update_button(self):
        """Position the update button over the update column header."""
        if hasattr(self, 'update_button'):
            # Get the position and size of the update column header
            header_rect = self.header().sectionViewportPosition(COLUMN_UPDATE)
            header_width = self.header().sectionSize(COLUMN_UPDATE)

            # Position the button
            self.update_button.setGeometry(header_rect, 0, header_width, 20)

    def resizeEvent(self, event):
        """Handle resize events to reposition the update button."""
        super().resizeEvent(event)
        self._position_update_button()

    def set_updates(self, updates):
        """Set the updates dict from the options page."""
        self._updates = updates

    def _has_update_available(self, plugin):
        """Check if plugin has update available."""
        return plugin.plugin_id in self._updates

    def _on_selection_changed(self):
        """Handle selection changes."""
        selected_items = self.selectedItems()
        if selected_items:
            plugin = selected_items[0].data(0, QtCore.Qt.ItemDataRole.UserRole)
            self.plugin_selection_changed.emit(plugin)
        else:
            self.plugin_selection_changed.emit(None)

    def _on_item_clicked(self, item, column):
        """Handle item clicks (checkbox clicks)."""
        if column == COLUMN_ENABLED:  # Handle enabled checkbox
            plugin = item.data(COLUMN_ENABLED, QtCore.Qt.ItemDataRole.UserRole)
            if plugin:
                # Prevent rapid toggling of the same plugin
                if plugin.plugin_id in self._toggling_plugins:
                    return

                # Base toggle decision on actual plugin state
                if plugin.state == PluginState.ENABLED:
                    target_enabled = False  # Disable it
                elif plugin.state == PluginState.LOADED:
                    target_enabled = False  # Disable loaded plugins (they're stuck, need to be reset)
                elif plugin.state in (PluginState.DISABLED, PluginState.DISCOVERED):
                    # Don't try to enable plugins that have failed before
                    if plugin.plugin_id in self._failed_enables:
                        return
                    target_enabled = True  # Enable it
                else:
                    return

                try:
                    self._toggling_plugins.add(plugin.plugin_id)
                    self._toggle_plugin(plugin, target_enabled)
                except Exception as e:
                    # Show error dialog to user
                    log.error("Failed to toggle plugin %s: %s", plugin.plugin_id, e, exc_info=True)
                    if target_enabled:
                        self._enable_error_dialog(plugin, str(e))
                    else:
                        self._disable_error_dialog(plugin, str(e))
                    # Track failed enable attempts
                    if target_enabled and "Already declared" in str(e):
                        self._failed_enables.add(plugin.plugin_id)
                finally:
                    # Clear failed enable tracking on successful disable
                    if not target_enabled and plugin.state == PluginState.DISABLED:
                        if plugin.plugin_id in self._failed_enables:
                            self._failed_enables.remove(plugin.plugin_id)

                    # Always update UI to reflect actual plugin state
                    actual_enabled = self._is_plugin_enabled(plugin)
                    item.setCheckState(
                        COLUMN_ENABLED,
                        QtCore.Qt.CheckState.Checked if actual_enabled else QtCore.Qt.CheckState.Unchecked,
                    )

                    # Remove from toggling set
                    self._toggling_plugins.discard(plugin.plugin_id)

                    # Emit signal for options dialog to refresh
                    action = "enabled" if actual_enabled else "disabled"
                    self.plugin_state_changed.emit(plugin, action)

        elif column == COLUMN_UPDATE:  # Handle update checkbox
            # Save checkbox state preference
            plugin = item.data(COLUMN_ENABLED, QtCore.Qt.ItemDataRole.UserRole)
            if plugin:
                config = get_config()
                do_not_update = list(config.persist['plugins3_do_not_update'])

                is_checked = item.checkState(COLUMN_UPDATE) == QtCore.Qt.CheckState.Checked

                # Update tooltip based on new state
                self._set_update_checkbox_tooltip(item, is_checked)

                if not is_checked and plugin.plugin_id not in do_not_update:
                    # User unchecked - add to do not update list
                    do_not_update.append(plugin.plugin_id)
                    config.persist['plugins3_do_not_update'] = do_not_update
                elif is_checked and plugin.plugin_id in do_not_update:
                    # User checked - remove from do not update list
                    do_not_update.remove(plugin.plugin_id)
                    config.persist['plugins3_do_not_update'] = do_not_update

            # Update header button when update checkboxes change
            self._update_header_button()

    def _refresh_plugin_list(self):
        """Refresh the plugin list to reflect current state."""
        if self._refreshing:
            return

        self._refreshing = True
        try:
            plugins = self.plugin_manager.plugins

            # Use utility to temporarily disconnect signal during refresh
            with temporary_disconnect(self.itemClicked, self._on_item_clicked):
                self.populate_plugins(plugins)
        finally:
            self._refreshing = False

    def _toggle_plugin(self, plugin, enabled):
        """Toggle plugin enabled state."""
        if enabled:
            self.plugin_manager.enable_plugin(plugin)
        else:
            self.plugin_manager.disable_plugin(plugin)

    def _show_context_menu(self, position):
        """Show context menu for plugin list."""
        item = self.itemAt(position)
        if not item:
            return

        plugin = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not plugin:
            return

        menu = QtWidgets.QMenu(self)

        # Enable/Disable action
        if self._is_plugin_enabled(plugin):
            disable_action = menu.addAction(_("Disable"))
            disable_action.triggered.connect(lambda: self._toggle_plugin_from_menu(plugin, False))
        else:
            enable_action = menu.addAction(_("Enable"))
            enable_action.triggered.connect(lambda: self._toggle_plugin_from_menu(plugin, True))

        menu.addSeparator()

        # Update action
        update_action = menu.addAction(_("Update"))
        update_action.triggered.connect(lambda: self._update_plugin_from_menu(plugin))
        update_action.setEnabled(self._has_update_available(plugin))

        # Uninstall action
        uninstall_action = menu.addAction(_("Uninstall"))
        uninstall_action.triggered.connect(lambda: self._uninstall_plugin_from_menu(plugin))

        # Reinstall action
        reinstall_action = menu.addAction(_("Reinstall"))
        reinstall_action.triggered.connect(lambda: self._reinstall_plugin_from_menu(plugin))

        # Switch ref action
        switch_ref_action = menu.addAction(_("Switch Ref"))
        switch_ref_action.triggered.connect(lambda: self._switch_ref_from_menu(plugin))

        menu.addSeparator()

        menu.addSeparator()

        # Information action
        info_action = menu.addAction(_("Information"))
        info_action.triggered.connect(lambda: self._show_plugin_info(plugin))

        # View repository action (if available)
        remote_url = self._get_plugin_remote_url(plugin)
        if remote_url:
            view_repo_action = menu.addAction(_("View Repository"))
            view_repo_action.triggered.connect(lambda: self._view_repository(plugin))

        # Show menu
        menu.exec(self.mapToGlobal(position))

    def _enable_error_dialog(self, plugin, errmsg):
        QtWidgets.QMessageBox.critical(
            self,
            _("Plugin Error"),
            _("Failed to enable plugin '{}':\n{}").format(plugin.name(), errmsg),
        )

    def _disable_error_dialog(self, plugin, errmsg):
        QtWidgets.QMessageBox.critical(
            self,
            _("Plugin Error"),
            _("Failed to disable plugin '{}':\n{}").format(plugin.name(), errmsg),
        )

    def _toggle_plugin_from_menu(self, plugin, enabled):
        """Toggle plugin from context menu."""
        try:
            self._toggle_plugin(plugin, enabled)
            # Refresh immediately now that signal loop is fixed
            self._refresh_plugin_list()
            # Emit signal for options dialog to refresh
            action = "enabled" if enabled else "disabled"
            self.plugin_state_changed.emit(plugin, action)
        except Exception as e:
            # Show error message
            if enabled:
                self._enable_error_dialog(plugin, str(e))
            else:
                self._disable_error_dialog(plugin, str(e))

    def _update_plugin_from_menu(self, plugin):
        """Update plugin from context menu."""
        async_manager = AsyncPluginManager(self.plugin_manager)
        async_manager.update_plugin(
            plugin=plugin, progress_callback=None, callback=partial(self._on_context_update_complete, plugin)
        )

    def _update_error_dialog(self, plugin, errmsg):
        QtWidgets.QMessageBox.critical(
            self,
            _("Plugin Error"),
            _("Failed to update plugin '{}':\n{}").format(plugin.name(), errmsg),
        )

    def _on_context_update_complete(self, plugin, result):
        """Handle context menu update completion."""
        if result.success:
            # Refresh the plugin list
            self.populate_plugins(self.plugin_manager.plugins)
            # Emit signal for options dialog to refresh and update updates dict
            self.plugin_state_changed.emit(plugin, "updated")
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            self._update_error_dialog(plugin, error_msg)

    def _uninstall_error_dialog(self, plugin, errmsg):
        QtWidgets.QMessageBox.critical(
            self,
            _("Plugin Error"),
            _("Failed to uninstall plugin '{}':\n{}").format(plugin.name(), errmsg),
        )

    def _uninstall_plugin_from_menu(self, plugin):
        """Uninstall plugin from context menu."""
        dialog = UninstallPluginDialog(plugin, self)
        dialog.exec()
        if dialog.uninstall_confirmed:
            try:
                async_manager = AsyncPluginManager(self.plugin_manager)
                async_manager.uninstall_plugin(
                    plugin, purge=dialog.purge_config, callback=partial(self._on_uninstall_complete, plugin)
                )
            except Exception as e:
                log.error("Failed to uninstall plugin %s: %s", plugin.plugin_id, e, exc_info=True)
                self._uninstall_error_dialog(plugin, str(e))

    def _on_uninstall_complete(self, plugin, result):
        """Handle uninstall completion."""
        if result.success:
            self._refresh_plugin_list()
            # Emit signal for options dialog to refresh and update updates dict
            self.plugin_state_changed.emit(plugin, "uninstalled")
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            self._uninstall_error_dialog(plugin, error_msg)

    def _reinstall_error_dialog(self, plugin, errmsg):
        QtWidgets.QMessageBox.critical(
            self,
            _("Plugin Error"),
            _("Failed to reinstall plugin '{}':\n{}").format(plugin.name(), errmsg),
        )

    def _reinstall_plugin_from_menu(self, plugin):
        """Reinstall plugin from context menu."""
        try:
            # Get plugin URL from metadata
            uuid = self.plugin_manager._get_plugin_uuid(plugin)
            metadata = self.plugin_manager._get_plugin_metadata(uuid)
            if not (metadata and hasattr(metadata, 'url')):
                self._reinstall_error_dialog(plugin, _("Could not find plugin repository URL"))
                return
            plugin_url = metadata.url

            # Get current ref for reinstall
            current_ref = None
            try:
                refs_info = self.plugin_manager.get_plugin_refs_info(plugin.plugin_id)
                if refs_info:
                    current_ref = refs_info.get('current_ref')
            except Exception:
                pass

            # Show confirmation dialog
            confirm_dialog = InstallConfirmDialog(plugin.name(), plugin_url, self, plugin.uuid, current_ref)
            if confirm_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
                return

            async_manager = AsyncPluginManager(self.plugin_manager)
            async_manager.install_plugin(
                url=plugin_url,
                ref=confirm_dialog.selected_ref.shortname if confirm_dialog.selected_ref else None,
                reinstall=True,
                callback=partial(self._on_reinstall_complete, plugin),
            )
        except Exception as e:
            log.error("Failed to reinstall plugin %s: %s", plugin.plugin_id, e, exc_info=True)
            self._reinstall_error_dialog(plugin, str(e))

    def _on_reinstall_complete(self, plugin, result):
        """Handle reinstall completion."""
        if result.success:
            self._refresh_plugin_list()
            # Emit signal for options dialog to refresh and update updates dict
            self.plugin_state_changed.emit(plugin, "reinstalled")
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            self._reinstall_error_dialog(plugin, error_msg)

    def _switch_ref_error_dialog(self, plugin, errmsg):
        QtWidgets.QMessageBox.critical(
            self,
            _("Plugin Error"),
            _("Failed to switch ref for plugin '{}':\n{}").format(plugin.name(), errmsg),
        )

    def _switch_ref_from_menu(self, plugin):
        """Switch plugin ref from context menu."""
        dialog = SwitchRefDialog(plugin, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            try:
                async_manager = AsyncPluginManager(self.plugin_manager)
                async_manager.switch_ref(
                    plugin=plugin,
                    ref=dialog.selected_ref.shortname if dialog.selected_ref else None,
                    callback=partial(self._on_switch_ref_complete, plugin),
                )
            except Exception as e:
                log.error("Failed to switch ref for plugin %s: %s", plugin.plugin_id, e, exc_info=True)
                self._switch_ref_error_dialog(plugin, str(e))

    def _on_switch_ref_complete(self, plugin, result):
        """Handle switch ref completion."""
        if result.success:
            # Only refresh the display for this specific plugin, not all plugins
            self._refresh_plugin_display(plugin)
            # Emit signal for options dialog to refresh and update updates dict
            self.plugin_state_changed.emit(plugin, "ref switched")
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            self._switch_ref_error_dialog(plugin, error_msg)

    def _on_plugin_ref_switched(self, plugin):
        """Handle plugin ref switched signal."""
        self._refresh_plugin_list()

    def _view_repository(self, plugin):
        """Open plugin repository in browser."""
        remote_url = self._get_plugin_remote_url(plugin)
        if remote_url:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(remote_url))

    def _show_plugin_info(self, plugin):
        """Show detailed plugin information dialog."""
        dialog = PluginInfoDialog(plugin, self)
        dialog.exec()


class UninstallPluginDialog(QtWidgets.QMessageBox):
    """Dialog for uninstalling plugins with purge option."""

    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.setWindowTitle(_("Uninstall Plugin"))
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        self.setIcon(QtWidgets.QMessageBox.Icon.Warning)

        # Confirmation message
        self.setText(_("Are you sure you want to uninstall '{}'?").format(self.plugin.name()))

        # Purge configuration checkbox
        self._purge_checkbox = QtWidgets.QCheckBox(_("Also remove plugin configuration"))
        self._purge_checkbox.setToolTip(_("Remove all saved settings and configuration for this plugin"))
        self.setCheckBox(self._purge_checkbox)

        # Buttons
        self._btn_confirm_uninstall = self.addButton(_("Yes, Uninstall!"), QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        self.addButton(QtWidgets.QMessageBox.StandardButton.Cancel)

    @property
    def purge_config(self) -> bool:
        return self._purge_checkbox.isChecked()

    @property
    def uninstall_confirmed(self) -> bool:
        return self.clickedButton() == self._btn_confirm_uninstall


class SwitchRefDialog(QtWidgets.QDialog):
    """Dialog for switching plugin git ref."""

    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.selected_ref = None
        # Cache tagger instance for performance
        self.tagger = QtCore.QCoreApplication.instance()
        self.plugin_manager = self.tagger.get_plugin_manager()
        if not self.plugin_manager:
            raise RuntimeError("Plugin manager not available")
        self.setWindowTitle(_("Switch Git Ref"))
        self.setModal(True)
        self.resize(400, 300)
        self.setMinimumSize(400, 300)
        self.setup_ui()
        self.load_refs()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        title_label = QtWidgets.QLabel(_("Switch ref for '{}'").format(self.plugin.name()))
        title_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(title_label)

        # Use the new RefSelectorWidget (no default tab for switch)
        self.ref_selector = RefSelectorWidget(include_default=False)
        layout.addWidget(self.ref_selector)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox()
        self.install_button = QtWidgets.QPushButton(_("Yes, Switch!"))
        button_box.addButton(self.install_button, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._switch_ref)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_refs(self):
        """Load available refs from repository."""
        try:
            # Get plugin refs info (includes current ref)
            refs_info = self.plugin_manager.get_plugin_refs_info(self.plugin.plugin_id)
            if refs_info and refs_info['url']:
                refs = self.plugin_manager.fetch_all_git_refs(refs_info['url'])
                current_ref = refs_info.get('current_ref')

                self.ref_selector.load_refs(refs, current_ref=current_ref, plugin_manager=self.plugin_manager)
        except Exception as e:
            log.error("SwitchRefDialog: Failed to load refs: %s", e, exc_info=True)

    def _switch_ref(self):
        """Handle switch button click."""
        self.selected_ref = self.ref_selector.get_selected_ref()

        if self.selected_ref:
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self,
                _("No Ref Selected"),
                _("Please select or enter a ref to switch to."),
            )

    def _uninstall(self):
        """Handle uninstall button click."""
        self.purge_config = self.purge_checkbox.isChecked()
        self.accept()
