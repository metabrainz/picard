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
from picard.plugin3.asyncops.manager import AsyncPluginManager
from picard.plugin3.plugin import PluginState
from picard.util import temporary_disconnect

from picard.ui.dialogs.installconfirm import InstallConfirmDialog
from picard.ui.dialogs.plugininfo import PluginInfoDialog


# Column positions
COLUMN_ENABLED = 0
COLUMN_PLUGIN = 1
COLUMN_VERSION = 2


class PluginListWidget(QtWidgets.QTreeWidget):
    """Widget for displaying and managing plugins."""

    plugin_selection_changed = QtCore.pyqtSignal(object)  # Emits selected plugin or None
    plugin_state_changed = QtCore.pyqtSignal()  # Emitted when plugin state changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._toggling_plugins = set()  # Track plugins being toggled
        self._failed_enables = set()  # Track plugins that failed to enable
        self.setup_ui()

    def setup_ui(self):
        """Setup the tree widget."""
        self.setHeaderLabels([_("Enabled"), _("Plugin"), _("Version")])
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        # Connect selection changes
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.itemClicked.connect(self._on_item_clicked)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Cache tagger instance for performance
        self.tagger = QtCore.QCoreApplication.instance()
        if not self.tagger or not hasattr(self.tagger, 'pluginmanager3'):
            raise RuntimeError("Plugin manager not available")

        # Cache plugin manager for performance
        self.plugin_manager = self.plugin_manager

        # Connect to plugin manager signals
        self.plugin_manager.plugin_ref_switched.connect(self._on_plugin_ref_switched)

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
            try:
                plugin_name = plugin.manifest.name()
            except (AttributeError, Exception):
                plugin_name = plugin.name or plugin.plugin_id
            item.setText(COLUMN_PLUGIN, plugin_name)

            # Add tooltip with description if available
            try:
                description = plugin.manifest.description()
                if description:
                    item.setToolTip(COLUMN_PLUGIN, description)
            except (AttributeError, Exception):
                pass

            # Column 2: Version
            item.setText(COLUMN_VERSION, self._get_version_display(plugin))

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
        return self.plugin_manager.get_plugin_remote_url(plugin)

    def _format_git_info(self, metadata):
        """Format git information for display."""
        return self.plugin_manager.get_plugin_git_info(metadata)

    def _get_version_display(self, plugin):
        """Get display text for plugin version."""
        version_text = self.plugin_manager.get_plugin_version_display(plugin)

        # Check if update is available and add indicator
        if self._has_update_available(plugin):
            version_text += " " + _("(Update available)")

        return version_text

    def _has_update_available(self, plugin):
        """Check if plugin has update available."""
        # Use the manager's method which handles versioning schemes correctly
        return self.plugin_manager.get_plugin_update_status(plugin)

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

                    # Emit signal for options dialog to refresh
                    self.plugin_state_changed.emit()

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
        plugins = self.plugin_manager.plugins

        # Use utility to temporarily disconnect signal during refresh
        with temporary_disconnect(self.itemClicked, self._on_item_clicked):
            self.populate_plugins(plugins)

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

        # Update action (if update available)
        if self._has_update_available(plugin):
            update_action = menu.addAction(_("Update"))
            update_action.triggered.connect(lambda: self._update_plugin_from_menu(plugin))

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
            self.plugin_state_changed.emit()
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
        from picard.plugin3.asyncops.manager import AsyncPluginManager

        async_manager = AsyncPluginManager(self.plugin_manager)
        async_manager.update_plugin(plugin=plugin, progress_callback=None, callback=self._on_context_update_complete)

    def _on_context_update_complete(self, result):
        """Handle context menu update completion."""
        if result.success:
            # Refresh the plugin list
            self.populate_plugins(self.plugin_manager.plugins)
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Update Failed"), error_msg)

    def _uninstall_plugin_from_menu(self, plugin):
        """Uninstall plugin from context menu."""
        dialog = UninstallPluginDialog(plugin, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            try:
                async_manager = AsyncPluginManager(self.plugin_manager)
                async_manager.uninstall_plugin(plugin, purge=dialog.purge_config, callback=self._on_uninstall_complete)
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, _("Uninstall Failed"), _("Failed to uninstall plugin: {}").format(str(e))
                )

    def _on_uninstall_complete(self, result):
        """Handle uninstall completion."""
        if result.success:
            self._refresh_plugin_list()
            # Emit signal for options dialog to refresh
            self.plugin_state_changed.emit()
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
                plugin_name = plugin.manifest.name()
            except (AttributeError, Exception):
                plugin_name = plugin.name or plugin.plugin_id

            # Show confirmation dialog
            confirm_dialog = InstallConfirmDialog(plugin_name, plugin_url, self)
            if confirm_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
                return

            async_manager = AsyncPluginManager(self.plugin_manager)
            async_manager.install_plugin(
                url=plugin_url,
                ref=confirm_dialog.selected_ref,
                reinstall=True,
                callback=self._on_reinstall_complete,
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, _("Reinstall Failed"), _("Failed to reinstall plugin: {}").format(str(e))
            )

    def _on_reinstall_complete(self, result):
        """Handle reinstall completion."""
        if result.success:
            self._refresh_plugin_list()
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Reinstall Failed"), error_msg)

    def _switch_ref_from_menu(self, plugin):
        """Switch plugin ref from context menu."""
        dialog = SwitchRefDialog(plugin, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            try:
                async_manager = AsyncPluginManager(self.plugin_manager)
                async_manager.switch_ref(plugin=plugin, ref=dialog.selected_ref, callback=self._on_switch_ref_complete)
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, _("Switch Ref Failed"), _("Failed to switch ref: {}").format(str(e))
                )

    def _on_switch_ref_complete(self, result):
        """Handle switch ref completion."""
        if result.success:
            self._refresh_plugin_list()
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
            name = self.plugin.manifest.name()
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

        uninstall_button = QtWidgets.QPushButton(_("Uninstall"))
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
        if not self.tagger or not hasattr(self.tagger, 'pluginmanager3'):
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
            name = self.plugin.manifest.name()
        except (AttributeError, Exception):
            name = self.plugin.name or self.plugin.plugin_id

        title_label = QtWidgets.QLabel(_("Switch ref for '{}'").format(name))
        title_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(title_label)

        # Tab widget for different ref types
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)

        # Tags tab
        tags_widget = QtWidgets.QWidget()
        tags_layout = QtWidgets.QVBoxLayout(tags_widget)
        self.tags_list = QtWidgets.QListWidget()
        tags_layout.addWidget(self.tags_list)
        self.tab_widget.addTab(tags_widget, _("Tags"))

        # Branches tab
        branches_widget = QtWidgets.QWidget()
        branches_layout = QtWidgets.QVBoxLayout(branches_widget)
        self.branches_list = QtWidgets.QListWidget()
        branches_layout.addWidget(self.branches_list)
        self.tab_widget.addTab(branches_widget, _("Branches"))

        # Custom tab
        custom_widget = QtWidgets.QWidget()
        custom_layout = QtWidgets.QVBoxLayout(custom_widget)
        custom_label = QtWidgets.QLabel(_("Enter tag, branch, or commit ID:"))
        custom_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        custom_layout.addWidget(custom_label)
        self.custom_edit = QtWidgets.QLineEdit()
        custom_layout.addWidget(self.custom_edit)
        self.tab_widget.addTab(custom_widget, _("Custom"))

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        switch_button = QtWidgets.QPushButton(_("Switch"))
        switch_button.clicked.connect(self._switch_ref)
        button_layout.addWidget(switch_button)

        cancel_button = QtWidgets.QPushButton(_("Cancel"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def load_refs(self):
        """Load available refs from repository."""
        try:
            # Get plugin URL from metadata
            uuid = self.plugin_manager._get_plugin_uuid(self.plugin)
            metadata = self.plugin_manager._get_plugin_metadata(uuid)
            if metadata and hasattr(metadata, 'url'):
                refs = self.plugin_manager.fetch_all_git_refs(metadata.url)

                # Populate tags
                for ref in refs.get('tags', []):
                    self.tags_list.addItem(ref['name'])

                # Populate branches
                for ref in refs.get('branches', []):
                    self.branches_list.addItem(ref['name'])
        except Exception:
            # If we can't fetch refs, user can still use custom input
            pass

    def _switch_ref(self):
        """Handle switch button click."""
        current_tab = self.tab_widget.currentIndex()

        if current_tab == 0:  # Tags
            current_item = self.tags_list.currentItem()
            if current_item:
                self.selected_ref = current_item.text()
        elif current_tab == 1:  # Branches
            current_item = self.branches_list.currentItem()
            if current_item:
                self.selected_ref = current_item.text()
        else:  # Custom
            self.selected_ref = self.custom_edit.text().strip()

        if self.selected_ref:
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, _("No Ref Selected"), _("Please select or enter a ref to switch to."))

    def _uninstall(self):
        """Handle uninstall button click."""
        self.purge_config = self.purge_checkbox.isChecked()
        self.accept()
