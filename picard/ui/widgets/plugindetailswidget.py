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

from PyQt6 import QtCore, QtWidgets

from picard.i18n import gettext as _
from picard.plugin3.asyncops.manager import AsyncPluginManager
from picard.plugin3.plugin import short_commit_id

from picard.ui.widgets.pluginlistwidget import UninstallPluginDialog


class PluginDetailsWidget(QtWidgets.QWidget):
    """Widget for displaying plugin details."""

    plugin_uninstalled = QtCore.pyqtSignal()  # Emitted when plugin is uninstalled
    plugin_updated = QtCore.pyqtSignal()  # Emitted when plugin is updated

    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.git_url_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
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
                plugin_name = plugin.manifest.name() or plugin.name or plugin.plugin_id
            except Exception:
                plugin_name = plugin.name or plugin.plugin_id
        elif plugin.name:
            plugin_name = plugin.name

        self.name_label.setText(plugin_name)

        # Get description from manifest
        description = _("No description available")
        if plugin.manifest and hasattr(plugin.manifest, 'description'):
            try:
                description = plugin.manifest.description() or description
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

        self.setVisible(True)

    def _uninstall_plugin(self):
        """Uninstall the current plugin."""
        if not self.current_plugin:
            return

        dialog = UninstallPluginDialog(self.current_plugin, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            tagger = QtWidgets.QApplication.instance()
            if hasattr(tagger, 'pluginmanager3') and tagger.pluginmanager3:
                try:
                    async_manager = AsyncPluginManager(tagger.pluginmanager3)
                    async_manager.uninstall_plugin(
                        self.current_plugin, purge=dialog.purge_config, callback=self._on_uninstall_complete
                    )
                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        self, _("Uninstall Failed"), _("Failed to uninstall plugin: {}").format(str(e))
                    )

    def _on_uninstall_complete(self, result):
        """Handle uninstall completion."""
        if result.success:
            self.show_plugin(None)  # Clear details
            self.plugin_uninstalled.emit()  # Signal that plugin was uninstalled
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Uninstall Failed"), error_msg)

    def _get_version_display(self, plugin):
        """Get version display text."""
        # Try to get version from manifest first
        if plugin.manifest and hasattr(plugin.manifest, '_data'):
            version = plugin.manifest._data.get('version')
            if version:
                return version

        # Fallback to git ref from metadata if no version in manifest
        try:
            plugin_uuid = plugin.manifest.uuid if plugin.manifest else None
            if plugin_uuid:
                tagger = QtWidgets.QApplication.instance()
                if hasattr(tagger, "pluginmanager3") and tagger.pluginmanager3:
                    metadata = tagger.pluginmanager3._get_plugin_metadata(plugin_uuid)
                    if metadata:
                        git_info = self._format_git_info(metadata)
                        if git_info:
                            return git_info
        except Exception:
            pass

        return _("Unknown")

    def _get_authors_display(self, plugin):
        """Get authors display text."""
        if plugin.manifest and hasattr(plugin.manifest, 'authors'):
            authors = plugin.manifest.authors
            if authors:
                return ", ".join(authors)
        return _("Unknown")

    def _get_plugin_remote_url(self, plugin):
        """Get plugin remote URL from metadata."""
        tagger = QtWidgets.QApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            return None

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

    def _get_trust_level_display(self, plugin):
        """Get trust level display text."""
        tagger = QtWidgets.QApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            return _("Unknown")

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

    def _get_git_ref_display(self, plugin):
        """Get git ref display text."""
        try:
            plugin_uuid = plugin.manifest.uuid if plugin.manifest else None
            if plugin_uuid:
                tagger = QtWidgets.QApplication.instance()
                if hasattr(tagger, "pluginmanager3") and tagger.pluginmanager3:
                    metadata = tagger.pluginmanager3._get_plugin_metadata(plugin_uuid)
                    if metadata:
                        git_info = self._format_git_info(metadata)
                        if git_info:
                            return git_info
        except Exception:
            pass
        return _("N/A")

    def _get_git_url_display(self, plugin):
        """Get git URL display text."""
        remote_url = self._get_plugin_remote_url(plugin)
        if remote_url:
            return remote_url
        return _("N/A")

    def _has_update_available(self, plugin):
        """Check if plugin has update available."""
        tagger = QtWidgets.QApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            return False

        # Use the manager's method which handles versioning schemes correctly
        return tagger.pluginmanager3.has_plugin_update(plugin)

    def _update_plugin(self):
        """Update the current plugin."""
        if not self.current_plugin:
            return

        # Confirm update
        reply = QtWidgets.QMessageBox.question(
            self,
            _("Update Plugin"),
            _("Are you sure you want to update '{}'?").format(
                self.current_plugin.name or self.current_plugin.plugin_id
            ),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self._perform_update()

    def _perform_update(self):
        """Perform the plugin update."""
        tagger = QtWidgets.QApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            return

        # Disable update button during update
        self.update_button.setEnabled(False)
        self.update_button.setText(_("Updating..."))

        # Import AsyncPluginManager
        from picard.plugin3.asyncops.manager import AsyncPluginManager

        async_manager = AsyncPluginManager(tagger.pluginmanager3)
        async_manager.update_plugin(
            plugin=self.current_plugin, progress_callback=None, callback=self._on_update_complete
        )

    def _on_update_complete(self, result):
        """Handle update completion."""
        self.update_button.setText(_("Update"))

        if result.success:
            self.plugin_updated.emit()  # Signal that plugin was updated
            # Refresh the display
            self.show_plugin(self.current_plugin)
        else:
            self.update_button.setEnabled(True)
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Update Failed"), error_msg)
