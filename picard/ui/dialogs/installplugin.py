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

import os

from PyQt6 import QtCore, QtWidgets

from picard import log
from picard.i18n import gettext as _
from picard.plugin3.asyncops.manager import AsyncPluginManager
from picard.plugin3.installable import (
    LocalInstallablePlugin,
    RegistryInstallablePlugin,
    UrlInstallablePlugin,
)
from picard.plugin3.registry import RegistryPlugin

from picard.ui import PicardDialog
from picard.ui.dialogs.installconfirm import InstallConfirmDialog
from picard.ui.dialogs.plugininfo import PluginInfoDialog


try:
    from markdown import markdown as render_markdown
except ImportError:
    render_markdown = None


# Tab positions
TAB_REGISTRY = 0
TAB_URL = 1
TAB_LOCAL = 2


class InstallPluginDialog(PicardDialog):
    """Dialog for installing plugins."""

    defaultsize = QtCore.QSize(500, 300)
    plugin_installed = QtCore.pyqtSignal(str)  # Emits plugin_id when installed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Install Plugin"))
        self.setModal(True)
        self.setMinimumSize(500, 300)

        # Cache frequently accessed objects
        self.plugin_manager = self.tagger.get_plugin_manager()

        # Fetch registry on dialog open, fallback to cache if network fails
        log.debug('InstallPluginDialog: Fetching registry on dialog open')
        try:
            self.plugin_manager._registry.fetch_registry(use_cache=True)
            log.debug('InstallPluginDialog: Registry fetch completed successfully')
        except Exception as e:
            # Network failed, use cache
            log.debug('InstallPluginDialog: Registry fetch failed: %s', e)

        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Tab widget for different install methods
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)

        # Registry tab
        registry_widget = QtWidgets.QWidget()
        registry_layout = QtWidgets.QVBoxLayout(registry_widget)

        # Search/filter controls
        search_layout = QtWidgets.QHBoxLayout()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setPlaceholderText(_("Search plugins..."))
        self.search_edit.textChanged.connect(self._filter_plugins)
        search_layout.addWidget(self.search_edit)

        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItem(_("All Categories"), "")
        self.category_combo.currentTextChanged.connect(self._filter_plugins)
        search_layout.addWidget(self.category_combo)

        registry_layout.addLayout(search_layout)

        # Plugin table
        self.plugin_table = QtWidgets.QTableWidget()
        self.plugin_table.setColumnCount(3)
        self.plugin_table.setHorizontalHeaderLabels([_("Trust"), _("Name"), _("Categories")])
        self.plugin_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.plugin_table.setAlternatingRowColors(True)
        self.plugin_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.plugin_table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.plugin_table.customContextMenuRequested.connect(self._show_context_menu)
        self.plugin_table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.plugin_table.itemSelectionChanged.connect(self._validate_input)

        # Set column widths
        header = self.plugin_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 60)  # Trust column
        header.resizeSection(1, 250)  # Name column

        registry_layout.addWidget(self.plugin_table)

        self.tab_widget.addTab(registry_widget, _("Registry"))

        # URL tab
        url_widget = QtWidgets.QWidget()
        url_layout = QtWidgets.QVBoxLayout(url_widget)

        url_group = QtWidgets.QGroupBox(_("Install from URL"))
        url_form = QtWidgets.QFormLayout(url_group)

        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText(_("https://github.com/user/plugin"))
        url_form.addRow(_("Git URL:"), self.url_edit)

        self.ref_edit = QtWidgets.QLineEdit()
        self.ref_edit.setPlaceholderText(_("main"))
        url_form.addRow(_("Ref/Tag:"), self.ref_edit)

        url_layout.addWidget(url_group)
        url_layout.addStretch()
        self.tab_widget.addTab(url_widget, _("URL"))

        # Local directory tab
        local_widget = QtWidgets.QWidget()
        local_layout = QtWidgets.QVBoxLayout(local_widget)

        local_group = QtWidgets.QGroupBox(_("Install from Local Directory"))
        local_form = QtWidgets.QFormLayout(local_group)

        # Directory path with browse button
        path_layout = QtWidgets.QHBoxLayout()
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setPlaceholderText(_("/path/to/plugin/directory"))
        path_layout.addWidget(self.path_edit)

        browse_button = QtWidgets.QPushButton(_("Browse..."))
        browse_button.clicked.connect(self._browse_directory)
        path_layout.addWidget(browse_button)

        local_form.addRow(_("Directory:"), path_layout)

        self.local_ref_edit = QtWidgets.QLineEdit()
        self.local_ref_edit.setPlaceholderText(_("main"))
        local_form.addRow(_("Ref/Tag:"), self.local_ref_edit)

        local_layout.addWidget(local_group)
        local_layout.addStretch()
        self.tab_widget.addTab(local_widget, _("Local"))

        # Warning label
        self.warning_label = QtWidgets.QLabel()
        self.warning_label.setStyleSheet("color: orange; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QtWidgets.QLabel()
        layout.addWidget(self.status_label)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox()
        self.install_button = QtWidgets.QPushButton(_("Install"))
        button_box.addButton(self.install_button, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._install_plugin)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Connect input changes to validation
        self.url_edit.textChanged.connect(self._validate_input)
        self.path_edit.textChanged.connect(self._validate_input)
        self.local_ref_edit.textChanged.connect(self._validate_input)
        self.tab_widget.currentChanged.connect(self._validate_input)
        self._load_registry_plugins()
        self._validate_input()

    def _validate_input(self):
        """Validate input and update UI."""
        current_tab = self.tab_widget.currentIndex()

        if current_tab == TAB_REGISTRY:  # Registry tab
            selected = self.plugin_table.currentRow() >= 0
            self.install_button.setEnabled(selected)
        elif current_tab == TAB_URL:  # URL tab
            url = self.url_edit.text().strip()
            self.install_button.setEnabled(bool(url))
            if url:
                self._check_trust_level(url)
        else:  # TAB_LOCAL - Local directory tab
            path = self.path_edit.text().strip()
            self.install_button.setEnabled(bool(path))

    def _load_registry_plugins(self):
        """Load plugins from registry."""
        try:
            registry = self.plugin_manager._registry
            plugins = registry.list_plugins()

            # Populate categories
            categories = set()
            for plugin in plugins:
                categories.update(plugin.get('categories', []))

            for category in sorted(categories):
                self.category_combo.addItem(category.title(), category)

            self._all_plugins = plugins
            self._filter_plugins()
        except Exception:
            pass

    def _filter_plugins(self):
        """Filter plugins based on search and category."""
        if not hasattr(self, '_all_plugins'):
            return

        search_text = self.search_edit.text().lower()
        category = self.category_combo.currentData()

        # Get installed plugin UUIDs
        installed_uuids = self._get_installed_plugin_uuids()

        self.plugin_table.setRowCount(0)

        trust_badges = {
            'official': '🛡️',
            'trusted': '✓',
            'community': '⚠️',
            'unregistered': '🔓',
        }

        trust_tooltips = {
            'official': _("Official plugin - reviewed by Picard team"),
            'trusted': _("Trusted plugin - from known developers"),
            'community': _("Community plugin - not reviewed"),
            'unregistered': _("Unregistered plugin - not in official registry"),
        }

        for plugin in self._all_plugins:
            # Create registry plugin wrapper for i18n support
            registry_plugin = RegistryPlugin(plugin)

            # Skip if already installed
            if registry_plugin.uuid and registry_plugin.uuid in installed_uuids:
                continue

            # Category filter
            if category and category not in registry_plugin.categories:
                continue

            # Search filter
            if search_text:
                searchable = f"{registry_plugin.name_i18n()} {registry_plugin.description_i18n()} {' '.join(registry_plugin.categories)}".lower()
                if search_text not in searchable:
                    continue

            row = self.plugin_table.rowCount()
            self.plugin_table.insertRow(row)

            # Trust level column
            trust_item = QtWidgets.QTableWidgetItem(trust_badges.get(registry_plugin.trust_level, '?'))
            trust_item.setToolTip(trust_tooltips.get(registry_plugin.trust_level, registry_plugin.trust_level))
            trust_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            trust_item.setData(QtCore.Qt.ItemDataRole.UserRole, plugin)
            self.plugin_table.setItem(row, 0, trust_item)

            # Name column
            registry_plugin = RegistryPlugin(plugin)
            name_item = QtWidgets.QTableWidgetItem(registry_plugin.name_i18n() or registry_plugin.id)
            desc = registry_plugin.description_i18n()

            # Build tooltip with description and click hint
            tooltip_parts = []
            if desc:
                if render_markdown:
                    html_desc = render_markdown(desc, output_format='html')
                    tooltip_parts.append(html_desc)
                else:
                    tooltip_parts.append(desc)

            tooltip_parts.append(_("Double-click to view detailed plugin information"))
            name_item.setToolTip('\n\n'.join(tooltip_parts))

            self.plugin_table.setItem(row, 1, name_item)

            # Categories column
            cat_item = QtWidgets.QTableWidgetItem(', '.join(registry_plugin.categories))
            self.plugin_table.setItem(row, 2, cat_item)

    def _get_installed_plugin_uuids(self):
        """Get set of installed plugin UUIDs."""
        installed_uuids = set()
        try:
            for plugin in self.plugin_manager.plugins:
                try:
                    uuid = plugin.uuid
                    if uuid:
                        installed_uuids.add(uuid)
                except (AttributeError, Exception):
                    pass
        except Exception:
            pass
        return installed_uuids

    def showEvent(self, event):
        """Refresh plugin filtering when dialog is shown."""
        super().showEvent(event)
        if hasattr(self, '_all_plugins'):
            self._filter_plugins()

    def _install_selected_plugin(self):
        """Install the selected plugin from registry."""
        if self.plugin_table.currentRow() >= 0:
            self._install_plugin()

    def _on_item_double_clicked(self, item):
        """Handle item double-click - show plugin info if name column, install otherwise."""
        if item and item.column() == 1:  # Name column
            self._show_plugin_info()
        else:
            # Double-click on other columns installs the plugin
            self._install_selected_plugin()

    def _show_context_menu(self, position):
        """Show context menu for plugin table."""
        if self.plugin_table.itemAt(position):
            menu = QtWidgets.QMenu(self)
            info_action = menu.addAction(_("Info"))
            info_action.triggered.connect(self._show_plugin_info)
            menu.exec(self.plugin_table.mapToGlobal(position))

    def _show_plugin_info(self):
        """Show detailed plugin information dialog."""
        current_row = self.plugin_table.currentRow()
        if current_row < 0:
            return

        trust_item = self.plugin_table.item(current_row, 0)
        plugin_data = trust_item.data(QtCore.Qt.ItemDataRole.UserRole)

        dialog = PluginInfoDialog(plugin_data, self)
        dialog.exec()

    def _browse_directory(self):
        """Open directory browser for local plugin selection."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            _("Select Plugin Directory"),
            "",
            QtWidgets.QFileDialog.Option.ShowDirsOnly | QtWidgets.QFileDialog.Option.DontResolveSymlinks,
        )
        if directory:
            self.path_edit.setText(directory)

    def _check_registry_plugin(self, plugin_id):
        """Check registry plugin and show info if needed."""
        try:
            registry = self.plugin_manager._registry
            # Try to find plugin in registry
            plugin_data = registry.find_plugin(plugin_id=plugin_id)
            if plugin_data:
                trust_level = registry.get_trust_level(plugin_data.get('url', ''))
                if trust_level in ("community", "unregistered"):
                    self._show_trust_warning(trust_level)
                else:
                    self.warning_label.hide()
            else:
                self.warning_label.setText(_("Plugin not found in registry"))
                self.warning_label.show()
        except Exception:
            self.warning_label.hide()

    def _show_trust_warning(self, trust_level):
        """Show trust level warning."""
        if trust_level == "community":
            self.warning_label.setText(
                _(
                    "Warning: This is a community plugin. "
                    "Community plugins are not reviewed by the Picard team. "
                    "Only install plugins from sources you trust."
                )
            )
            self.warning_label.show()
        elif trust_level == "unregistered":
            self.warning_label.setText(
                _(
                    "Warning: This plugin is not in the official registry. "
                    "Installing unregistered plugins may pose security risks. "
                    "Only install plugins from sources you trust."
                )
            )
            self.warning_label.show()
        else:
            self.warning_label.hide()

    def _check_trust_level(self, url):
        """Check trust level and show warning if needed."""
        if not self.plugin_manager:
            return

        try:
            registry = self.plugin_manager._registry
            trust_level = registry.get_trust_level(url)
            self._show_trust_warning(trust_level)
        except Exception:
            self.warning_label.hide()

    def _create_registry_plugin(self):
        """Create RegistryInstallablePlugin from selected registry plugin."""
        current_row = self.plugin_table.currentRow()
        if current_row < 0:
            return None

        trust_item = self.plugin_table.item(current_row, 0)
        plugin_data = trust_item.data(QtCore.Qt.ItemDataRole.UserRole)
        registry_plugin = RegistryPlugin(plugin_data)
        return RegistryInstallablePlugin(registry_plugin, self.plugin_manager._registry)

    def _create_url_plugin(self):
        """Create UrlInstallablePlugin from URL input."""
        url = self.url_edit.text().strip()
        ref = self.ref_edit.text().strip() or None
        if not url:
            return None
        return UrlInstallablePlugin(url, ref, self.plugin_manager._registry)

    def _create_local_plugin(self):
        """Create LocalInstallablePlugin from local path input."""
        url = self.path_edit.text().strip()
        ref = self.local_ref_edit.text().strip() or None
        if not url:
            QtWidgets.QMessageBox.warning(
                self, _("No Directory Selected"), _("Please select a local plugin directory.")
            )
            return None

        # Validate directory
        if not os.path.isdir(url):
            QtWidgets.QMessageBox.critical(self, _("Invalid Directory"), _("The selected path is not a directory."))
            return None

        # Check for MANIFEST.toml
        manifest_path = os.path.join(url, "MANIFEST.toml")
        if not os.path.isfile(manifest_path):
            QtWidgets.QMessageBox.critical(
                self,
                _("Invalid Plugin Directory"),
                _(
                    "The selected directory does not contain a MANIFEST.toml file. A valid plugin requires both a git repository and a MANIFEST.toml file."
                ),
            )
            return None

        return LocalInstallablePlugin(url, ref, self.plugin_manager._registry)

    def _disable_ui_for_installation(self):
        """Disable UI elements during installation."""
        for widget in self.findChildren(QtWidgets.QWidget):
            if widget != self.progress_bar and widget != self.status_label:
                widget.setEnabled(False)

    def _enable_ui_after_installation(self):
        """Re-enable UI elements after installation."""
        for widget in self.findChildren(QtWidgets.QWidget):
            widget.setEnabled(True)
        self._validate_input()  # Restore proper button states

    def _install_plugin(self):
        """Install the plugin."""
        current_tab = self.tab_widget.currentIndex()

        # Create appropriate InstallablePlugin instance
        if current_tab == TAB_REGISTRY:
            plugin = self._create_registry_plugin()
        elif current_tab == TAB_URL:
            plugin = self._create_url_plugin()
        else:  # TAB_LOCAL
            plugin = self._create_local_plugin()

        if not plugin:
            return

        # Validate plugin has install URL
        url = plugin.get_install_url()
        if not url:
            QtWidgets.QMessageBox.critical(self, _("Error"), _("Plugin has no repository URL"))
            return

        # Disable UI before showing confirmation dialog to prevent interaction
        self._disable_ui_for_installation()

        ref = None
        if getattr(plugin, 'ref', None) is None:
            # Show confirmation dialog
            plugin_name = plugin.get_display_name()
            plugin_uuid = plugin.plugin_uuid
            confirm_dialog = InstallConfirmDialog(plugin_name, url, self, plugin_uuid, None)
            if confirm_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
                # Re-enable UI if user cancels
                self._enable_ui_after_installation()
                return
            if confirm_dialog.selected_ref:
                ref = confirm_dialog.selected_ref.shortname

        # Use versioning scheme for registry plugins when no ref specified
        if current_tab == TAB_REGISTRY and ref is None:
            # Get original plugin data for versioning scheme
            current_row = self.plugin_table.currentRow()
            trust_item = self.plugin_table.item(current_row, 0)
            plugin_data = trust_item.data(QtCore.Qt.ItemDataRole.UserRole)
            ref = self.plugin_manager.select_ref_for_plugin(plugin_data)
        elif hasattr(plugin, 'ref') and ref is None:
            ref = plugin.ref

        # Show progress bar
        self.progress_bar.show()
        self.progress_bar.setValue(0)

        # Start async installation
        async_manager = AsyncPluginManager(self.plugin_manager)
        async_manager.install_plugin(url=url, ref=ref, progress_callback=self._on_progress, callback=self._on_complete)

    def _on_progress(self, update):
        """Handle installation progress."""
        self.progress_bar.setValue(update.percent)
        self.status_label.setText(update.message)

    def _on_complete(self, result):
        """Handle installation completion."""
        self.progress_bar.hide()

        if result.success:
            self.status_label.setText(_("Plugin installed successfully"))
            self.plugin_installed.emit(result.result)
            # No need to re-enable UI, we're closing the dialog
            QtCore.QTimer.singleShot(1000, self.accept)  # Close after 1 second
        else:
            self.status_label.setText(_("Installation failed"))
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Installation Failed"), error_msg)
            # Re-enable UI
            self._enable_ui_after_installation()
