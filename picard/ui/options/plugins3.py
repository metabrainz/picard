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

from PyQt6 import QtWidgets

from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_, gettext as _

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

    def __init__(self, api=None, parent=None):
        super().__init__(api=api, parent=parent)
        self.all_plugins = []  # Store all plugins for filtering
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Toolbar
        toolbar_layout = QtWidgets.QHBoxLayout()

        # Search box
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText(_("Search plugins..."))
        self.search_edit.textChanged.connect(self._filter_plugins)
        toolbar_layout.addWidget(self.search_edit)

        toolbar_layout.addStretch()

        self.install_button = QtWidgets.QPushButton(_("Install Plugin"))
        self.install_button.clicked.connect(self._install_plugin)
        toolbar_layout.addWidget(self.install_button)

        self.check_updates_button = QtWidgets.QPushButton(_("Check for Updates"))
        self.check_updates_button.clicked.connect(self._check_for_updates)
        toolbar_layout.addWidget(self.check_updates_button)

        toolbar_layout.addStretch()

        self.refresh_button = QtWidgets.QPushButton(_("Refresh"))
        self.refresh_button.clicked.connect(self.load)
        toolbar_layout.addWidget(self.refresh_button)

        layout.addLayout(toolbar_layout)

        # Main content - splitter with plugin list and details
        splitter = QtWidgets.QSplitter()
        splitter.setObjectName("plugin_splitter")

        # Plugin list
        self.plugin_list = PluginListWidget()
        self.plugin_list.plugin_selection_changed.connect(self._on_plugin_selected)
        # Connect plugin state changes to refresh options dialog
        self.plugin_list.plugin_state_changed.connect(self._on_plugin_state_changed)
        splitter.addWidget(self.plugin_list)

        # Plugin details
        self.plugin_details = PluginDetailsWidget()
        self.plugin_details.plugin_uninstalled.connect(self.load)  # Refresh on uninstall
        self.plugin_details.plugin_updated.connect(self.load)  # Refresh on update
        splitter.addWidget(self.plugin_details)

        # Set splitter proportions
        splitter.setSizes([300, 200])

        layout.addWidget(splitter)

        # Status label
        self.status_label = QtWidgets.QLabel()
        layout.addWidget(self.status_label)

    def load(self):
        """Load plugins from plugin manager."""
        # Check plugin system availability once
        if not hasattr(self.tagger, 'pluginmanager3') or not self.tagger.pluginmanager3:
            self._show_disabled_state()
            return

        try:
            self.all_plugins = self.tagger.pluginmanager3.plugins
            self._filter_plugins()  # Apply current filter
            self.status_label.setText(_("Loaded {} plugins").format(len(self.all_plugins)))
            self._show_enabled_state()
        except Exception as e:
            self.status_label.setText(_("Error loading plugins: {}").format(str(e)))

    def _show_disabled_state(self):
        """Show UI when plugin system is disabled."""
        self.plugin_list.clear()
        self.plugin_details.setVisible(False)
        self.install_button.setEnabled(False)
        self.check_updates_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.search_edit.setEnabled(False)
        self.status_label.setText(_("Plugin system not available - Git backend required"))

    def _show_enabled_state(self):
        """Show UI when plugin system is enabled."""
        self.install_button.setEnabled(True)
        self.check_updates_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.search_edit.setEnabled(True)

    def _filter_plugins(self):
        """Filter plugins based on search text."""
        search_text = self.search_edit.text().lower()

        if not search_text:
            # Show all plugins
            filtered_plugins = self.all_plugins
        else:
            # Filter plugins by name, plugin_id, or description
            filtered_plugins = []
            for plugin in self.all_plugins:
                if (
                    search_text in (plugin.name or "").lower()
                    or search_text in plugin.plugin_id.lower()
                    or search_text in getattr(plugin, "description", "").lower()
                ):
                    filtered_plugins.append(plugin)

        self.plugin_list.populate_plugins(filtered_plugins)

    def save(self):
        """Save is handled automatically by plugin enable/disable."""
        pass

    def _on_plugin_selected(self, plugin):
        """Handle plugin selection."""
        self.plugin_details.show_plugin(plugin)

    def _on_plugin_state_changed(self):
        """Handle plugin state changes (enable/disable/uninstall)."""
        # Refresh the options dialog to update plugin option pages
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.refresh_plugin_pages()
        else:
            pass  # No dialog found

    def _install_plugin(self):
        """Show install plugin dialog."""
        dialog = InstallPluginDialog(self)
        dialog.plugin_installed.connect(self._on_plugin_installed)
        dialog.exec()

    def _on_plugin_installed(self, plugin_id):
        """Handle plugin installation completion."""
        self.load()  # Refresh plugin list
        self.status_label.setText(_("Plugin '{}' installed successfully").format(plugin_id))
        # Refresh the options dialog to show new plugin option pages
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.refresh_plugin_pages()

    def _check_for_updates(self):
        """Check for plugin updates."""
        # Plugin system availability already checked in load()
        self.check_updates_button.setEnabled(False)
        self.check_updates_button.setText(_("Checking..."))
        self.status_label.setText(_("Checking for plugin updates..."))

        try:
            # Use the manager's check_updates method (which handles versioning schemes correctly)
            updates = self.tagger.pluginmanager3.check_updates()

            if updates:
                # Convert UpdateCheck objects to plugins for the dialog
                plugins_with_updates = []
                for update in updates:
                    # Find the plugin object by plugin_id
                    for plugin in self.tagger.pluginmanager3.plugins:
                        if plugin.plugin_id == update.plugin_id:
                            plugins_with_updates.append(plugin)
                            break

                self.status_label.setText(
                    _("Found {} plugin(s) with updates available").format(len(plugins_with_updates))
                )
                self._show_update_dialog(plugins_with_updates)
            else:
                self.status_label.setText(_("All plugins are up to date"))

        except Exception as e:
            self.status_label.setText(_("Error checking for updates: {}").format(str(e)))
        finally:
            self.check_updates_button.setEnabled(True)
            self.check_updates_button.setText(_("Check for Updates"))

    def _show_update_dialog(self, plugins_with_updates):
        """Show dialog with available updates."""
        plugin_names = [p.name or p.plugin_id for p in plugins_with_updates]
        reply = QtWidgets.QMessageBox.question(
            self,
            _("Updates Available"),
            _("The following plugins have updates available:\n\n{}\n\nWould you like to update them now?").format(
                "\n".join(f"• {name}" for name in plugin_names)
            ),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self._update_plugins(plugins_with_updates)

    def _update_plugins(self, plugins):
        """Update multiple plugins."""
        if not plugins:
            return

        # Disable UI during updates
        self.check_updates_button.setEnabled(False)
        self.install_button.setEnabled(False)

        from picard.plugin3.asyncops.manager import AsyncPluginManager

        async_manager = AsyncPluginManager(self.tagger.pluginmanager3)

        # For simplicity, update plugins one by one
        # TODO: Could be enhanced to use update_all_plugins for batch updates
        self._update_queue = plugins.copy()
        self._update_next_plugin(async_manager)

    def _update_next_plugin(self, async_manager):
        """Update the next plugin in the queue."""
        if not self._update_queue:
            # All updates complete
            self.check_updates_button.setEnabled(True)
            self.install_button.setEnabled(True)
            self.status_label.setText(_("All plugin updates completed"))
            self.load()  # Refresh plugin list
            return

        plugin = self._update_queue.pop(0)
        self.status_label.setText(_("Updating {}...").format(plugin.name or plugin.plugin_id))

        async_manager.update_plugin(
            plugin=plugin,
            progress_callback=None,
            callback=lambda result, am=async_manager: self._on_plugin_update_complete(result, am),
        )

    def _on_plugin_update_complete(self, result, async_manager):
        """Handle individual plugin update completion."""
        if not result.success:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.warning(self, _("Update Failed"), _("Failed to update plugin: {}").format(error_msg))

        # Continue with next plugin
        self._update_next_plugin(async_manager)


register_options_page(Plugins3OptionsPage)
