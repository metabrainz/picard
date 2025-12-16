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

        # Cache update status to avoid repeated network calls during search
        self._update_status_cache = {}

        # Cache version info to avoid repeated expensive calls
        self._version_cache = {}

        # Cache update results to avoid repeated check_updates() calls
        self._cached_updates = []

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
            try:
                plugin_name = plugin.manifest.name_i18n()
            except (AttributeError, Exception):
                plugin_name = plugin.name or plugin.plugin_id
            item.setText(COLUMN_PLUGIN, plugin_name)

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
        self._resync_do_not_update(installed_plugins_uuids)

    def _resync_do_not_update(self, uuid_set):
        """Resync do not update persist list with installed plugins list"""
        # A plugin could have been removed by another mean, so this ensures we removed old entries
        config = get_config()
        do_not_update = set(config.persist['plugins3_do_not_update_plugins'])
        resynced_do_not_update = do_not_update.intersection(uuid_set)
        config.persist['plugins3_do_not_update_plugins'] = list(resynced_do_not_update)

    def _is_plugin_enabled(self, plugin):
        """Check if plugin is enabled."""
        return plugin.state == PluginState.ENABLED

    def _get_plugin_remote_url(self, plugin):
        """Get plugin remote URL from metadata."""
        return self.plugin_manager.get_plugin_remote_url(plugin)

    def _format_git_info(self, metadata):
        """Format git information for display."""
        return self.plugin_manager.get_plugin_git_info(metadata)

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
        elif self._has_update_available_cached(plugin):
            # Get new version info from cache first to avoid expensive calls during updates
            try:
                new_version = self._get_cached_new_version(plugin)
                item.setText(COLUMN_UPDATE, new_version)
            except Exception:
                item.setText(COLUMN_UPDATE, _("Available"))

            # Add checkbox for update selection
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)

            # Check if user has previously unchecked this plugin
            config = get_config()
            do_not_update = config.persist['plugins3_do_not_update_plugins']

            if plugin.uuid and plugin.uuid in do_not_update:
                item.setCheckState(COLUMN_UPDATE, QtCore.Qt.CheckState.Unchecked)
                self._set_update_checkbox_tooltip(item, False)
            else:
                item.setCheckState(COLUMN_UPDATE, QtCore.Qt.CheckState.Checked)
                self._set_update_checkbox_tooltip(item, True)
        else:
            # No update available - no text, no checkbox
            item.setText(COLUMN_UPDATE, "                   ")  # hacky
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsUserCheckable)

    def _get_cached_new_version(self, plugin):
        """Get new version from cache or compute if not cached."""
        # Return cached version if available
        if plugin.plugin_id in self._version_cache:
            return self._version_cache[plugin.plugin_id]

        # Compute and cache the version
        new_version = self._get_new_version(plugin)
        self._version_cache[plugin.plugin_id] = new_version
        return new_version

    def _format_update_version(self, update):
        """Format update version info for display (matching git info format)."""
        from picard.git.utils import RefItem

        ref = getattr(update, 'new_ref', None) or getattr(update, 'old_ref', 'main')
        commit = getattr(update, 'new_commit', None)

        ref_item = RefItem(name=ref, commit=commit)
        return ref_item.format() or _("Available")

    def _get_new_version(self, plugin):
        """Get the new version available for update."""
        # Use cached update info instead of calling check_updates()
        # This prevents network calls during UI rendering
        if hasattr(self, '_cached_updates'):
            for update in self._cached_updates:
                if update.plugin_id == plugin.plugin_id:
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
        self._version_cache.pop(plugin.plugin_id, None)
        self._update_status_cache.pop(plugin.plugin_id, None)
        self._refresh_plugin_display(plugin)

    def _refresh_plugin_display(self, plugin):
        """Refresh display for a specific plugin."""
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            item_plugin = item.data(COLUMN_ENABLED, QtCore.Qt.ItemDataRole.UserRole)
            if item_plugin and item_plugin.plugin_id == plugin.plugin_id:
                # Update version column to show new ref
                item.setText(COLUMN_VERSION, self._get_clean_version_display(plugin))
                # Update update column
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

    def _load_cached_update_status(self):
        """Load cached update status from disk - completely passive, no plugin access."""
        # Don't access plugin_manager.plugins here as it might trigger cache updates
        # Just load what's already in the cache file without triggering any operations
        try:
            cache = self.plugin_manager._refs_cache.load_cache()
            update_cache = cache.get('update_status', {})
            for plugin_id, entry in update_cache.items():
                if isinstance(entry, dict) and 'has_update' in entry:
                    self._update_status_cache[plugin_id] = entry['has_update']
        except Exception:
            # Silently ignore cache loading errors
            pass

    def refresh_update_status(self, force_network_check=False):
        """Public method to refresh update status for all plugins.

        Args:
            force_network_check: If True, make network calls to check for updates.
                                If False, only use cached data.
        """
        if force_network_check:
            self._refresh_update_status()
        else:
            # Only refresh display with cached data, no network calls
            self._refresh_cached_update_status()

    def _has_update_available_cached(self, plugin):
        """Check if plugin has update available using cache."""
        return self._update_status_cache.get(plugin.plugin_id, False)

    def _has_update_available(self, plugin):
        """Check if plugin has update available."""
        # This is only called from context menu, so network call is acceptable
        return self.plugin_manager.get_plugin_update_status(plugin)

    def _refresh_cached_update_status(self):
        """Refresh update status using only cached data - no network calls."""
        # Load cached update status from disk only when needed
        self._load_cached_update_status()

    def _refresh_update_status(self):
        """Refresh update status for all plugins."""
        self._update_status_cache.clear()
        self._version_cache.clear()  # Clear version cache too

        # Get all updates at once and cache them
        try:
            self._cached_updates = self.plugin_manager.check_updates()
        except Exception as e:
            log.debug("check_updates() failed: %s", e)
            self._cached_updates = []

        # Update individual plugin status cache
        for plugin in self.plugin_manager.plugins:
            self._refresh_single_plugin_update_status(plugin)

    def _refresh_single_plugin_update_status(self, plugin):
        """Refresh update status for a single plugin."""
        try:
            has_update = self.plugin_manager.get_plugin_update_status(plugin, force_refresh=True)
            self._update_status_cache[plugin.plugin_id] = has_update
        except Exception as e:
            log.debug("get_plugin_update_status() for %s failed: %s", plugin.plugin_id, e)
            # Don't let update check failures break the UI
            self._update_status_cache[plugin.plugin_id] = False

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
                    action = "enable" if target_enabled else "disable"
                    QtWidgets.QMessageBox.critical(
                        self,
                        _("Plugin Error"),
                        _("Failed to {} plugin '{}':\n\n{}").format(action, plugin.name or plugin.plugin_id, str(e)),
                    )
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
            if plugin and plugin.uuid:
                config = get_config()
                do_not_update = list(config.persist['plugins3_do_not_update_plugins'])

                is_checked = item.checkState(COLUMN_UPDATE) == QtCore.Qt.CheckState.Checked

                # Update tooltip based on new state
                self._set_update_checkbox_tooltip(item, is_checked)

                if not is_checked and plugin.uuid not in do_not_update:
                    # User unchecked - add to do not update list
                    do_not_update.append(plugin.uuid)
                    config.persist['plugins3_do_not_update_plugins'] = do_not_update
                elif is_checked and plugin.uuid in do_not_update:
                    # User checked - remove from do not update list
                    do_not_update.remove(plugin.uuid)
                    config.persist['plugins3_do_not_update_plugins'] = do_not_update

            # Update header button when update checkboxes change
            self._update_header_button()

    def _update_item_to_intended_state(self, item, enabled):
        """Update item display to show intended state."""
        item.setCheckState(COLUMN_ENABLED, QtCore.Qt.CheckState.Checked if enabled else QtCore.Qt.CheckState.Unchecked)

    def _update_item_display(self, item, plugin):
        """Update display for a specific item."""
        item.setCheckState(
            COLUMN_ENABLED,
            QtCore.Qt.CheckState.Checked if self._is_plugin_enabled(plugin) else QtCore.Qt.CheckState.Unchecked,
        )

    def _clear_toggle_and_refresh(self, plugin_id):
        """Clear toggle state and refresh plugin list."""
        self._toggling_plugins.discard(plugin_id)
        self._refresh_plugin_list()

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
            QtWidgets.QMessageBox.critical(
                self,
                _("Plugin Error"),
                _("Failed to {} plugin '{}': {}").format(
                    _("enable") if enabled else _("disable"), plugin.name or plugin.plugin_id, str(e)
                ),
            )

    def _update_plugin_from_menu(self, plugin):
        """Update plugin from context menu."""
        async_manager = AsyncPluginManager(self.plugin_manager)
        async_manager.update_plugin(
            plugin=plugin, progress_callback=None, callback=partial(self._on_context_update_complete, plugin)
        )

    def _on_context_update_complete(self, plugin, result):
        """Handle context menu update completion."""
        if result.success:
            # Clear version cache for updated plugin
            self._version_cache.pop(plugin.plugin_id, None)

            # Refresh update status for the specific plugin since it was updated
            self._refresh_single_plugin_update_status(plugin)

            # Refresh the plugin list
            self.populate_plugins(self.plugin_manager.plugins)
            # Emit signal for options dialog to refresh
            self.plugin_state_changed.emit(plugin, "updated")
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Update Failed"), error_msg)

    def _uninstall_plugin_from_menu(self, plugin):
        """Uninstall plugin from context menu."""
        dialog = UninstallPluginDialog(plugin, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            try:
                async_manager = AsyncPluginManager(self.plugin_manager)
                async_manager.uninstall_plugin(
                    plugin, purge=dialog.purge_config, callback=partial(self._on_uninstall_complete, plugin)
                )
            except Exception as e:
                log.error("Failed to uninstall plugin %s: %s", plugin.plugin_id, e, exc_info=True)
                QtWidgets.QMessageBox.critical(
                    self, _("Uninstall Failed"), _("Failed to uninstall plugin: {}").format(str(e))
                )

    def _on_uninstall_complete(self, plugin, result):
        """Handle uninstall completion."""
        if result.success:
            self._refresh_plugin_list()
            # Emit signal for options dialog to refresh
            self.plugin_state_changed.emit(plugin, "uninstalled")
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Uninstall Failed"), error_msg)

    def _reinstall_plugin_from_menu(self, plugin):
        """Reinstall plugin from context menu."""
        try:
            # Get plugin URL from metadata
            uuid = self.plugin_manager._get_plugin_uuid(plugin)
            metadata = self.plugin_manager._get_plugin_metadata(uuid)
            if not (metadata and hasattr(metadata, 'url')):
                QtWidgets.QMessageBox.critical(self, _("Reinstall Failed"), _("Could not find plugin repository URL"))
                return
            plugin_url = metadata.url

            # Get plugin name
            try:
                plugin_name = plugin.manifest.name_i18n()
            except (AttributeError, Exception):
                plugin_name = plugin.name or plugin.plugin_id

            # Get current ref for reinstall
            current_ref = None
            try:
                refs_info = self.plugin_manager.get_plugin_refs_info(plugin.plugin_id)
                if refs_info:
                    current_ref = refs_info.get('current_ref')
            except Exception:
                pass

            # Show confirmation dialog
            confirm_dialog = InstallConfirmDialog(plugin_name, plugin_url, self, plugin.uuid, current_ref)
            if confirm_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
                return

            async_manager = AsyncPluginManager(self.plugin_manager)
            async_manager.install_plugin(
                url=plugin_url,
                ref=confirm_dialog.selected_ref,  # Pass RefItem directly
                reinstall=True,
                callback=partial(self._on_reinstall_complete, plugin),
            )
        except Exception as e:
            log.error("Failed to reinstall plugin %s: %s", plugin.plugin_id, e, exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, _("Reinstall Failed"), _("Failed to reinstall plugin: {}").format(str(e))
            )

    def _on_reinstall_complete(self, plugin, result):
        """Handle reinstall completion."""
        if result.success:
            self._refresh_plugin_list()
            # Emit signal for options dialog to refresh
            self.plugin_state_changed.emit(plugin, "reinstalled")
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Reinstall Failed"), error_msg)

    def _switch_ref_from_menu(self, plugin):
        """Switch plugin ref from context menu."""
        dialog = SwitchRefDialog(plugin, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            try:
                async_manager = AsyncPluginManager(self.plugin_manager)
                async_manager.switch_ref(
                    plugin=plugin,
                    ref=dialog.selected_ref,  # Pass RefItem directly
                    callback=partial(self._on_switch_ref_complete, plugin),
                )
            except Exception as e:
                log.error("Failed to switch ref for plugin %s: %s", plugin.plugin_id, e, exc_info=True)
                QtWidgets.QMessageBox.critical(
                    self, _("Switch Ref Failed"), _("Failed to switch ref: {}").format(str(e))
                )

    def _on_switch_ref_complete(self, plugin, result):
        """Handle switch ref completion."""
        if result.success:
            # Check for enable failures
            switch_result = result.result
            if (
                isinstance(switch_result, dict)
                and switch_result.get('was_enabled')
                and not switch_result.get('enable_success')
            ):
                # Plugin switched but failed to enable
                error_msg = str(switch_result.get('enable_error', 'Unknown enable error'))
                QtWidgets.QMessageBox.warning(
                    self,
                    _("Plugin Enable Failed"),
                    _("Plugin switched successfully but failed to enable:\n\n{}").format(error_msg),
                )

            # Refresh update status for the specific plugin since ref changed
            self._refresh_single_plugin_update_status(plugin)

            # Only refresh the display for this specific plugin, not all plugins
            self._refresh_plugin_display(plugin)
            # Emit signal for options dialog to refresh
            self.plugin_state_changed.emit(plugin, "ref switched")
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Switch Ref Failed"), error_msg)

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


class UninstallPluginDialog(QtWidgets.QDialog):
    """Dialog for uninstalling plugins with purge option."""

    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.purge_config = False
        self.setWindowTitle(_("Uninstall Plugin"))
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Plugin name
        try:
            name = self.plugin.manifest.name_i18n()
        except (AttributeError, Exception):
            name = self.plugin.name or self.plugin.plugin_id

        # Confirmation message
        message = QtWidgets.QLabel(_("Are you sure you want to uninstall '{}'?").format(name))
        message.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        message.setWordWrap(True)
        layout.addWidget(message)

        # Purge configuration checkbox
        self.purge_checkbox = QtWidgets.QCheckBox(_("Also remove plugin configuration"))
        self.purge_checkbox.setToolTip(_("Remove all saved settings and configuration for this plugin"))
        layout.addWidget(self.purge_checkbox)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        uninstall_button = QtWidgets.QPushButton(_("Yes, Uninstall!"))
        uninstall_button.clicked.connect(self._uninstall)
        button_layout.addWidget(uninstall_button)

        cancel_button = QtWidgets.QPushButton(_("Cancel"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def _uninstall(self):
        """Handle uninstall button click."""
        self.purge_config = self.purge_checkbox.isChecked()
        self.accept()


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
        self.setup_ui()
        self.load_refs()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Plugin name
        try:
            name = self.plugin.manifest.name_i18n()
        except (AttributeError, Exception):
            name = self.plugin.name or self.plugin.plugin_id

        title_label = QtWidgets.QLabel(_("Switch ref for '{}'").format(name))
        title_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(title_label)

        # Use the new RefSelectorWidget (no default tab for switch)
        self.ref_selector = RefSelectorWidget(include_default=False)
        layout.addWidget(self.ref_selector)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        switch_button = QtWidgets.QPushButton(_("Yes, Switch!"))
        switch_button.clicked.connect(self._switch_ref)
        button_layout.addWidget(switch_button)

        cancel_button = QtWidgets.QPushButton(_("Cancel"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

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
            QtWidgets.QMessageBox.warning(self, _("No Ref Selected"), _("Please select or enter a ref to switch to."))

    def _uninstall(self):
        """Handle uninstall button click."""
        self.purge_config = self.purge_checkbox.isChecked()
        self.accept()
