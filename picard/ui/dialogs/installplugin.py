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

        # URL input section
        url_group = QtWidgets.QGroupBox(_("Install from URL"))
        url_layout = QtWidgets.QFormLayout(url_group)

        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText(_("https://github.com/user/plugin"))
        url_layout.addRow(_("Git URL:"), self.url_edit)

        self.ref_edit = QtWidgets.QLineEdit()
        self.ref_edit.setPlaceholderText(_("main"))
        url_layout.addRow(_("Ref/Tag:"), self.ref_edit)

        layout.addWidget(url_group)

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

        # Connect URL changes to validation
        self.url_edit.textChanged.connect(self._validate_input)
        self._validate_input()

    def _validate_input(self):
        """Validate input and update UI."""
        url = self.url_edit.text().strip()
        self.install_button.setEnabled(bool(url))

        if url:
            # Check trust level and show warning if needed
            self._check_trust_level(url)

    def _check_trust_level(self, url):
        """Check trust level and show warning if needed."""
        tagger = QtWidgets.QApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            return

        try:
            registry = tagger.pluginmanager3._registry
            trust_level = registry.get_trust_level(url)

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
        except Exception:
            self.warning_label.hide()

    def _install_plugin(self):
        """Install the plugin."""
        url = self.url_edit.text().strip()
        ref = self.ref_edit.text().strip() or None

        if not url:
            return

        # Get plugin manager
        tagger = QtWidgets.QApplication.instance()
        if not hasattr(tagger, "pluginmanager3") or not tagger.pluginmanager3:
            QtWidgets.QMessageBox.critical(self, _("Error"), _("Plugin system not available"))
            return

        # Disable UI during installation
        self.install_button.setEnabled(False)
        self.url_edit.setEnabled(False)
        self.ref_edit.setEnabled(False)
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
        self.url_edit.setEnabled(True)
        self.ref_edit.setEnabled(True)
        self.progress_bar.hide()

        if result.success:
            self.status_label.setText(_("Plugin installed successfully"))
            self.plugin_installed.emit(result.result)
            QtWidgets.QTimer.singleShot(1000, self.accept)  # Close after 1 second
        else:
            self.status_label.setText(_("Installation failed"))
            error_msg = str(result.error) if result.error else _("Unknown error")
            QtWidgets.QMessageBox.critical(self, _("Installation Failed"), error_msg)
