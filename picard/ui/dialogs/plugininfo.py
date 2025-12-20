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

from picard.ui import PreserveGeometry


class PluginInfoDialog(QtWidgets.QDialog, PreserveGeometry):
    """Dialog showing detailed plugin information for both registry and installed plugins."""

    defaultsize = QtCore.QSize(600, 500)

    def __init__(self, plugin_data, parent=None):
        super().__init__(parent)
        self._plugin_data = plugin_data

        # Cache plugin manager for performance
        tagger = QtCore.QCoreApplication.instance()
        self.plugin_manager = tagger.get_plugin_manager()

        self.setWindowTitle(_("Plugin Information"))
        self.setModal(True)
        self.setMinimumSize(500, 300)
        self.setup_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.restore_geometry()

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

        # Short description under title
        short_desc = self._get_short_description()
        if short_desc:
            desc_label = QtWidgets.QLabel(f"<i>{short_desc}</i>")
            desc_label.setWordWrap(True)
            desc_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(desc_label)

        # Create scroll area for the rest of the content
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Content widget for scroll area
        content_widget = QtWidgets.QWidget()
        content_widget.setMinimumHeight(100)
        content_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        content_layout = QtWidgets.QVBoxLayout(content_widget)

        # Details in a form layout
        details_widget = QtWidgets.QWidget()
        details_widget.setMinimumHeight(100)
        details_layout = QtWidgets.QFormLayout(details_widget)

        # Add fields based on available data
        self._add_field(details_layout, _("ID:"), self._get_plugin_id())
        self._add_field(details_layout, _("UUID:"), self._get_plugin_uuid())
        self._add_field(details_layout, _("Registry ID:"), self._get_registry_id())
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

        content_layout.addWidget(details_widget)

        # Description
        description = self._get_description()
        if description:
            desc_label = QtWidgets.QLabel(_("Description:"))
            font = desc_label.font()
            font.setBold(True)
            desc_label.setFont(font)
            content_layout.addWidget(desc_label)

            desc_text = QtWidgets.QLabel()
            desc_text.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
            desc_text.setText(description.rstrip())
            desc_text.setMinimumHeight(50)
            desc_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            desc_text.setOpenExternalLinks(True)
            desc_text.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding
            )
            content_layout.addWidget(desc_text)

        # Set content widget to scroll area and add to main layout
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # Close button
        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(QtWidgets.QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)

    @staticmethod
    def _make_label():
        label = QtWidgets.QLabel()
        label.setWordWrap(True)
        label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        return label

    def _add_field(self, layout, name, value):
        """Add field to layout if value exists."""
        if value:
            value_label = self._make_label()

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

            label = self._make_label()
            label.setText(name)
            layout.addRow(label, value_label)

    def _is_installable_plugin(self):
        """Check if this is an InstallablePlugin object vs installed plugin."""
        from picard.plugin3.installable import InstallablePlugin

        return isinstance(self.plugin_data, InstallablePlugin)

    def _get_plugin_name(self):
        """Get plugin name."""
        if self._is_installable_plugin():
            return getattr(self.plugin_data, 'name', '') or getattr(self.plugin_data, 'id', '')
        else:
            try:
                return self.plugin_data.manifest.name_i18n()
            except (AttributeError, Exception):
                return getattr(self.plugin_data, 'name', '')

    def _get_plugin_id(self):
        """Get plugin ID."""
        if self._is_installable_plugin():
            return getattr(self.plugin_data, 'id', getattr(self.plugin_data, 'plugin_uuid', ''))
        else:
            return getattr(self.plugin_data, 'plugin_id', getattr(self.plugin_data, 'plugin_uuid', ''))

    def _get_plugin_uuid(self):
        """Get plugin UUID."""
        return getattr(self.plugin_data, 'uuid', getattr(self.plugin_data, 'plugin_uuid', '')) or ''

    def _get_plugin_version(self):
        """Get plugin version."""
        if self._is_installable_plugin():
            return ''  # InstallablePlugin objects don't have version
        else:
            try:
                return self.plugin_data.manifest._data.get('version', '') if self.plugin_data.manifest else ''
            except (AttributeError, Exception):
                return ''

    def _get_api_version(self):
        """Get API version."""
        if self._is_installable_plugin():
            return ''
        else:
            try:
                api_versions = self.plugin_data.manifest._data.get('api', []) if self.plugin_data.manifest else []
                return ', '.join(api_versions)
            except (AttributeError, Exception):
                return ''

    def _get_trust_level(self):
        """Get trust level."""
        if self._is_installable_plugin():
            trust_level = getattr(self.plugin_data, 'trust_level', '')
            return trust_level.title() if trust_level else ''
        else:
            # For installed plugins, use the plugin manager to get trust level
            try:
                registry = self.plugin_manager._registry
                # Get remote URL from metadata
                remote_url = self._get_plugin_remote_url()
                if remote_url:
                    trust_level = registry.get_trust_level(remote_url)
                    return self._format_trust_level(trust_level)
                # For local plugins without remote_url, show as Local
                return _("Local")
            except Exception:
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

    def _get_plugin_remote_url(self):
        """Get plugin remote URL from metadata."""
        if self._is_installable_plugin():
            return getattr(self.plugin_data, 'git_url', getattr(self.plugin_data, 'source_url', '')) or ''
        else:
            try:
                return self.plugin_manager.get_plugin_remote_url(self.plugin_data) or '' if self.plugin_manager else ''
            except (AttributeError, Exception):
                return ''

    def _get_categories(self):
        """Get categories."""
        if self._is_installable_plugin():
            categories = getattr(self.plugin_data, 'categories', [])
            return ', '.join(categories) if categories else ''
        else:
            try:
                categories = self.plugin_data.manifest._data.get('categories', []) if self.plugin_data.manifest else []
                return ', '.join(categories)
            except (AttributeError, Exception):
                return ''

    def _get_authors(self):
        """Get authors."""
        if self._is_installable_plugin():
            authors = getattr(self.plugin_data, 'authors', [])
            return ', '.join(authors) if authors else ''
        else:
            try:
                authors = self.plugin_data.manifest.authors if self.plugin_data.manifest else []
                return ', '.join(authors) if authors else ''
            except (AttributeError, Exception):
                return ''

    def _get_maintainers(self):
        """Get maintainers."""
        if self._is_installable_plugin():
            maintainers = getattr(self.plugin_data, 'maintainers', [])
            return ', '.join(maintainers) if maintainers else ''
        else:
            try:
                maintainers = self.plugin_data.manifest.maintainers if self.plugin_data.manifest else []
                return ', '.join(maintainers) if maintainers else ''
            except (AttributeError, Exception):
                return ''

    def _get_repository(self):
        """Get repository URL."""
        if self._is_installable_plugin():
            return getattr(self.plugin_data, 'git_url', getattr(self.plugin_data, 'source_url', '')) or ''
        else:
            try:
                return self.plugin_manager.get_plugin_remote_url(self.plugin_data) or '' if self.plugin_manager else ''
            except (AttributeError, Exception):
                return ''

    def _get_versioning_scheme(self):
        """Get versioning scheme."""
        if self._is_installable_plugin():
            return getattr(self.plugin_data, 'versioning_scheme', '') or ''
        else:
            try:
                return self.plugin_manager.get_plugin_versioning_scheme(self.plugin_data) if self.plugin_manager else ''
            except (AttributeError, Exception):
                return ''

    def _get_registry_id(self):
        """Get registry ID."""
        if self._is_installable_plugin():
            return getattr(self.plugin_data, 'id', '') or ''
        else:
            return getattr(self.plugin_data, 'registry_id', '') or ''

    def _get_state(self):
        """Get plugin state."""
        if self._is_installable_plugin():
            return ''
        else:
            state = getattr(self.plugin_data, 'state', '')
            return state.name if hasattr(state, 'name') else str(state) if state else ''

    def _get_license(self):
        """Get license."""
        if self._is_installable_plugin():
            return getattr(self.plugin_data, 'license', '') or ''
        else:
            try:
                return self.plugin_data.manifest.license if self.plugin_data.manifest else ''
            except (AttributeError, Exception):
                return ''

    def _get_license_url(self):
        """Get license URL."""
        if self._is_installable_plugin():
            return getattr(self.plugin_data, 'license_url', '') or ''
        else:
            try:
                return self.plugin_data.manifest.license_url if self.plugin_data.manifest else ''
            except (AttributeError, Exception):
                return ''

    def _get_homepage(self):
        """Get homepage URL."""
        if self._is_installable_plugin():
            return getattr(self.plugin_data, 'homepage', '') or ''
        else:
            try:
                return self.plugin_data.manifest._data.get('homepage', '') if self.plugin_data.manifest else ''
            except (AttributeError, Exception):
                return ''

    def _get_path(self):
        """Get plugin path."""
        if self._is_installable_plugin():
            return ''
        else:
            path = getattr(self.plugin_data, 'local_path', '')
            return str(path) if path else ''

    def _get_short_description(self):
        """Get plugin short description."""
        if self._is_installable_plugin():
            if hasattr(self.plugin_data, 'description_i18n'):
                return self.plugin_data.description_i18n()
            return getattr(self.plugin_data, 'description', '') or ''
        else:
            try:
                return self.plugin_data.manifest.description_i18n() if self.plugin_data.manifest else ''
            except (AttributeError, Exception):
                return ''

    def _get_description(self):
        """Get plugin long description."""
        if self._is_installable_plugin():
            # For InstallablePlugin, short and long description are the same
            return self._get_short_description()
        else:
            try:
                if self.plugin_data.manifest:
                    # Try long description first, then fall back to short
                    long_desc = self.plugin_data.manifest.long_description_i18n()
                    if long_desc:
                        return long_desc
                    return self.plugin_data.manifest.description_i18n()
                return ''
            except (AttributeError, Exception):
                return ''
