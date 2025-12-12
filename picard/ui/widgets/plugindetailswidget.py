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

from picard.ui.widgets.pluginlistwidget import UninstallPluginDialog


class PluginDetailsWidget(QtWidgets.QWidget):
    """Widget for displaying plugin details."""

    plugin_uninstalled = QtCore.pyqtSignal()  # Emitted when plugin is uninstalled
    plugin_updated = QtCore.pyqtSignal()  # Emitted when plugin is updated

    def __init__(self, parent=None):
        super().__init__(parent)
        # Cache tagger instance for performance
        self.tagger = QtWidgets.QApplication.instance()
        self.plugin_manager = self.tagger.get_plugin_manager()
        if not self.plugin_manager:
            raise RuntimeError("Plugin manager not available")

        self.setup_ui()
        self.current_plugin = None

    def setup_ui(self):
        """Setup the details widget."""
        layout = QtWidgets.QVBoxLayout(self)

        # Plugin name
        self.name_label = QtWidgets.QLabel()
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.name_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.name_label)

        # Description
        self.description_label = QtWidgets.QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.description_label)

        # Details grid
        details_widget = QtWidgets.QWidget()
        details_layout = QtWidgets.QFormLayout(details_widget)

        self.version_label = QtWidgets.QLabel()
        self.version_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addRow(_("Version:"), self.version_label)

        self.authors_label = QtWidgets.QLabel()
        self.authors_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addRow(_("Authors:"), self.authors_label)

        self.trust_level_label = QtWidgets.QLabel()
        self.trust_level_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addRow(_("Trust Level:"), self.trust_level_label)

        self.plugin_id_label = QtWidgets.QLabel()
        self.plugin_id_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addRow(_("Plugin ID:"), self.plugin_id_label)

        self.git_ref_label = QtWidgets.QLabel()
        self.git_ref_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addRow(_("Git Ref:"), self.git_ref_label)

        self.git_url_label = QtWidgets.QLabel()
        self.git_url_label.setWordWrap(True)
        self.git_url_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse | QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.git_url_label.setOpenExternalLinks(True)
        details_layout.addRow(_("Repository:"), self.git_url_label)

        layout.addWidget(details_widget)

        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.update_button = QtWidgets.QPushButton(_("Update"))
        self.update_button.clicked.connect(self._update_plugin)
        button_layout.addWidget(self.update_button)

        self.uninstall_button = QtWidgets.QPushButton(_("Uninstall"))
        self.uninstall_button.clicked.connect(self._uninstall_plugin)
        button_layout.addWidget(self.uninstall_button)

        self.description_button = QtWidgets.QPushButton(_("Full Description"))
        self.description_button.clicked.connect(self._show_full_description)
        button_layout.addWidget(self.description_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()

        # Initially hide everything
        self.setVisible(False)

    def show_plugin(self, plugin):
        """Show details for the given plugin."""
        self.current_plugin = plugin

        if plugin is None:
            self.setVisible(False)
            return

        # Get plugin name from manifest, fallback to plugin.name or plugin_id
        plugin_name = plugin.plugin_id  # Default fallback
        if plugin.manifest:
            try:
                plugin_name = plugin.manifest.name_i18n() or plugin.name or plugin.plugin_id
            except Exception:
                plugin_name = plugin.name or plugin.plugin_id
        elif plugin.name:
            plugin_name = plugin.name

        self.name_label.setText(plugin_name)

        # Get description from manifest
        description = _("No description available")
        if plugin.manifest and hasattr(plugin.manifest, 'description_i18n'):
            try:
                description = plugin.manifest.description_i18n() or description
            except Exception:
                pass
        self.description_label.setText(description)
        self.version_label.setText(self._get_version_display(plugin))
        self.authors_label.setText(self._get_authors_display(plugin))
        self.trust_level_label.setText(self._get_trust_level_display(plugin))
        self.plugin_id_label.setText(plugin.plugin_id)
        self.git_ref_label.setText(self._get_git_ref_display(plugin))
        self.git_url_label.setText(self._get_git_url_display(plugin))

        # Check if update is available and enable/disable update button
        self.update_button.setEnabled(self._has_update_available(plugin))

        # Enable/disable description button based on long description availability
        has_long_desc = self.plugin_manager.long_description_as_html(plugin) is not None
        self.description_button.setEnabled(has_long_desc)

        self.setVisible(True)

    def _show_full_description(self):
        """Show full plugin description in a dialog."""
        if not self.current_plugin:
            return

        html_desc = self.plugin_manager.long_description_as_html(self.current_plugin)
        if not html_desc:
            return

        # Create dialog to show full description
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(_("Plugin Description"))
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Plugin name
        try:
            name = self.current_plugin.manifest.name_i18n()
        except (AttributeError, Exception):
            name = self.current_plugin.name or self.current_plugin.plugin_id

        title_label = QtWidgets.QLabel(f"<h2>{name}</h2>")
        layout.addWidget(title_label)

        # Description text browser
        text_browser = QtWidgets.QTextBrowser()
        text_browser.setHtml(html_desc)
        text_browser.setOpenExternalLinks(True)
        layout.addWidget(text_browser)

        # Close button
        button_layout = QtWidgets.QHBoxLayout()

        # Homepage button (if available)
        homepage_url = self.plugin_manager.get_plugin_homepage(self.current_plugin)
        if homepage_url:
            homepage_button = QtWidgets.QPushButton(_("Open Homepage"))
            homepage_button.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(homepage_url)))
            button_layout.addWidget(homepage_button)

        button_layout.addStretch()
        close_button = QtWidgets.QPushButton(_("Close"))
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        dialog.exec()

    def _uninstall_plugin(self):
        """Uninstall the current plugin."""
        if not self.current_plugin:
            return

        # Find the plugin list widget and call its uninstall method
        plugin_list = self._find_plugin_list_widget()
        if plugin_list:
            plugin_list._uninstall_plugin_from_menu(self.current_plugin)
        else:
            # Fallback to old method if plugin list not found
            self._perform_uninstall()

    def _on_uninstall_complete(self, result):
        """Handle uninstall completion."""
        if result.success:
            # Emit the same signal as context menu for status updates
            if hasattr(self, '_uninstalling_plugin') and hasattr(self.parent(), 'plugin_state_changed'):
                self.parent().plugin_state_changed.emit(self._uninstalling_plugin, "uninstalled")
                delattr(self, '_uninstalling_plugin')
            self.show_plugin(None)  # Clear details
            self.plugin_uninstalled.emit()  # Signal that plugin was uninstalled
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Uninstall Failed"), error_msg)

    def _get_version_display(self, plugin):
        """Get version display text."""
        return self.plugin_manager.get_plugin_version_display(plugin)

    def _get_authors_display(self, plugin):
        """Get authors display text."""
        if plugin.manifest and hasattr(plugin.manifest, 'authors'):
            authors = plugin.manifest.authors
            if authors:
                return ", ".join(authors)
        return _("Unknown")

    def _get_plugin_remote_url(self, plugin):
        """Get plugin remote URL from metadata."""
        return self.plugin_manager.get_plugin_remote_url(plugin)

    def _format_git_info(self, metadata):
        """Format git information for display."""
        return self.plugin_manager.get_plugin_git_info(metadata)

    def _get_trust_level_display(self, plugin):
        """Get trust level display text."""
        try:
            registry = self.plugin_manager._registry

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

    def _get_git_ref_display(self, plugin):
        """Get git ref display text."""
        try:
            plugin_uuid = plugin.manifest.uuid if plugin.manifest else None
            if plugin_uuid:
                metadata = self.plugin_manager._get_plugin_metadata(plugin_uuid)
                if metadata:
                    git_info = self._format_git_info(metadata)
                    if git_info:
                        return git_info
        except Exception:
            pass
        return _("N/A")

    def _get_git_url_display(self, plugin):
        """Get git URL display text as clickable HTML link."""
        remote_url = self._get_plugin_remote_url(plugin)
        if remote_url and (remote_url.startswith('http://') or remote_url.startswith('https://')):
            return f'<a href="{remote_url}">{remote_url}</a>'
        elif remote_url:
            return remote_url
        return _("N/A")

    def _has_update_available(self, plugin):
        """Check if plugin has update available."""
        # Use the manager's method which handles versioning schemes correctly
        return self.plugin_manager.get_plugin_update_status(plugin)

    def _update_plugin(self):
        """Update the current plugin."""
        if not self.current_plugin:
            return

        # Find the plugin list widget and call its update method
        plugin_list = self._find_plugin_list_widget()
        if plugin_list:
            plugin_list._update_plugin_from_menu(self.current_plugin)
        else:
            # Fallback to old method if plugin list not found
            self._perform_update()

    def _find_plugin_list_widget(self):
        """Find the PluginListWidget in the parent hierarchy."""
        parent = self.parent()
        while parent:
            if hasattr(parent, '_update_plugin_from_menu'):
                return parent
            # Check if parent has a plugin_list attribute
            if hasattr(parent, 'plugin_list'):
                return parent.plugin_list
            parent = parent.parent()
        return None

    def _perform_uninstall(self):
        """Fallback uninstall method."""
        dialog = UninstallPluginDialog(self.current_plugin, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            try:
                self._uninstalling_plugin = self.current_plugin  # Store for callback
                async_manager = AsyncPluginManager(self.plugin_manager)
                async_manager.uninstall_plugin(
                    self.current_plugin, purge=dialog.purge_config, callback=self._on_uninstall_complete
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, _("Uninstall Failed"), _("Failed to uninstall plugin: {}").format(str(e))
                )

    def _perform_update(self):
        """Fallback update method."""
        # Disable update button during update
        self.update_button.setEnabled(False)
        self.update_button.setText(_("Updating..."))

        # Import AsyncPluginManager
        from picard.plugin3.asyncops.manager import AsyncPluginManager

        async_manager = AsyncPluginManager(self.plugin_manager)
        async_manager.update_plugin(
            plugin=self.current_plugin, progress_callback=None, callback=self._on_update_complete
        )

    def _on_update_complete(self, result):
        """Handle update completion."""
        self.update_button.setText(_("Update"))

        if result.success:
            self.plugin_updated.emit()  # Signal that plugin was updated
            # Emit the same signal as context menu for status updates
            if hasattr(self.parent(), 'plugin_state_changed'):
                self.parent().plugin_state_changed.emit(self.current_plugin, "updated")
            # Refresh the display
            self.show_plugin(self.current_plugin)
        else:
            self.update_button.setEnabled(True)
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Update Failed"), error_msg)
