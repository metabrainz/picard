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

from picard.i18n import gettext as _


try:
    from markdown import markdown as render_markdown
except ImportError:
    render_markdown = None


class PluginInfoDialog(QtWidgets.QDialog):
    """Dialog showing detailed plugin information for both registry and installed plugins."""

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
        name = self._get_plugin_name()
        title_label = QtWidgets.QLabel(f"<h2>{name}</h2>")
        layout.addWidget(title_label)

        # Details in a form layout
        details_widget = QtWidgets.QWidget()
        details_layout = QtWidgets.QFormLayout(details_widget)

        # Add fields based on available data
        self._add_field(details_layout, _("ID:"), self._get_plugin_id())
        self._add_field(details_layout, _("UUID:"), self._get_plugin_uuid())
        self._add_field(details_layout, _("Version:"), self._get_plugin_version())
        self._add_field(details_layout, _("API Version:"), self._get_api_version())
        self._add_field(details_layout, _("Trust Level:"), self._get_trust_level())
        self._add_field(details_layout, _("Categories:"), self._get_categories())
        self._add_field(details_layout, _("Authors:"), self._get_authors())
        self._add_field(details_layout, _("Maintainers:"), self._get_maintainers())
        self._add_field(details_layout, _("Repository:"), self._get_repository())
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
            layout.addRow(label, QtWidgets.QLabel(value))

    def _is_registry_plugin(self):
        """Check if this is registry plugin data (dict) vs installed plugin (object)."""
        return isinstance(self.plugin_data, dict)

    def _get_plugin_name(self):
        """Get plugin name."""
        if self._is_registry_plugin():
            return self.plugin_data.get('name', self.plugin_data.get('id', ''))
        else:
            try:
                return self.plugin_data.manifest.name()
            except (AttributeError, Exception):
                return self.plugin_data.name or self.plugin_data.plugin_id

    def _get_plugin_id(self):
        """Get plugin ID."""
        if self._is_registry_plugin():
            return self.plugin_data.get('id', '')
        else:
            return self.plugin_data.plugin_id

    def _get_plugin_uuid(self):
        """Get plugin UUID."""
        if self._is_registry_plugin():
            return self.plugin_data.get('uuid', '')
        else:
            try:
                return self.plugin_data.manifest.uuid()
            except (AttributeError, Exception):
                return ''

    def _get_plugin_version(self):
        """Get plugin version."""
        if self._is_registry_plugin():
            return ''  # Registry doesn't have version info
        else:
            try:
                return self.plugin_data.manifest.version()
            except (AttributeError, Exception):
                return ''

    def _get_api_version(self):
        """Get API version."""
        if self._is_registry_plugin():
            return ''  # Could be extracted from refs but complex
        else:
            try:
                return self.plugin_data.manifest.api_version()
            except (AttributeError, Exception):
                return ''

    def _get_trust_level(self):
        """Get trust level."""
        if self._is_registry_plugin():
            trust_level = self.plugin_data.get('trust_level', 'community')
            return trust_level.title()
        else:
            return ''

    def _get_categories(self):
        """Get categories."""
        if self._is_registry_plugin():
            categories = self.plugin_data.get('categories', [])
            return ', '.join(categories)
        else:
            return ''

    def _get_authors(self):
        """Get authors."""
        if self._is_registry_plugin():
            authors = self.plugin_data.get('authors', [])
            return ', '.join(authors)
        else:
            try:
                authors = self.plugin_data.manifest.authors()
                return ', '.join(authors) if authors else ''
            except (AttributeError, Exception):
                return ''

    def _get_maintainers(self):
        """Get maintainers."""
        if self._is_registry_plugin():
            maintainers = self.plugin_data.get('maintainers', [])
            return ', '.join(maintainers)
        else:
            return ''

    def _get_repository(self):
        """Get repository URL."""
        if self._is_registry_plugin():
            return self.plugin_data.get('git_url', '')
        else:
            return ''

    def _get_versioning_scheme(self):
        """Get versioning scheme."""
        if self._is_registry_plugin():
            return self.plugin_data.get('versioning_scheme', '')
        else:
            return ''

    def _get_description(self):
        """Get plugin description."""
        if self._is_registry_plugin():
            return self.plugin_data.get('description', '')
        else:
            try:
                return self.plugin_data.manifest.long_description() or self.plugin_data.manifest.description()
            except (AttributeError, Exception):
                return ''
