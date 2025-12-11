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

from PyQt6 import QtCore, QtGui, QtWidgets

from picard.i18n import gettext as _
from picard.plugin3.plugin import PluginState, short_commit_id
from picard.util import temporary_disconnect


# Column positions
COLUMN_ENABLED = 0
COLUMN_PLUGIN = 1
COLUMN_VERSION = 2
COLUMN_TRUST_LEVEL = 3


class PluginListWidget(QtWidgets.QTreeWidget):
    """Widget for displaying and managing plugins."""

    plugin_selection_changed = QtCore.pyqtSignal(object)  # Emits selected plugin or None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._toggling_plugins = set()  # Track plugins being toggled
        self._failed_enables = set()  # Track plugins that failed to enable
        self.setup_ui()

    def setup_ui(self):
        """Setup the tree widget."""
        self.setHeaderLabels([_("Enabled"), _("Plugin"), _("Version"), _("Trust Level")])
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        # Connect selection changes
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.itemClicked.connect(self._on_item_clicked)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def populate_plugins(self, plugins):
        """Populate the widget with plugins."""
        self.clear()

        for plugin in plugins:
            item = QtWidgets.QTreeWidgetItem()

            # Column 0: Checkbox only (no text)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                COLUMN_ENABLED,
                QtCore.Qt.CheckState.Checked if self._is_plugin_enabled(plugin) else QtCore.Qt.CheckState.Unchecked,
            )

            # Column 1: Plugin name
            item.setText(COLUMN_PLUGIN, plugin.name or plugin.plugin_id)

            # Column 2: Version
            item.setText(COLUMN_VERSION, self._get_version_display(plugin))

            # Column 3: Trust level
            item.setText(COLUMN_TRUST_LEVEL, self._get_trust_level_display(plugin))

            # Store plugin reference
            item.setData(COLUMN_ENABLED, QtCore.Qt.ItemDataRole.UserRole, plugin)

            self.addTopLevelItem(item)

        # Resize columns to content
        for i in range(self.columnCount()):
            self.resizeColumnToContents(i)

    def _is_plugin_enabled(self, plugin):
        """Check if plugin is enabled."""
        return plugin.state == PluginState.ENABLED

    def _get_plugin_remote_url(self, plugin):
        """Get plugin remote URL from metadata."""
        tagger = QtCore.QCoreApplication.instance()
        # Assume plugin manager is available if this widget is being used
        try:
            plugin_uuid = plugin.manifest.uuid if plugin.manifest else None
            if plugin_uuid:
                metadata = tagger.pluginmanager3._get_plugin_metadata(plugin_uuid)
                if metadata and hasattr(metadata, 'url'):
                    return metadata.url
        except Exception:
            pass
        return None

    def _format_git_info(self, metadata):
        """Format git ref and commit info compactly (reused from CLI).

        Returns string like "ref @commit" or "@commit" if ref is a commit hash.
        Returns empty string if no metadata.
        """
        if not metadata:
            return ''

        ref = metadata.ref or ''
        commit = metadata.commit or ''

        if not commit:
            return ''

        commit_short = short_commit_id(commit)
        # Skip ref if it's a commit hash (same as or starts with the commit short ID)
        if ref and not ref.startswith(commit_short):
            return f'{ref} @{commit_short}'
        return f'@{commit_short}'

    def _get_version_display(self, plugin):
        """Get display text for plugin version."""
        version_text = ""

        # Try to get version from manifest first
        if plugin.manifest and hasattr(plugin.manifest, '_data'):
            version = plugin.manifest._data.get('version')
            if version:
                version_text = version

        # Fallback to git ref from metadata if no version in manifest
        if not version_text:
            try:
                plugin_uuid = plugin.manifest.uuid if plugin.manifest else None
                if plugin_uuid:
                    tagger = QtCore.QCoreApplication.instance()
                    if hasattr(tagger, "pluginmanager3") and tagger.pluginmanager3:
                        metadata = tagger.pluginmanager3._get_plugin_metadata(plugin_uuid)
                        if metadata:
                            git_info = self._format_git_info(metadata)
                            if git_info:
                                version_text = git_info
            except Exception:
                pass

        if not version_text:
            version_text = _("Unknown")

        # Check if update is available
        if self._has_update_available(plugin):
            version_text += " " + _("(Update available)")

        return version_text

    def _has_update_available(self, plugin):
        """Check if plugin has update available."""
        remote_url = self._get_plugin_remote_url(plugin)
        if not remote_url:
            return False

        tagger = QtCore.QCoreApplication.instance()
        try:
            # Get current ref from metadata
            plugin_uuid = plugin.manifest.uuid if plugin.manifest else None
            if not plugin_uuid:
                return False

            metadata = tagger.pluginmanager3._get_plugin_metadata(plugin_uuid)
            if not metadata or not hasattr(metadata, 'ref'):
                return False

            current_ref = metadata.ref

            # Check if there's a newer ref available
            refs_cache = tagger.pluginmanager3._refs_cache
            latest_ref = refs_cache.get_latest_ref(remote_url)
            return latest_ref and latest_ref != current_ref
        except Exception:
            return False

    def _get_trust_level_display(self, plugin):
        """Get display text for trust level."""
        tagger = QtCore.QCoreApplication.instance()
        try:
            registry = tagger.pluginmanager3._registry

            # Get remote URL from metadata
            remote_url = self._get_plugin_remote_url(plugin)
            if remote_url:
                trust_level = registry.get_trust_level(remote_url)
                return self._format_trust_level(trust_level)

            # For local plugins without remote_url, show as Local
            return _("Local")

        except Exception:
            pass

        return _("Unknown")

    def _format_trust_level(self, trust_level):
        """Format trust level for display."""
        trust_map = {
            "official": _("Official"),
            "trusted": _("Trusted"),
            "community": _("Community"),
            "unregistered": _("Unregistered"),
        }
        return trust_map.get(trust_level, _("Unknown"))

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
        if column == COLUMN_ENABLED:  # Only handle clicks on the checkbox column
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
                    from PyQt6 import QtWidgets

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
        tagger = QtCore.QCoreApplication.instance()
        plugins = tagger.pluginmanager3.plugins

        # Use utility to temporarily disconnect signal during refresh
        with temporary_disconnect(self.itemClicked, self._on_item_clicked):
            self.populate_plugins(plugins)

    def _toggle_plugin(self, plugin, enabled):
        """Toggle plugin enabled state."""
        tagger = QtCore.QCoreApplication.instance()
        if enabled:
            tagger.pluginmanager3.enable_plugin(plugin)
        else:
            tagger.pluginmanager3.disable_plugin(plugin)

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

        # Update action (if update available)
        if self._has_update_available(plugin):
            update_action = menu.addAction(_("Update"))
            update_action.triggered.connect(lambda: self._update_plugin_from_menu(plugin))

        # Uninstall action
        uninstall_action = menu.addAction(_("Uninstall"))
        uninstall_action.triggered.connect(lambda: self._uninstall_plugin_from_menu(plugin))

        menu.addSeparator()

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
        tagger = QtCore.QCoreApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            return

        from picard.plugin3.asyncops.manager import AsyncPluginManager

        async_manager = AsyncPluginManager(tagger.pluginmanager3)
        async_manager.update_plugin(plugin=plugin, progress_callback=None, callback=self._on_context_update_complete)

    def _on_context_update_complete(self, result):
        """Handle context menu update completion."""
        if result.success:
            # Refresh the plugin list
            tagger = QtCore.QCoreApplication.instance()
            if hasattr(tagger, "pluginmanager3") and tagger.pluginmanager3:
                self.populate_plugins(tagger.pluginmanager3.plugins)
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Update Failed"), error_msg)

    def _uninstall_plugin_from_menu(self, plugin):
        """Uninstall plugin from context menu."""
        reply = QtWidgets.QMessageBox.question(
            self,
            _("Uninstall Plugin"),
            _("Are you sure you want to uninstall '{}'?").format(plugin.name or plugin.plugin_id),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            tagger = QtCore.QCoreApplication.instance()
            if hasattr(tagger, "pluginmanager3") and tagger.pluginmanager3:
                try:
                    tagger.pluginmanager3.uninstall_plugin(plugin)
                    # Refresh the plugin list
                    self.populate_plugins(tagger.pluginmanager3.plugins)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        self, _("Uninstall Failed"), _("Failed to uninstall plugin: {}").format(str(e))
                    )

    def _view_repository(self, plugin):
        """Open plugin repository in browser."""
        remote_url = self._get_plugin_remote_url(plugin)
        if remote_url:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(remote_url))
