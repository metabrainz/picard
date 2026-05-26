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
from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.config import get_config
from picard.i18n import gettext as _

from picard.ui import PicardDialog
from picard.ui.util import font_scaled_size
from picard.ui.widgets.refselector import RefSelectorWidget


class InstallConfirmDialog(PicardDialog):
    """Dialog for confirming plugin installation with trust warnings and ref selection."""

    defaultsize = QtCore.QSize(500, 400)

    def __init__(self, plugin_name, url, parent=None, plugin_uuid=None, current_ref=None):
        super().__init__(parent)
        self.plugin_name = plugin_name
        self.url = url
        self.plugin_uuid = plugin_uuid
        self.current_ref = current_ref
        self.selected_ref = None

        # Cache plugin manager for performance
        self.plugin_manager = self.tagger.get_plugin_manager()

        self.setWindowTitle(_("Confirm Plugin Installation"))
        self.setModal(True)
        self.setMinimumSize(font_scaled_size(self, 60, 20))
        self.setup_ui()
        self.check_trust_and_blacklist()
        self.load_refs()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # General security warning (with "don't show again")
        config = get_config()
        if config.persist['show_plugin_install_warning']:
            warning_content = QtWidgets.QHBoxLayout()

            icon_label = QtWidgets.QLabel()
            icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning)
            icon_label.setPixmap(icon.pixmap(24, 24))
            icon_label.setFixedSize(28, 28)
            icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            warning_content.addWidget(icon_label)

            text_layout = QtWidgets.QVBoxLayout()
            general_warning = QtWidgets.QLabel(
                _("Plugins run with full access to your system. Only install plugins from sources you trust.")
            )
            general_warning.setWordWrap(True)
            font = general_warning.font()
            font.setPointSizeF(font.pointSizeF() * 1.1)
            font.setBold(True)
            general_warning.setFont(font)
            text_layout.addWidget(general_warning)

            self._dont_show_checkbox = QtWidgets.QCheckBox(_("Don't show this warning again"))
            text_layout.addWidget(self._dont_show_checkbox)
            warning_content.addLayout(text_layout)

            layout.addLayout(warning_content)
            layout.addWidget(self._create_separator())
        else:
            self._dont_show_checkbox = None

        # Plugin name and URL
        info_label = QtWidgets.QLabel(_("Install plugin: {name}").format(name=f"<b>{self.plugin_name}</b>"))
        info_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(info_label)

        if self.url.startswith(('http://', 'https://')):
            url_display = f'<a href="{self.url}">{self.url}</a>'
        else:
            url_display = self.url
        url_label = QtWidgets.QLabel(_("Repository: {url}").format(url=url_display))
        url_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse | QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        url_label.setOpenExternalLinks(True)
        url_label.setWordWrap(True)
        layout.addWidget(url_label)

        # Trust/blacklist warning area (shown conditionally)
        self.warning_label = QtWidgets.QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        # Ref selection (optional)
        ref_group = QtWidgets.QGroupBox(_("Git Reference (Optional)"))
        ref_layout = QtWidgets.QVBoxLayout(ref_group)

        # Use the new RefSelectorWidget
        self.ref_selector = RefSelectorWidget(include_default=True)
        ref_layout.addWidget(self.ref_selector)
        layout.addWidget(ref_group)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox()
        self.install_button = QtWidgets.QPushButton(_("Yes, Install!"))
        button_box.addButton(self.install_button, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._confirm_install)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_separator(self):
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        return separator

    def check_trust_and_blacklist(self):
        """Check trust level and blacklist status."""
        try:
            registry = self.plugin_manager._registry

            # Check blacklist first
            is_blacklisted, reason = registry.is_blacklisted(self.url, self.plugin_uuid)
            if is_blacklisted:
                self.warning_label.setText(
                    "<b>" + _("This plugin is blacklisted: {reason}").format(reason=reason) + "</b>"
                )
                self.warning_label.show()
                self.install_button.setEnabled(False)
                return

            # Check trust level
            trust_level = registry.get_trust_level(self.url)
            if trust_level in ("community", "unregistered"):
                if trust_level == "community":
                    warning_text = _(
                        "This is a community plugin. Community plugins are not reviewed by the Picard team."
                    )
                else:  # unregistered
                    warning_text = _(
                        "This plugin is not in the official registry. "
                        "Installing unregistered plugins may pose security risks."
                    )
                self.warning_label.setText("<b>" + warning_text + "</b>")
                self.warning_label.show()
        except Exception:
            pass

    def load_refs(self):
        """Load available refs from repository."""
        try:
            refs = self.plugin_manager.fetch_all_git_refs(self.url)
            if refs:
                self.ref_selector.load_refs(refs, current_ref=self.current_ref, plugin_manager=self.plugin_manager)

                # Get default ref info from manager
                if self.plugin_uuid:
                    default_ref, description = self.plugin_manager.get_default_ref_info(self.plugin_uuid)
                    if default_ref:
                        self.ref_selector.set_default_ref_info(default_ref, _(description))
        except Exception:
            # If we can't fetch refs, user can still use default or custom input
            pass

    def _confirm_install(self):
        """Handle install button click."""
        if self._dont_show_checkbox and self._dont_show_checkbox.isChecked():
            config = get_config()
            config.persist['show_plugin_install_warning'] = False
        self.selected_ref = self.ref_selector.get_selected_ref()
        self.accept()
