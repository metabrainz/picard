# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

from __future__ import annotations

from PyQt6 import QtWidgets

from picard.config import get_config
from picard.i18n import gettext as _
from picard.util import get_url


class WelcomePage(QtWidgets.QWizardPage):
    """Welcome page introducing Picard to new users."""

    def __init__(self, parent: QtWidgets.QWizard | None = None):
        super().__init__(parent)
        self.setTitle(_("Welcome to MusicBrainz Picard"))

        layout = QtWidgets.QVBoxLayout(self)

        text = QtWidgets.QLabel(
            _(
                "<p>Picard helps you tag and organize your music collection "
                "using the MusicBrainz database.</p>"
                "<p>This wizard will help you configure a few important settings "
                "before you get started. You can always change these later in "
                "the Options dialog.</p>"
                "<p><a href='{doc_url}'>Read the documentation</a></p>"
            ).format(doc_url=get_url('/getting_started/screen_main.html'))
        )
        text.setWordWrap(True)
        text.setOpenExternalLinks(True)
        layout.addWidget(text)
        layout.addStretch()


class FileOrganizationPage(QtWidgets.QWizardPage):
    """Page for configuring file renaming and moving."""

    def __init__(self, parent: QtWidgets.QWizard | None = None):
        super().__init__(parent)
        self.setTitle(_("File Organization"))
        self.setSubTitle(_("Choose whether Picard should rename and move your files when saving tags."))

        layout = QtWidgets.QVBoxLayout(self)

        self.rename_checkbox = QtWidgets.QCheckBox(_("Rename files based on tags (e.g. \"Artist - Title.mp3\")"))
        layout.addWidget(self.rename_checkbox)

        self.move_checkbox = QtWidgets.QCheckBox(_("Move files to a directory structure based on tags"))
        self.move_checkbox.toggled.connect(self._update_move_to_state)
        layout.addWidget(self.move_checkbox)

        move_to_layout = QtWidgets.QHBoxLayout()
        self.move_to_edit = QtWidgets.QLineEdit()
        self.move_to_edit.setEnabled(False)
        move_to_layout.addWidget(self.move_to_edit)
        self.browse_button = QtWidgets.QToolButton()
        self.browse_button.setText(_("…"))
        self.browse_button.setEnabled(False)
        self.browse_button.clicked.connect(self._browse_directory)
        move_to_layout.addWidget(self.browse_button)
        layout.addLayout(move_to_layout)

        layout.addStretch()

    def initializePage(self) -> None:
        config = get_config()
        self.rename_checkbox.setChecked(config.setting['rename_files'])
        self.move_checkbox.setChecked(config.setting['move_files'])
        self.move_to_edit.setText(config.setting['move_files_to'])

    def _update_move_to_state(self, checked: bool) -> None:
        self.move_to_edit.setEnabled(checked)
        self.browse_button.setEnabled(checked)

    def _browse_directory(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            _("Select destination directory"),
            self.move_to_edit.text(),
        )
        if directory:
            self.move_to_edit.setText(directory)


class CoverArtPage(QtWidgets.QWizardPage):
    """Page for configuring cover art settings."""

    def __init__(self, parent: QtWidgets.QWizard | None = None):
        super().__init__(parent)
        self.setTitle(_("Cover Art"))
        self.setSubTitle(_("Choose how Picard should handle album cover art."))

        layout = QtWidgets.QVBoxLayout(self)

        self.embed_checkbox = QtWidgets.QCheckBox(_("Embed cover art into audio files"))
        layout.addWidget(self.embed_checkbox)

        self.save_to_files_checkbox = QtWidgets.QCheckBox(_("Save cover art as separate image files"))
        layout.addWidget(self.save_to_files_checkbox)

        layout.addStretch()

    def initializePage(self) -> None:
        config = get_config()
        self.embed_checkbox.setChecked(config.setting['save_images_to_tags'])
        self.save_to_files_checkbox.setChecked(config.setting['save_images_to_files'])


class SetupWizard(QtWidgets.QWizard):
    """First-run setup wizard for new Picard users."""

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(_("Picard Setup"))
        self.setWizardStyle(QtWidgets.QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(500, 350)
        self.setOption(QtWidgets.QWizard.WizardOption.NoBackButtonOnStartPage)

        self.welcome_page = WelcomePage(self)
        self.file_org_page = FileOrganizationPage(self)
        self.cover_art_page = CoverArtPage(self)

        self.addPage(self.welcome_page)
        self.addPage(self.file_org_page)
        self.addPage(self.cover_art_page)

    def accept(self) -> None:
        config = get_config()
        config.setting['rename_files'] = self.file_org_page.rename_checkbox.isChecked()
        config.setting['move_files'] = self.file_org_page.move_checkbox.isChecked()
        config.setting['move_files_to'] = self.file_org_page.move_to_edit.text()
        config.setting['save_images_to_tags'] = self.cover_art_page.embed_checkbox.isChecked()
        config.setting['save_images_to_files'] = self.cover_art_page.save_to_files_checkbox.isChecked()
        config.persist['setup_wizard_completed'] = True
        super().accept()

    def reject(self) -> None:
        config = get_config()
        config.persist['setup_wizard_completed'] = True
        super().reject()

    @staticmethod
    def should_show() -> bool:
        config = get_config()
        return not config.persist['setup_wizard_completed']
