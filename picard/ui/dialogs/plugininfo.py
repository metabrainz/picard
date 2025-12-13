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
from picard.plugin3.registry import RegistryPlugin


try:
    from markdown import markdown as render_markdown
except ImportError:
    render_markdown = None


class PluginInfoDialog(QtWidgets.QDialog):
    """Dialog showing detailed plugin information for both registry and installed plugins."""

    def __init__(self, plugin_data, parent=None):
        super().__init__(parent)
        self._plugin_data = plugin_data

        # Cache plugin manager for performance
        tagger = QtCore.QCoreApplication.instance()
        self.plugin_manager = tagger.get_plugin_manager()

        self.setWindowTitle(_("Plugin Information"))
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()

    @property
    def plugin_data(self):
        """Get plugin data."""
        return self._plugin_data

    @plugin_data.setter
    def plugin_data(self, value):
        """Set plugin data and clear cached registry plugin."""
        self._plugin_data = value
        if hasattr(self, '_registry_plugin'):
            delattr(self, '_registry_plugin')

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Plugin name as title
        name = self._get_plugin_name()
        title_label = QtWidgets.QLabel(f"<h2>{name}</h2>")
        title_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(title_label)

        # Details in a form layout
        details_widget = QtWidgets.QWidget()
        details_layout = QtWidgets.QFormLayout(details_widget)

        # Add fields based on available data
        self._add_field(details_layout, _("ID:"), self._get_plugin_id())
        self._add_field(details_layout, _("UUID:"), self._get_plugin_uuid())
        self._add_field(details_layout, _("Registry ID:"), self._get_registry_id())
        self._add_field(details_layout, _("Status:"), self._get_status())
        self._add_field(details_layout, _("State:"), self._get_state())
        self._add_field(details_layout, _("Version:"), self._get_plugin_version())
        self._add_field(details_layout, _("API Version:"), self._get_api_version())
        self._add_field(details_layout, _("Trust Level:"), self._get_trust_level())
        self._add_field(details_layout, _("Categories:"), self._get_categories())
        self._add_field(details_layout, _("Authors:"), self._get_authors())
        self._add_field(details_layout, _("Maintainers:"), self._get_maintainers())
        self._add_field(details_layout, _("Repository:"), self._get_repository())
        self._add_field(details_layout, _("License:"), self._get_license())
        self._add_field(details_layout, _("License URL:"), self._get_license_url())
        self._add_field(details_layout, _("Homepage:"), self._get_homepage())
        self._add_field(details_layout, _("Path:"), self._get_path())
        self._add_field(details_layout, _("Versioning:"), self._get_versioning_scheme())

        layout.addWidget(details_widget)

        # Description
        description = self._get_description()
        if description:
            desc_label = QtWidgets.QLabel(_("Description:"))
            layout.addWidget(desc_label)

            desc_text = QtWidgets.QTextBrowser()
            desc_text.setMaximumHeight(200)

            if render_markdown and self._is_registry_plugin():
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

    def _add_field(self, layout, label, value):
        """Add field to layout if value exists."""
        if value:
            value_label = QtWidgets.QLabel()
            value_label.setWordWrap(True)
            value_label.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding
            )

            # Check if value is a URL and make it clickable
            if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
                value_label.setText(f'<a href="{value}">{value}</a>')
                value_label.setTextInteractionFlags(
                    QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
                    | QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
                )
                value_label.setOpenExternalLinks(True)
            else:
                value_label.setText(str(value))
                value_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addRow(label, value_label)

    def _is_registry_plugin(self):
        """Check if this is registry plugin data (dict) vs installed plugin (object)."""
        return isinstance(self.plugin_data, dict)

    @property
    def registry_plugin(self):
        """Get RegistryPlugin wrapper for registry plugin data."""
        if not hasattr(self, '_registry_plugin'):
            self._registry_plugin = RegistryPlugin(self.plugin_data) if self._is_registry_plugin() else None
        return self._registry_plugin

    def _get_plugin_name(self):
        """Get plugin name."""
        if self._is_registry_plugin():
            return self.registry_plugin.name_i18n() or self.registry_plugin.id
        else:
            try:
                return self.plugin_data.manifest.name_i18n()
            except (AttributeError, Exception):
                return self.plugin_data.name or self.plugin_data.plugin_id

    def _get_plugin_id(self):
        """Get plugin ID."""
        if self._is_registry_plugin():
            return self.registry_plugin.id
        else:
            return self.plugin_data.plugin_id

    def _get_plugin_uuid(self):
        """Get plugin UUID."""
        if self._is_registry_plugin():
            return self.registry_plugin.uuid or ''
        else:
            try:
                return self.plugin_data.manifest.uuid if self.plugin_data.manifest else ''
            except (AttributeError, Exception):
                return ''

    def _get_plugin_version(self):
        """Get plugin version."""
        if self._is_registry_plugin():
            return ''  # Registry doesn't have version info
        else:
            try:
                return self.plugin_data.manifest._data.get('version', '') if self.plugin_data.manifest else ''
            except (AttributeError, Exception):
                return ''

    def _get_api_version(self):
        """Get API version."""
        if self._is_registry_plugin():
            return ''  # Could be extracted from refs but complex
        else:
            try:
                api_versions = self.plugin_data.manifest._data.get('api', []) if self.plugin_data.manifest else []
                return ', '.join(api_versions)
            except (AttributeError, Exception):
                return ''

    def _get_trust_level(self):
        """Get trust level."""
        if self._is_registry_plugin():
            return self.registry_plugin.trust_level.title()
        else:
            return ''

    def _get_categories(self):
        """Get categories."""
        if self._is_registry_plugin():
            return ', '.join(self.registry_plugin.categories)
        else:
            try:
                categories = self.plugin_data.manifest._data.get('categories', []) if self.plugin_data.manifest else []
                return ', '.join(categories)
            except (AttributeError, Exception):
                return ''

    def _get_authors(self):
        """Get authors."""
        if self._is_registry_plugin():
            authors = self.registry_plugin.get('authors', [])
            return ', '.join(authors)
        else:
            try:
                authors = self.plugin_data.manifest.authors if self.plugin_data.manifest else []
                return ', '.join(authors) if authors else ''
            except (AttributeError, Exception):
                return ''

    def _get_maintainers(self):
        """Get maintainers."""
        if self._is_registry_plugin():
            maintainers = self.registry_plugin.get('maintainers', [])
            return ', '.join(maintainers)
        else:
            try:
                maintainers = self.plugin_data.manifest.maintainers if self.plugin_data.manifest else []
                return ', '.join(maintainers) if maintainers else ''
            except (AttributeError, Exception):
                return ''

    def _get_repository(self):
        """Get repository URL."""
        if self._is_registry_plugin():
            return self.registry_plugin.git_url or ''
        else:
            # For installed plugins, get from manager
            try:
                if self.plugin_manager:
                    return self.plugin_manager.get_plugin_remote_url(self.plugin_data) or ''
                return ''
            except (AttributeError, Exception):
                return ''

    def _get_versioning_scheme(self):
        """Get versioning scheme."""
        if self._is_registry_plugin():
            return self.registry_plugin.get('versioning_scheme', '')
        else:
            # For installed plugins, get versioning scheme from manager
            try:
                if self.plugin_manager:
                    return self.plugin_manager.get_plugin_versioning_scheme(self.plugin_data)
                return ''
            except (AttributeError, Exception):
                return ''

    def _get_registry_id(self):
        """Get registry ID."""
        if self._is_registry_plugin():
            return self.registry_plugin.id
        else:
            return getattr(self.plugin_data, 'registry_id', '')

    def _get_status(self):
        """Get plugin status (enabled/disabled)."""
        if self._is_registry_plugin():
            return ''
        else:
            return _("enabled") if self.plugin_data.enable else _("disabled")

    def _get_state(self):
        """Get plugin state."""
        if self._is_registry_plugin():
            return ''
        else:
            return (
                getattr(self.plugin_data, 'state', '').name
                if hasattr(getattr(self.plugin_data, 'state', ''), 'name')
                else str(getattr(self.plugin_data, 'state', ''))
            )

    def _get_license(self):
        """Get license."""
        if self._is_registry_plugin():
            return self.registry_plugin.get('license', '')
        else:
            try:
                return self.plugin_data.manifest.license if self.plugin_data.manifest else ''
            except (AttributeError, Exception):
                return ''

    def _get_license_url(self):
        """Get license URL."""
        if self._is_registry_plugin():
            return self.registry_plugin.get('license_url', '')
        else:
            try:
                return self.plugin_data.manifest.license_url if self.plugin_data.manifest else ''
            except (AttributeError, Exception):
                return ''

    def _get_homepage(self):
        """Get homepage URL."""
        if self._is_registry_plugin():
            return self.registry_plugin.get('homepage', '')
        else:
            try:
                return self.plugin_data.manifest._data.get('homepage', '') if self.plugin_data.manifest else ''
            except (AttributeError, Exception):
                return ''

    def _get_path(self):
        """Get plugin path."""
        if self._is_registry_plugin():
            return ''
        else:
            path = getattr(self.plugin_data, 'local_path', '')
            return str(path) if path else ''

    def _get_description(self):
        """Get plugin description."""
        if self._is_registry_plugin():
            return self.registry_plugin.description_i18n()
        else:
            try:
                if self.plugin_data.manifest:
                    # Try long description first, then short description
                    long_desc = self.plugin_data.manifest.long_description_i18n()
                    if long_desc:
                        return long_desc
                    return self.plugin_data.manifest.description_i18n()
                return ''
            except (AttributeError, Exception):
                return ''
