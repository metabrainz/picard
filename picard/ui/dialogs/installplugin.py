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


try:
    from markdown import markdown as render_markdown
except ImportError:
    render_markdown = None


# Tab positions
TAB_REGISTRY = 0
TAB_URL = 1


class InstallPluginDialog(QtWidgets.QDialog):
    """Dialog for installing plugins."""

    plugin_installed = QtCore.pyqtSignal(str)  # Emits plugin_id when installed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Install Plugin"))
        self.setModal(True)
        self.resize(500, 300)
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
        self.plugin_table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.plugin_table.customContextMenuRequested.connect(self._show_context_menu)
        self.plugin_table.itemDoubleClicked.connect(self._install_selected_plugin)
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

        layout.addStretch()

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.install_button = QtWidgets.QPushButton(_("Install"))
        self.install_button.clicked.connect(self._install_plugin)
        self.install_button.setDefault(True)
        button_layout.addWidget(self.install_button)

        self.cancel_button = QtWidgets.QPushButton(_("Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Connect input changes to validation
        self.url_edit.textChanged.connect(self._validate_input)
        self.tab_widget.currentChanged.connect(self._validate_input)
        self._load_registry_plugins()
        self._validate_input()

    def _validate_input(self):
        """Validate input and update UI."""
        current_tab = self.tab_widget.currentIndex()

        if current_tab == TAB_REGISTRY:  # Registry tab
            selected = self.plugin_table.currentRow() >= 0
            self.install_button.setEnabled(selected)
        else:  # URL tab
            url = self.url_edit.text().strip()
            self.install_button.setEnabled(bool(url))
            if url:
                self._check_trust_level(url)

    def _load_registry_plugins(self):
        """Load plugins from registry."""
        tagger = QtWidgets.QApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            return

        try:
            registry = tagger.pluginmanager3._registry
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
            # Category filter
            if category and category not in plugin.get('categories', []):
                continue

            # Search filter
            if search_text:
                searchable = f"{plugin.get('name', '')} {plugin.get('description', '')} {' '.join(plugin.get('categories', []))}".lower()
                if search_text not in searchable:
                    continue

            row = self.plugin_table.rowCount()
            self.plugin_table.insertRow(row)

            # Trust level column
            trust_level = plugin.get('trust_level', 'community')
            trust_item = QtWidgets.QTableWidgetItem(trust_badges.get(trust_level, '?'))
            trust_item.setToolTip(trust_tooltips.get(trust_level, trust_level))
            trust_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            trust_item.setData(QtCore.Qt.ItemDataRole.UserRole, plugin)
            self.plugin_table.setItem(row, 0, trust_item)

            # Name column
            name_item = QtWidgets.QTableWidgetItem(plugin.get('name', plugin.get('id', '')))
            desc = plugin.get('description', '')
            if desc and render_markdown:
                html_desc = render_markdown(desc, output_format='html')
                name_item.setToolTip(html_desc)
            elif desc:
                name_item.setToolTip(desc)
            self.plugin_table.setItem(row, 1, name_item)

            # Categories column
            categories = plugin.get('categories', [])
            cat_item = QtWidgets.QTableWidgetItem(', '.join(categories))
            self.plugin_table.setItem(row, 2, cat_item)

    def _install_selected_plugin(self):
        """Install the selected plugin from registry."""
        if self.plugin_table.currentRow() >= 0:
            self._install_plugin()

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

    def _check_registry_plugin(self, plugin_id):
        """Check registry plugin and show info if needed."""
        """Check registry plugin and show info if needed."""
        tagger = QtWidgets.QApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            return

        try:
            registry = tagger.pluginmanager3._registry
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
        tagger = QtWidgets.QApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            return

        try:
            registry = tagger.pluginmanager3._registry
            trust_level = registry.get_trust_level(url)
            self._show_trust_warning(trust_level)
        except Exception:
            self.warning_label.hide()

    def _install_plugin(self):
        """Install the plugin."""
        current_tab = self.tab_widget.currentIndex()

        # Get plugin manager
        tagger = QtWidgets.QApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            QtWidgets.QMessageBox.critical(self, _("Error"), _("Plugin system not available"))
            return

        if current_tab == TAB_REGISTRY:  # Registry tab
            current_row = self.plugin_table.currentRow()
            if current_row < 0:
                return

            trust_item = self.plugin_table.item(current_row, 0)
            plugin_data = trust_item.data(QtCore.Qt.ItemDataRole.UserRole)
            url = plugin_data.get('git_url')
            ref = None  # Use default ref

            if not url:
                QtWidgets.QMessageBox.critical(self, _("Error"), _("Plugin has no repository URL"))
                return
        else:  # URL tab
            url = self.url_edit.text().strip()
            ref = self.ref_edit.text().strip() or None
            if not url:
                return

        # Disable UI during installation
        self.install_button.setEnabled(False)
        self.plugin_table.setEnabled(False)
        self.search_edit.setEnabled(False)
        self.category_combo.setEnabled(False)
        self.url_edit.setEnabled(False)
        self.ref_edit.setEnabled(False)
        self.tab_widget.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)

        # Start async installation
        async_manager = AsyncPluginManager(tagger.pluginmanager3)
        async_manager.install_plugin(url=url, ref=ref, progress_callback=self._on_progress, callback=self._on_complete)

    def _on_progress(self, update):
        """Handle installation progress."""
        self.progress_bar.setValue(update.percent)
        self.status_label.setText(update.message)

    def _on_complete(self, result):
        """Handle installation completion."""
        # Re-enable UI
        self.install_button.setEnabled(True)
        self.plugin_table.setEnabled(True)
        self.search_edit.setEnabled(True)
        self.category_combo.setEnabled(True)
        self.url_edit.setEnabled(True)
        self.ref_edit.setEnabled(True)
        self.tab_widget.setEnabled(True)
        self.progress_bar.hide()

        if result.success:
            self.status_label.setText(_("Plugin installed successfully"))
            self.plugin_installed.emit(result.result)
            QtWidgets.QTimer.singleShot(1000, self.accept)  # Close after 1 second
        else:
            self.status_label.setText(_("Installation failed"))
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Installation Failed"), error_msg)


class PluginInfoDialog(QtWidgets.QDialog):
    """Dialog showing detailed plugin information."""

    def __init__(self, plugin_data, parent=None):
        super().__init__(parent)
        self.plugin_data = plugin_data
        self.setWindowTitle(_("Plugin Information"))
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Plugin name as title
        name = self.plugin_data.get('name', self.plugin_data.get('id', ''))
        title_label = QtWidgets.QLabel(f"<h2>{name}</h2>")
        layout.addWidget(title_label)

        # Details in a form layout
        details_widget = QtWidgets.QWidget()
        details_layout = QtWidgets.QFormLayout(details_widget)

        # Basic info
        details_layout.addRow(_("ID:"), QtWidgets.QLabel(self.plugin_data.get('id', '')))
        details_layout.addRow(_("UUID:"), QtWidgets.QLabel(self.plugin_data.get('uuid', '')))

        trust_level = self.plugin_data.get('trust_level', 'community')
        details_layout.addRow(_("Trust Level:"), QtWidgets.QLabel(trust_level.title()))

        categories = ', '.join(self.plugin_data.get('categories', []))
        details_layout.addRow(_("Categories:"), QtWidgets.QLabel(categories))

        authors = ', '.join(self.plugin_data.get('authors', []))
        if authors:
            details_layout.addRow(_("Authors:"), QtWidgets.QLabel(authors))

        maintainers = ', '.join(self.plugin_data.get('maintainers', []))
        if maintainers:
            details_layout.addRow(_("Maintainers:"), QtWidgets.QLabel(maintainers))

        git_url = self.plugin_data.get('git_url', '')
        if git_url:
            details_layout.addRow(_("Repository:"), QtWidgets.QLabel(git_url))

        versioning_scheme = self.plugin_data.get('versioning_scheme', '')
        if versioning_scheme:
            details_layout.addRow(_("Versioning:"), QtWidgets.QLabel(versioning_scheme))

        layout.addWidget(details_widget)

        # Description
        desc_label = QtWidgets.QLabel(_("Description:"))
        layout.addWidget(desc_label)

        desc_text = QtWidgets.QTextBrowser()
        desc_text.setMaximumHeight(200)

        description = self.plugin_data.get('description', '')
        if description and render_markdown:
            html_desc = render_markdown(description, output_format='html')
            desc_text.setHtml(html_desc)
        else:
            desc_text.setPlainText(description)

        layout.addWidget(desc_text)

        # Close button
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        close_button = QtWidgets.QPushButton(_("Close"))
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)
