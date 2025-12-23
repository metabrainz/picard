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

from PyQt6 import QtCore, QtWidgets

from picard.i18n import gettext as _
from picard.plugin3.asyncops.manager import AsyncPluginManager

from picard.ui.dialogs.plugininfo import PluginInfoDialog
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
        # Set minimum width to prevent resizing when content changes
        self.setMinimumWidth(250)

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
        self.details_layout = QtWidgets.QFormLayout(details_widget)

        self.git_ref_label = QtWidgets.QLabel()
        self.git_ref_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_layout.addRow(_("Version:"), self.git_ref_label)

        self.authors_label = QtWidgets.QLabel()
        self.authors_label.setWordWrap(True)
        self.authors_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_layout.addRow(_("Authors:"), self.authors_label)

        self.maintainers_label = QtWidgets.QLabel()
        self.maintainers_label.setWordWrap(True)
        self.maintainers_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_layout.addRow(_("Maintainers:"), self.maintainers_label)

        self.git_url_label = QtWidgets.QLabel()
        self.git_url_label.setWordWrap(True)
        self.git_url_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse | QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.git_url_label.setOpenExternalLinks(True)
        self.details_layout.addRow(_("Repository:"), self.git_url_label)

        layout.addWidget(details_widget)

        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.update_button = QtWidgets.QPushButton(_("Update"))
        self.update_button.clicked.connect(self._update_plugin)
        button_layout.addWidget(self.update_button)

        self.uninstall_button = QtWidgets.QPushButton(_("Uninstall"))
        self.uninstall_button.clicked.connect(self._uninstall_plugin)
        button_layout.addWidget(self.uninstall_button)

        self.description_button = QtWidgets.QPushButton(_("Information"))
        self.description_button.clicked.connect(self._show_full_description)
        button_layout.addWidget(self.description_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()

        # Initially hide everything
        self.setVisible(False)

    def show_plugin(self, plugin, has_update=None):
        """Show details for the given plugin.

        Args:
            plugin: Plugin to show
            has_update: Optional cached update status to avoid network call
        """
        self.current_plugin = plugin

        if plugin is None:
            self.setVisible(False)
            return

        self.name_label.setText(plugin.name())

        # Get description from manifest
        description = _("No description available")
        if plugin.manifest and hasattr(plugin.manifest, 'description_i18n'):
            try:
                description = plugin.manifest.description_i18n() or description
            except Exception:
                pass
        self.description_label.setText(description)

        # Show/hide rows based on available data
        git_ref = self._get_git_ref_display(plugin)
        self.details_layout.setRowVisible(self.git_ref_label, bool(git_ref))
        if git_ref:
            self.git_ref_label.setText(git_ref)

        authors = self._get_authors_display(plugin)
        self.details_layout.setRowVisible(self.authors_label, bool(authors))
        if authors:
            self.authors_label.setText(authors)

        maintainers = self._get_maintainers_display(plugin)
        self.details_layout.setRowVisible(self.maintainers_label, bool(maintainers))
        if maintainers:
            self.maintainers_label.setText(maintainers)

        git_url = self._get_git_url_display(plugin)
        self.details_layout.setRowVisible(self.git_url_label, bool(git_url))
        if git_url:
            self.git_url_label.setText(git_url)

        # Check if update is available - use cached value if provided, otherwise disable button
        if has_update is not None:
            self.update_button.setEnabled(has_update)
        else:
            # Don't check for updates during normal display to avoid network calls
            self.update_button.setEnabled(False)

        # Always enable description button since PluginInfoDialog shows comprehensive info
        self.description_button.setEnabled(True)

        self.setVisible(True)

    def _show_full_description(self):
        """Show plugin information dialog (same as context menu Information)."""
        if not self.current_plugin:
            return

        dialog = PluginInfoDialog(self.current_plugin, self)
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

    def _on_uninstall_complete(self, plugin, result):
        """Handle uninstall completion."""
        if result.success:
            # Emit the same signal as context menu for status updates
            if hasattr(self.parent(), 'plugin_state_changed'):
                self.parent().plugin_state_changed.emit(plugin, "uninstalled")
            self.show_plugin(None)  # Clear details
            self.plugin_uninstalled.emit()  # Signal that plugin was uninstalled
        else:
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Uninstall Failed"), error_msg)

    def _get_authors_display(self, plugin):
        """Get authors display text."""
        if plugin.manifest and hasattr(plugin.manifest, 'authors'):
            authors = plugin.manifest.authors
            if authors:
                return ", ".join(authors)
        return ""

    def _get_maintainers_display(self, plugin):
        """Get maintainers display text."""
        if plugin.manifest and hasattr(plugin.manifest, 'maintainers'):
            maintainers = plugin.manifest.maintainers
            if maintainers:
                return ", ".join(maintainers)
        return ""

    def _get_plugin_remote_url(self, plugin):
        """Get plugin remote URL from metadata."""
        return self.plugin_manager.get_plugin_remote_url(plugin)

    def _format_git_info(self, metadata):
        """Format git information for display."""
        return self.plugin_manager.get_plugin_git_info(metadata)

    def _get_git_ref_display(self, plugin):
        """Get git ref display text."""
        try:
            if plugin.uuid:
                metadata = self.plugin_manager._get_plugin_metadata(plugin.uuid)
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
        return ""

    def _update_plugin(self):
        """Update the current plugin."""
        if not self.current_plugin:
            return

        # Check if plugin is in do_not_update list and ask for confirmation
        if self.current_plugin:
            from picard.config import get_config

            config = get_config()
            do_not_update = config.persist['plugins3_do_not_update']
            plugin_id = self.current_plugin.plugin_id

            if plugin_id in do_not_update:
                # Ask for confirmation
                reply = QtWidgets.QMessageBox.question(
                    self,
                    _("Update Plugin"),
                    _("Plugin '{}' is set to not update automatically.\n\nDo you want to update it anyway?").format(
                        self.current_plugin.name()
                    ),
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                    QtWidgets.QMessageBox.StandardButton.No,
                )

                if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                    return

                # Clear the do_not_update flag if user confirmed
                do_not_update = list(do_not_update)
                do_not_update.remove(plugin_id)
                config.persist['plugins3_do_not_update'] = do_not_update

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
        dialog.exec()
        if dialog.uninstall_confirmed:
            try:
                async_manager = AsyncPluginManager(self.plugin_manager)
                async_manager.uninstall_plugin(
                    self.current_plugin,
                    purge=dialog.purge_config,
                    callback=partial(self._on_uninstall_complete, self.current_plugin),
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

        async_manager = AsyncPluginManager(self.plugin_manager)
        async_manager.update_plugin(
            plugin=self.current_plugin,
            progress_callback=None,
            callback=partial(self._on_update_complete, self.current_plugin),
        )

    def _on_update_complete(self, plugin, result):
        """Handle update completion."""
        self.update_button.setText(_("Update"))

        if result.success:
            self.plugin_updated.emit()  # Signal that plugin was updated
            # Emit the same signal as context menu for status updates
            if hasattr(self.parent(), 'plugin_state_changed'):
                self.parent().plugin_state_changed.emit(plugin, "updated")
            # Refresh the display - plugin should no longer have update available
            self.show_plugin(plugin, False)
        else:
            self.update_button.setEnabled(True)
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Update Failed"), error_msg)
