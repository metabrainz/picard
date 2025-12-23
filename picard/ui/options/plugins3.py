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

from datetime import datetime
from functools import partial

from PyQt6 import QtCore, QtWidgets

from picard import log
from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_, gettext as _
from picard.plugin3.asyncops.manager import AsyncPluginManager

from picard.ui.dialogs.installplugin import InstallPluginDialog
from picard.ui.options import OptionsPage
from picard.ui.widgets.plugindetailswidget import PluginDetailsWidget
from picard.ui.widgets.pluginlistwidget import PluginListWidget


class Plugins3OptionsPage(OptionsPage):
    """Plugin management options page."""

    NAME = 'plugins'
    TITLE = N_('Plugins')
    PARENT = None
    SORT_ORDER = 90
    ACTIVE = True

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.all_plugins = []  # Store all plugins for filtering

        # Cache plugin manager for performance
        self.plugin_manager = self.tagger.get_plugin_manager()

        self.setup_ui()

    def _save_updates(self, updates):
        """Save updates to config, cleaning up stale entries for uninstalled plugins."""
        config = get_config()
        current_plugin_ids = {plugin.plugin_id for plugin in self.all_plugins}
        config.persist['plugins3_updates'] = {
            pid: update for pid, update in updates.items() if pid in current_plugin_ids
        }

    def setup_ui(self):
        """Setup the UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Toolbar
        toolbar_layout = QtWidgets.QHBoxLayout()

        # Search box
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText(_("Search plugins..."))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._filter_plugins)
        toolbar_layout.addWidget(self.search_edit)

        toolbar_layout.addStretch()

        self.install_button = QtWidgets.QPushButton(_("Install Plugin"))
        self.install_button.setToolTip(_("Install a new plugin from the registry or a custom URL"))
        self.install_button.clicked.connect(self._install_plugin)
        toolbar_layout.addWidget(self.install_button)

        self.refresh_all_button = QtWidgets.QPushButton(_("Refresh All"))
        self.refresh_all_button.setToolTip(_("Refresh plugin registry, list, and check for updates"))
        self.refresh_all_button.clicked.connect(self._refresh_all)
        toolbar_layout.addWidget(self.refresh_all_button)

        toolbar_layout.addStretch()

        self.details_toggle_button = QtWidgets.QPushButton(_("Hide Details"))
        self.details_toggle_button.setCheckable(True)
        self.details_toggle_button.setChecked(True)  # Details visible by default
        self.details_toggle_button.setToolTip(_("Show/hide plugin details panel"))
        self.details_toggle_button.clicked.connect(self._toggle_details_panel)
        toolbar_layout.addWidget(self.details_toggle_button)

        layout.addLayout(toolbar_layout)

        # Main content - splitter with plugin list and details
        self.splitter = QtWidgets.QSplitter()
        self.splitter.setObjectName("plugin_splitter")

        # Plugin list
        self.plugin_list = PluginListWidget()
        self.plugin_list.plugin_selection_changed.connect(self._on_plugin_selected)
        # Connect plugin state changes to refresh options dialog
        self.plugin_list.plugin_state_changed.connect(self._on_plugin_state_changed)
        # Connect update selected plugins signal
        self.plugin_list.update_selected_plugins.connect(self._update_plugins)
        self.splitter.addWidget(self.plugin_list)

        # Plugin details
        self.plugin_details = PluginDetailsWidget()
        self.plugin_details.plugin_uninstalled.connect(self.load)  # Refresh on uninstall
        self.plugin_details.plugin_updated.connect(self.load)  # Refresh on update
        self.splitter.addWidget(self.plugin_details)

        # Set splitter proportions
        self.splitter.setSizes([300, 200])

        layout.addWidget(self.splitter, 1)  # Give most space to splitter

        # Status mini-log (shows last 3 messages)
        self.status_log = QtWidgets.QTextEdit()
        self.status_log.setMaximumHeight(60)  # About 3 lines
        self.status_log.setReadOnly(True)
        self.status_log.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.status_messages = []  # Keep track of last 3 messages
        layout.addWidget(self.status_log, 0)  # Minimal space for status

    def _show_status(self, message, clear_after_ms=None):
        """Add message to status log (keeps last 3 messages)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"

        # Add to messages list and keep only last 3
        self.status_messages.append(formatted_message)
        if len(self.status_messages) > 3:
            self.status_messages.pop(0)

        # Update display
        self.status_log.setPlainText("\n".join(self.status_messages))
        # Scroll to bottom to show latest message
        self.status_log.verticalScrollBar().setValue(self.status_log.verticalScrollBar().maximum())
        QtWidgets.QApplication.processEvents()

    def load(self):
        """Load plugins from plugin manager."""
        self._show_status(_("Loading plugins..."))
        try:
            # Load plugins immediately when page is loaded
            self.all_plugins = self.plugin_manager.plugins
            # Validate persisted updates against current plugin state
            config = get_config()
            saved_updates = dict(config.persist['plugins3_updates'])
            valid_updates = {}
            for plugin in self.all_plugins:
                if plugin.plugin_id in saved_updates:
                    update_info = saved_updates[plugin.plugin_id]
                    # Check if the update is still valid (current commit == old_commit from update info)
                    current_commit = plugin.get_current_commit_id()
                    saved_old_commit = update_info.old_commit
                    if current_commit and saved_old_commit and current_commit == saved_old_commit:
                        valid_updates[plugin.plugin_id] = update_info
            config.persist['plugins3_updates'] = valid_updates
            # Pass current updates dict to plugin list widget
            self.plugin_list.set_updates(valid_updates)
            self._filter_plugins()
            self._show_status(_("Loaded {} plugins").format(len(self.all_plugins)))
            self._show_enabled_state()
            self._update_details_button_text()  # Update button state based on plugin availability
        except Exception as e:
            log.debug("Error loading plugins", exc_info=True)
            self._show_status(_("Error loading plugins: {}").format(str(e)))

    def _refresh_all(self):
        """Refresh registry, list, and update status."""
        self.refresh_all_button.setEnabled(False)
        self.refresh_all_button.setText(_("Refreshing..."))
        self._show_status(_("Refreshing plugin registry, list, and checking for updates..."))

        try:
            # Refresh registry from server
            if self.plugin_manager:
                self.plugin_manager.refresh_registry_and_caches()

                # Fetch remote refs for all plugins (for ref selectors)
                self.plugin_manager.refresh_all_plugin_refs()

            # Reload plugin list
            self.all_plugins = self.plugin_manager.plugins

            # Check for updates (silent - no dialog) - skip fetching since we just did it
            new_updates = self.plugin_manager.check_updates(skip_fetch=True)
            self._save_updates(new_updates)

            # Pass updates to widget
            self.plugin_list.set_updates(new_updates)

            # Refresh UI with network-fetched update status
            self._filter_plugins()

            self._show_status(
                _("Refreshed - {} plugins, {} updates available").format(len(self.all_plugins), len(new_updates))
            )

        except Exception as e:
            log.error("Failed to refresh all: %s", e, exc_info=True)
            self._show_status(_("Error refreshing: {}").format(str(e)))
        finally:
            self.refresh_all_button.setEnabled(True)
            self.refresh_all_button.setText(_("Refresh All"))

    def _show_disabled_state(self):
        """Show UI when plugin system is disabled."""
        self.plugin_list.clear()
        self.plugin_details.setVisible(False)
        self.install_button.setEnabled(False)
        self.refresh_all_button.setEnabled(False)
        self.search_edit.setEnabled(False)
        self._show_status(_("Plugin system not available - Git backend required"))

    def _show_enabled_state(self):
        """Show UI when plugin system is enabled."""
        self.install_button.setEnabled(True)
        self.refresh_all_button.setEnabled(True)
        self.search_edit.setEnabled(True)

    def _filter_plugins(self):
        """Filter plugins based on search text."""
        search_text = self.search_edit.text().lower()

        if not search_text:
            # Show all plugins
            filtered_plugins = self.all_plugins
        else:
            # Filter plugins by name
            filtered_plugins = []
            for plugin in self.all_plugins:
                if search_text in plugin.name().lower():
                    filtered_plugins.append(plugin)

        self.plugin_list.populate_plugins(filtered_plugins)
        self._update_details_button_text()  # Update button state based on filtered plugin count

    def save(self):
        """Save is handled automatically by direct config updates."""
        pass

    def _toggle_details_panel(self):
        """Toggle visibility of the plugin details panel."""
        is_visible = self.plugin_details.isVisible()

        if not is_visible:
            # Showing details - ensure a plugin is selected
            selected_items = self.plugin_list.selectedItems()
            if not selected_items and self.plugin_list.topLevelItemCount() > 0:
                # No selection but plugins available - select first plugin
                first_item = self.plugin_list.topLevelItem(0)
                self.plugin_list.setCurrentItem(first_item)

        self.plugin_details.setVisible(not is_visible)
        self._update_details_button_text()

    def _update_details_button_text(self):
        """Update the details button text based on panel visibility."""
        # Disable button if no plugins available
        has_plugins = self.plugin_list.topLevelItemCount() > 0
        self.details_toggle_button.setEnabled(has_plugins)

        if self.plugin_details.isVisible():
            self.details_toggle_button.setText(_("Hide Details"))
            self.details_toggle_button.setChecked(True)
        else:
            self.details_toggle_button.setText(_("Show Details"))
            self.details_toggle_button.setChecked(False)

    def _on_plugin_selected(self, plugin):
        """Handle plugin selection."""
        # Get cached update status to avoid network call
        has_update = None
        if plugin:
            config = get_config()
            has_update = plugin.plugin_id in config.persist['plugins3_updates']

        self.plugin_details.show_plugin(plugin, has_update)
        # Update button text since details are now shown
        self._update_details_button_text()

    def _on_plugin_state_changed(self, plugin, action):
        """Handle plugin state changes (enable/disable/uninstall)."""
        log.debug("_on_plugin_state_changed called: plugin=%s, action=%s", plugin.plugin_id, action)
        self._show_status(_("Plugin '{}' {}").format(plugin.name(), action))

        # Update the updates dict based on the action
        if action in ("updated", "reinstalled", "ref switched"):
            log.debug("Re-checking updates for plugin %s after action: %s", plugin.plugin_id, action)
            # Re-check for updates after the action
            try:
                new_updates = self.plugin_manager.check_updates()
                if plugin.plugin_id in new_updates:
                    log.debug("Plugin %s has update available after %s", plugin.plugin_id, action)
                else:
                    log.debug("Plugin %s has no updates after %s", plugin.plugin_id, action)
                self._save_updates(new_updates)
            except Exception as e:
                log.error("Failed to check updates after %s: %s", action, e)
                # Fallback: remove from updates dict
                config = get_config()
                config.persist['plugins3_updates'].pop(plugin.plugin_id, None)
            # Update the plugin list widget with new updates dict
            config = get_config()
            self.plugin_list.set_updates(config.persist['plugins3_updates'])
            # Refresh the plugin list display to show the changes
            self._filter_plugins()
        elif action == "uninstalled":
            # Remove from updates dict since plugin no longer exists
            config = get_config()
            config.persist['plugins3_updates'].pop(plugin.plugin_id, None)
            # Update the plugin list widget with new updates dict
            self.plugin_list.set_updates(config.persist['plugins3_updates'])
            # Refresh the plugin list display to show the changes
            self._filter_plugins()
            # Clean up plugin settings
            if plugin.plugin_id:
                self._cleanup_plugin_settings(plugin.plugin_id)

        # Refresh the options dialog to update plugin option pages
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.refresh_plugin_pages()
        else:
            pass  # No dialog found

    def _cleanup_plugin_settings(self, plugin_id):
        """Clean up plugin settings when plugin is uninstalled."""
        config = get_config()

        # Remove from do_not_update list
        do_not_update = list(config.persist['plugins3_do_not_update'])
        if plugin_id in do_not_update:
            do_not_update.remove(plugin_id)
            config.persist['plugins3_do_not_update'] = do_not_update

        # Remove from updates dict
        if plugin_id in config.persist['plugins3_updates']:
            config.persist['plugins3_updates'].pop(plugin_id)

    def _install_plugin(self):
        """Show install plugin dialog."""
        dialog = InstallPluginDialog(self)
        dialog.plugin_installed.connect(self._on_plugin_installed)
        dialog.exec()

    def _on_plugin_installed(self, plugin_id):
        """Handle plugin installation completion."""
        log.debug("_on_plugin_installed called for plugin: %s", plugin_id)

        # Check for updates BEFORE loading the plugin list
        try:
            log.debug("Checking for updates after plugin installation")
            new_updates = self.plugin_manager.check_updates()
            self._save_updates(new_updates)
            config = get_config()
            log.debug("Updated plugin list with %d updates", len(config.persist['plugins3_updates']))
        except Exception as e:
            log.error("Failed to check updates after plugin installation: %s", e)

        # Now load and refresh the plugin list with updates available
        self.load()  # This will call set_updates() with the current updates dict

        self._show_status(_("Plugin '{}' installed successfully").format(plugin_id))
        # Refresh the options dialog to show new plugin option pages
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.refresh_plugin_pages()

    def _update_plugins(self, plugins):
        """Update multiple plugins."""
        if not plugins:
            return

        # Disable UI during updates
        self.refresh_all_button.setEnabled(False)
        self.install_button.setEnabled(False)

        async_manager = AsyncPluginManager(self.plugin_manager)

        # For simplicity, update plugins one by one
        # TODO: Could be enhanced to use update_all_plugins for batch updates
        self._update_queue = plugins.copy()
        self._update_next_plugin(async_manager)

    def _update_next_plugin(self, async_manager):
        """Update the next plugin in the queue."""
        if not self._update_queue:
            # All updates complete
            self.refresh_all_button.setEnabled(True)
            self.install_button.setEnabled(True)
            self._show_status(_("All plugin updates completed"))
            # Refresh display to show updated status
            self._filter_plugins()
            return

        plugin = self._update_queue.pop(0)
        self._show_status(_("Updating {}...").format(plugin.name or plugin.plugin_id))

        # Mark plugin as updating in UI
        self.plugin_list.mark_plugin_updating(plugin)

        async_manager.update_plugin(
            plugin=plugin,
            progress_callback=None,
            callback=partial(self._on_plugin_update_complete, async_manager, plugin),
        )

    def _on_plugin_update_complete(self, async_manager, plugin, result):
        """Handle individual plugin update completion."""
        # Mark plugin update as complete in UI
        self.plugin_list.mark_plugin_update_complete(plugin)

        if result.success:
            # Remove updated plugin from updates dict since it's now up-to-date
            config = get_config()
            config.persist['plugins3_updates'].pop(plugin.plugin_id, None)
            # Update the plugin list widget with new updates dict
            self.plugin_list.set_updates(config.persist['plugins3_updates'])
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.warning(self, _("Update Failed"), _("Failed to update plugin: {}").format(error_msg))

        # Continue with next plugin
        self._update_next_plugin(async_manager)


register_options_page(Plugins3OptionsPage)
