# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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
    QtGui,
    QtWidgets,
)

from picard import tagger_instance
from picard.config import (
    Config,
    get_config,
)
from picard.const.sys import IS_WIN
from picard.i18n import gettext as _
from picard.util import (
    get_url,
    icontheme,
)


class WizardCheckbox(QtWidgets.QWidget):
    def __init__(self, title: str, description: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        style = QtWidgets.QApplication.style()
        assert style

        palette = self.palette()
        highlight_bg = palette.color(QtGui.QPalette.ColorRole.Highlight)
        highlight_text = palette.color(QtGui.QPalette.ColorRole.HighlightedText)

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            WizardCheckbox:hover {{
                background-color: {highlight_bg.name()};
            }}
            * {{
                color: {highlight_text.name()};
            }}
        """)

        layout = QtWidgets.QVBoxLayout(self)

        self._checkbox = QtWidgets.QCheckBox(title)
        font = self._checkbox.font()
        font.setWeight(QtGui.QFont.Weight.Bold)
        self._checkbox.setFont(font)
        layout.addWidget(self._checkbox)

        hint = QtWidgets.QLabel(description)
        label_indent = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_IndicatorWidth) + style.pixelMetric(
            QtWidgets.QStyle.PixelMetric.PM_CheckBoxLabelSpacing
        )
        hint.setIndent(label_indent)
        hint.setWordWrap(True)
        hint.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        layout.addWidget(hint)

    def mousePressEvent(self, event: QtGui.QMouseEvent | None) -> None:
        if event is None:
            return
        self._checkbox.toggle()
        event.accept()

    def set_checked(self, checked: bool) -> None:
        self._checkbox.setChecked(checked)

    def is_checked(self) -> bool:
        return self._checkbox.isChecked()


class SetupWizardPage(QtWidgets.QWizardPage):
    """Base class for setup wizard pages that can save settings."""

    def __init__(self, parent: QtWidgets.QWizard | None = None):
        super().__init__(parent)
        self.setPixmap(
            QtWidgets.QWizard.WizardPixmap.LogoPixmap,
            icontheme.lookup('preferences-desktop').pixmap(32, 32),
        )

    def save_settings(self, config: Config) -> None:
        """Save page settings to config. Override in subclasses."""


class WelcomePage(SetupWizardPage):
    """Welcome page introducing Picard to new users."""

    def __init__(self, parent: QtWidgets.QWizard | None = None):
        super().__init__(parent)
        self.setTitle(_("Welcome to MusicBrainz Picard"))

        layout = QtWidgets.QVBoxLayout(self)

        doc_url = get_url('/getting_started/screen_main.html')
        text = QtWidgets.QLabel(
            _(
                "<p>Picard helps you tag and organize your music collection "
                "using the MusicBrainz database.</p>"
                "<p>This wizard will help you configure a few important settings "
                "before you get started. You can always change these later in "
                "the Options dialog.</p>"
            )
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        link = QtWidgets.QLabel(
            '<a href="{url}">{text}</a>'.format(
                url=doc_url,
                text=_("Read the documentation"),
            )
        )
        link.setToolTip(doc_url)
        link.setOpenExternalLinks(True)
        layout.addWidget(link)
        layout.addStretch()


class FileOrganizationPage(SetupWizardPage):
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
        style = self.style()
        if style:
            self.browse_button.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon))
        self.browse_button.setEnabled(False)
        self.browse_button.clicked.connect(self._browse_directory)
        move_to_layout.addWidget(self.browse_button)
        layout.addLayout(move_to_layout)

        layout.addStretch()
        hint = QtWidgets.QLabel(
            _(
                "You can change these later from the Options menu "
                "or under Options \N{RIGHTWARDS ARROW} Options "
                "\N{RIGHTWARDS ARROW} File Naming."
            )
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

    def initializePage(self) -> None:
        config = get_config()
        self.rename_checkbox.setChecked(config.setting['rename_files'])
        self.move_checkbox.setChecked(config.setting['move_files'])
        self.move_to_edit.setText(config.setting['move_files_to'])

    def save_settings(self, config: Config) -> None:
        config.setting['rename_files'] = self.rename_checkbox.isChecked()
        config.setting['move_files'] = self.move_checkbox.isChecked()
        config.setting['move_files_to'] = self.move_to_edit.text()

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


class CoverArtPage(SetupWizardPage):
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
        hint = QtWidgets.QLabel(
            _("You can change these later under Options \N{RIGHTWARDS ARROW} Options \N{RIGHTWARDS ARROW} Cover Art.")
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

    def initializePage(self) -> None:
        config = get_config()
        self.embed_checkbox.setChecked(config.setting['save_images_to_tags'])
        self.save_to_files_checkbox.setChecked(config.setting['save_images_to_files'])

    def save_settings(self, config: Config) -> None:
        config.setting['save_images_to_tags'] = self.embed_checkbox.isChecked()
        config.setting['save_images_to_files'] = self.save_to_files_checkbox.isChecked()


class UpdatesPage(SetupWizardPage):
    """Page for configuring update settings."""

    def __init__(self, parent: QtWidgets.QWizard | None = None):
        super().__init__(parent)
        self.setTitle(_("Updates"))
        self.setSubTitle(_("Choose how Picard should check for updates."))
        self.setPixmap(
            QtWidgets.QWizard.WizardPixmap.LogoPixmap,
            icontheme.lookup('plugin-update').pixmap(32, 32),
        )

        layout = QtWidgets.QVBoxLayout(self)

        self.update_check_app = WizardCheckbox(
            _("Check for program updates during startup"),
            _("Check for a new program version on the Picard website and show an update dialog if available."),
        )
        layout.addWidget(self.update_check_app)
        if not tagger_instance().autoupdate_enabled:
            self.update_check_app.hide()

        self.update_check_plugins = WizardCheckbox(
            _("Check for plugin updates during startup"),
            _("Check for plugin updates on the Picard website and show a notification in the status bar."),
        )
        layout.addWidget(self.update_check_plugins)

        self.update_check_docs = WizardCheckbox(
            _("Check for documentation updates during startup"),
            _(
                "On startup the available documentation languages will be updated from ReadTheDocs.org. "
                "This allows showing the online documentation in the best available language based on "
                "the currently selected user interface language."
            ),
        )
        layout.addWidget(self.update_check_docs)

        layout.addStretch()
        hint = QtWidgets.QLabel(
            _("You can change these later under Options \N{RIGHTWARDS ARROW} General \N{RIGHTWARDS ARROW} Startup.")
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

    def initializePage(self) -> None:
        config = get_config()
        self.update_check_app.set_checked(config.setting['check_for_updates'])
        self.update_check_plugins.set_checked(config.setting['check_for_plugin_updates'])
        self.update_check_docs.set_checked(config.setting['check_rtd_updates'])

    def save_settings(self, config: Config) -> None:
        config.setting['check_for_updates'] = self.update_check_app.is_checked()
        config.setting['check_for_plugin_updates'] = self.update_check_plugins.is_checked()
        config.setting['check_rtd_updates'] = self.update_check_docs.is_checked()


class SetupWizard(QtWidgets.QWizard):
    """First-run setup wizard for new Picard users."""

    PAGES: list[type[SetupWizardPage]] = [
        WelcomePage,
        FileOrganizationPage,
        CoverArtPage,
        UpdatesPage,
    ]

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(_("Picard Setup"))
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.setMinimumSize(620, 480)
        self.setOption(QtWidgets.QWizard.WizardOption.NoBackButtonOnStartPage)
        if IS_WIN:
            self.setWizardStyle(QtWidgets.QWizard.WizardStyle.ModernStyle)

        self._pages: list[SetupWizardPage] = []
        for page_class in self.PAGES:
            page = page_class(self)
            self._pages.append(page)
            self.addPage(page)

    def accept(self) -> None:
        config = get_config()
        for page in self._pages:
            page.save_settings(config)
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
