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


class InstallConfirmDialog(QtWidgets.QDialog):
    """Dialog for confirming plugin installation with trust warnings and ref selection."""

    def __init__(self, plugin_name, url, parent=None):
        super().__init__(parent)
        self.plugin_name = plugin_name
        self.url = url
        self.selected_ref = None
        self.setWindowTitle(_("Confirm Plugin Installation"))
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        self.check_trust_and_blacklist()
        self.load_refs()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Plugin name and URL
        info_label = QtWidgets.QLabel(_("Install plugin: {}").format(self.plugin_name))
        info_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(info_label)

        url_label = QtWidgets.QLabel(_("Repository: {}").format(self.url))
        url_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        url_label.setWordWrap(True)
        layout.addWidget(url_label)

        # Warning area
        self.warning_label = QtWidgets.QLabel()
        self.warning_label.setStyleSheet("color: orange; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        # Ref selection (optional)
        ref_group = QtWidgets.QGroupBox(_("Git Reference (Optional)"))
        ref_layout = QtWidgets.QVBoxLayout(ref_group)

        # Tab widget for ref selection
        self.ref_tab_widget = QtWidgets.QTabWidget()

        # Default tab
        default_widget = QtWidgets.QWidget()
        default_layout = QtWidgets.QVBoxLayout(default_widget)
        default_layout.addWidget(QtWidgets.QLabel(_("Use default branch/tag")))
        self.ref_tab_widget.addTab(default_widget, _("Default"))

        # Tags tab
        tags_widget = QtWidgets.QWidget()
        tags_layout = QtWidgets.QVBoxLayout(tags_widget)
        self.tags_list = QtWidgets.QListWidget()
        tags_layout.addWidget(self.tags_list)
        self.ref_tab_widget.addTab(tags_widget, _("Tags"))

        # Branches tab
        branches_widget = QtWidgets.QWidget()
        branches_layout = QtWidgets.QVBoxLayout(branches_widget)
        self.branches_list = QtWidgets.QListWidget()
        branches_layout.addWidget(self.branches_list)
        self.ref_tab_widget.addTab(branches_widget, _("Branches"))

        # Custom tab
        custom_widget = QtWidgets.QWidget()
        custom_layout = QtWidgets.QVBoxLayout(custom_widget)
        custom_label = QtWidgets.QLabel(_("Enter tag, branch, or commit ID:"))
        custom_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        custom_layout.addWidget(custom_label)
        self.custom_edit = QtWidgets.QLineEdit()
        custom_layout.addWidget(self.custom_edit)
        self.ref_tab_widget.addTab(custom_widget, _("Custom"))

        ref_layout.addWidget(self.ref_tab_widget)
        layout.addWidget(ref_group)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.install_button = QtWidgets.QPushButton(_("Install"))
        self.install_button.clicked.connect(self._confirm_install)
        self.install_button.setDefault(True)
        button_layout.addWidget(self.install_button)

        cancel_button = QtWidgets.QPushButton(_("Cancel"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def check_trust_and_blacklist(self):
        """Check trust level and blacklist status."""
        tagger = QtCore.QCoreApplication.instance()
        try:
            registry = tagger.pluginmanager3._registry

            # Check blacklist first
            is_blacklisted, reason = registry.is_blacklisted(self.url)
            if is_blacklisted:
                self.warning_label.setText(_("ERROR: This plugin is blacklisted: {}").format(reason))
                self.warning_label.setStyleSheet("color: red; font-weight: bold;")
                self.warning_label.show()
                self.install_button.setEnabled(False)
                return

            # Check trust level
            trust_level = registry.get_trust_level(self.url)
            if trust_level in ("community", "unregistered"):
                if trust_level == "community":
                    warning_text = _(
                        "Warning: This is a community plugin. "
                        "Community plugins are not reviewed by the Picard team. "
                        "Only install plugins from sources you trust."
                    )
                else:  # unregistered
                    warning_text = _(
                        "Warning: This plugin is not in the official registry. "
                        "Installing unregistered plugins may pose security risks. "
                        "Only install plugins from sources you trust."
                    )
                self.warning_label.setText(warning_text)
                self.warning_label.show()
        except Exception:
            pass

    def load_refs(self):
        """Load available refs from repository."""
        try:
            tagger = QtCore.QCoreApplication.instance()
            refs = tagger.pluginmanager3.fetch_all_git_refs(self.url)
            if refs:
                # Populate tags
                for ref in refs.get('tags', []):
                    self.tags_list.addItem(ref['name'])

                # Populate branches
                for ref in refs.get('branches', []):
                    self.branches_list.addItem(ref['name'])
        except Exception:
            # If we can't fetch refs, user can still use default or custom input
            pass

    def _confirm_install(self):
        """Handle install button click."""
        current_tab = self.ref_tab_widget.currentIndex()

        if current_tab == 0:  # Default
            self.selected_ref = None
        elif current_tab == 1:  # Tags
            current_item = self.tags_list.currentItem()
            if current_item:
                self.selected_ref = current_item.text()
        elif current_tab == 2:  # Branches
            current_item = self.branches_list.currentItem()
            if current_item:
                self.selected_ref = current_item.text()
        else:  # Custom
            self.selected_ref = self.custom_edit.text().strip() or None

        self.accept()
